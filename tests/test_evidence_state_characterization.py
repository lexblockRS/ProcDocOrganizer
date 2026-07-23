"""Caracterização observável da máquina de apresentação de Evidence."""

from dataclasses import replace
import unittest

from contracts import DocumentNavigationRequest
from controllers.evidence_controller import EvidenceController, EvidenceEditorMode
from models import EvidenceDraft, EvidenceSourceCandidate
from services import EvidenceServiceError, EvidenceSourceStatus
from tests.test_evidence_controller import (
    SHA_A,
    SHA_B,
    ServiceDouble,
    WorkspaceDouble,
    evidence,
)


class RecordingWorkspace(WorkspaceDouble):
    def __init__(self):
        super().__init__()
        self.calls = []
        self.clears = 0
        self.focus_count = 0

    def set_evidences(self, items, statuses=None):
        super().set_evidences(items, statuses)
        self.calls.append(("set_evidences", tuple(item.id for item in items)))

    def set_draft(self, draft, creating=False, source_locked=False):
        super().set_draft(draft, creating, source_locked)
        self.calls.append(("set_draft", draft.evidence_id, creating, source_locked))

    def set_source_status(self, status):
        super().set_source_status(status)
        self.calls.append(("set_source_status", status))

    def select_evidence(self, evidence_id):
        super().select_evidence(evidence_id)
        self.calls.append(("select_evidence", evidence_id))

    def set_editor_state(self, mode, dirty, valid, **projection):
        super().set_editor_state(mode, dirty, valid, **projection)
        self.calls.append(("set_editor_state", mode, dirty, valid, projection))

    def _apply_editor_projection(self, mode, dirty, valid, **projection):
        super()._apply_editor_projection(mode, dirty, valid, **projection)

    def show_message(self, message):
        super().show_message(message)
        self.calls.append(("show_message", message))

    def focus_title(self):
        super().focus_title()
        self.focus_count += 1
        self.calls.append(("focus_title",))

    def clear(self):
        super().clear()
        self.clears += 1
        self.calls.append(("clear",))


class FailingService(ServiceDouble):
    def __init__(self, operation, items=()):
        super().__init__(items)
        self.operation = operation

    def _fail(self, operation):
        if self.operation == operation:
            raise EvidenceServiceError(f"falha em {operation}")

    def list_all(self):
        self._fail("list_all")
        return super().list_all()

    def is_source_available(self, item):
        self._fail("source_status")
        return super().is_source_available(item)

    def is_document_available(self, identity):
        self._fail("availability")
        return super().is_document_available(identity)

    def create(self, request):
        self._fail("create")
        return super().create(request)

    def update(self, request):
        self._fail("update")
        return super().update(request)

    def delete(self, evidence_id):
        self._fail("delete")
        return super().delete(evidence_id)


def make_controller(
    items=(), *, decisions=(), service=None, delete=True, duplicates=True,
    navigation=None,
):
    workspace = RecordingWorkspace()
    service = service or ServiceDouble(items)
    decisions = list(decisions)
    notifications = []
    confirmations = []

    def confirm_unsaved():
        confirmations.append("unsaved")
        return decisions.pop(0) if decisions else "cancel"

    controller = EvidenceController(
        workspace,
        service,
        confirm_unsaved=confirm_unsaved,
        confirm_delete=lambda item: confirmations.append(("delete", item.id))
        or delete,
        confirm_duplicates=lambda found: confirmations.append(
            ("duplicates", len(found))
        ) or duplicates,
        notify=lambda kind, message: notifications.append((kind, message)),
        document_navigation_requested=navigation,
    )
    return controller, workspace, service, notifications, confirmations


class EvidenceStateCharacterizationTests(unittest.TestCase):
    def test_initial_state_without_service_and_service_absence_commands(self):
        workspace = RecordingWorkspace()
        controller = EvidenceController(workspace)
        initial_clears = workspace.clears

        self.assertEqual(controller.mode, EvidenceEditorMode.EMPTY)
        self.assertFalse(controller.dirty)
        self.assertFalse(controller.load())
        self.assertTrue(controller.start_create())
        controller.update_draft(EvidenceDraft(title="incompleto"))
        self.assertFalse(controller.save())
        self.assertFalse(controller.start_create_from_source(
            EvidenceSourceCandidate(SHA_A, 1)
        ))
        self.assertEqual(workspace.clears, initial_clears + 1)
        # O delete sem seleção é um no-op mesmo sem service.
        controller.selected_evidence = None
        self.assertFalse(controller.delete())

    def test_delete_with_selection_and_missing_service_propagates_attribute_error(self):
        item = evidence()
        workspace = RecordingWorkspace()
        controller = EvidenceController(
            workspace, confirm_delete=lambda _item: True
        )
        controller.selected_evidence = item

        with self.assertRaises(AttributeError):
            controller.delete()

    def test_set_service_loads_and_set_none_clears_observable_state(self):
        item = evidence()
        workspace = RecordingWorkspace()
        controller = EvidenceController(workspace)
        service = ServiceDouble((item,))

        controller.set_service(service)
        self.assertEqual(tuple(x.id for x in workspace.items), (item.id,))
        self.assertIn("list_all", service.calls)
        controller.select(item.id)

        controller.set_service(None)
        self.assertIsNone(controller.service)
        self.assertEqual(workspace.items, ())
        self.assertIsNone(workspace.selected)
        self.assertEqual(controller.mode, EvidenceEditorMode.EMPTY)
        self.assertEqual(controller.current_draft, EvidenceDraft.empty())
        self.assertFalse(workspace.source_locked)

    def test_load_preserves_or_clears_selection_by_identity(self):
        first, second = evidence("A"), evidence("B")
        controller, workspace, service, _, _ = make_controller((first, second))
        controller.load()
        controller.select(first.id)

        self.assertTrue(controller.load())
        self.assertEqual(workspace.selected, first.id)
        self.assertEqual(workspace.draft.title, "A")

        service.items = [second]
        self.assertTrue(controller.load())
        self.assertIsNone(workspace.selected)
        self.assertEqual(controller.mode, EvidenceEditorMode.EMPTY)
        self.assertEqual(workspace.draft, EvidenceDraft.empty())

    def test_select_same_item_is_observable_no_op(self):
        item = evidence()
        controller, workspace, _, _, _ = make_controller((item,))
        controller.load()
        controller.select(item.id)
        before = list(workspace.calls)

        self.assertTrue(controller.select(item.id))
        self.assertEqual(workspace.calls, before)

    def test_dirty_select_save_discard_and_cancel_complete_transitions(self):
        first, second = evidence("A"), evidence("B")
        for decision in ("save", "discard", "cancel"):
            with self.subTest(decision=decision):
                controller, workspace, service, _, confirmations = make_controller(
                    (first, second), decisions=(decision,)
                )
                controller.load()
                controller.select(first.id)
                controller.update_draft(
                    replace(controller.current_draft, title="Alterada")
                )

                accepted = controller.select(second.id)

                self.assertEqual(confirmations, ["unsaved"])
                self.assertEqual(accepted, decision != "cancel")
                self.assertEqual(
                    workspace.selected,
                    first.id if decision == "cancel" else second.id,
                )
                self.assertEqual(
                    service.calls.count("update"), 1 if decision == "save" else 0
                )
                if accepted:
                    self.assertEqual(controller.mode, EvidenceEditorMode.VIEWING)
                    self.assertFalse(controller.dirty)

    def test_dirty_load_discard_is_completed_by_reload_and_reselection(self):
        item = evidence()
        controller, workspace, _, _, confirmations = make_controller(
            (item,), decisions=("discard",)
        )
        controller.load()
        controller.select(item.id)
        controller.update_draft(replace(controller.current_draft, title="Alterada"))

        self.assertTrue(controller.load())

        self.assertEqual(confirmations, ["unsaved"])
        self.assertEqual(workspace.selected, item.id)
        self.assertEqual(workspace.draft.title, item.title)
        self.assertFalse(controller.dirty)
        self.assertEqual(controller.mode, EvidenceEditorMode.VIEWING)

    def test_can_leave_discard_restores_controller_and_workspace_render(self):
        item = evidence()
        controller, workspace, _, _, _ = make_controller(
            (item,), decisions=("discard",)
        )
        controller.load()
        controller.select(item.id)
        changed = replace(controller.current_draft, title="Alterada")
        controller.update_draft(changed)
        workspace.calls.clear()

        self.assertTrue(controller.can_leave())

        self.assertEqual(controller.current_draft, controller.baseline_draft)
        self.assertEqual(workspace.draft, controller.baseline_draft)
        renders = [
            call for call in workspace.calls
            if call[0] == "set_editor_state"
        ]
        self.assertEqual(len(renders), 1)
        self.assertEqual(renders[0][4]["draft"], controller.baseline_draft)
        self.assertEqual(controller.mode, EvidenceEditorMode.VIEWING)

    def test_create_and_update_save_reload_selection_and_baseline(self):
        controller, workspace, service, notifications, _ = make_controller()
        controller.start_create()
        controller.update_draft(
            EvidenceDraft(document_identity=SHA_A, title="Nova")
        )
        self.assertTrue(controller.save())
        created = controller.selected_evidence

        self.assertEqual(service.calls.count("create"), 1)
        self.assertEqual(workspace.selected, created.id)
        self.assertEqual(controller.current_draft, controller.baseline_draft)
        self.assertFalse(controller.dirty)
        self.assertEqual(controller.mode, EvidenceEditorMode.VIEWING)

        controller.update_draft(replace(controller.current_draft, title="Editada"))
        self.assertTrue(controller.save())
        self.assertEqual(service.calls.count("update"), 1)
        self.assertEqual(workspace.selected, created.id)
        self.assertEqual(controller.current_draft, controller.baseline_draft)
        self.assertEqual(notifications[-1][0], "success")

    def test_delete_performs_one_empty_visual_reset(self):
        item = evidence()
        controller, workspace, service, _, confirmations = make_controller((item,))
        controller.load()
        controller.select(item.id)
        workspace.calls.clear()

        self.assertTrue(controller.delete())

        empty_renders = [
            call for call in workspace.calls
            if call[0] == "set_editor_state"
            and call[1] == EvidenceEditorMode.EMPTY
        ]
        self.assertEqual(len(empty_renders), 1)
        self.assertEqual(service.calls.count("delete"), 1)
        self.assertEqual(confirmations, [("delete", item.id)])
        self.assertEqual(controller.mode, EvidenceEditorMode.EMPTY)

    def test_each_reload_lists_once_and_calculates_each_status_once(self):
        first, second = evidence("A"), evidence("B")

        class CountingService(ServiceDouble):
            def __init__(self, items):
                super().__init__(items)
                self.status_calls = []

            def is_source_available(self, item):
                self.status_calls.append(item.id)
                return super().is_source_available(item)

        service = CountingService((first, second))
        controller, _, _, _, _ = make_controller(service=service)

        self.assertTrue(controller.load())

        self.assertEqual(service.calls.count("list_all"), 1)
        self.assertCountEqual(service.status_calls, (first.id, second.id))
        self.assertEqual(len(service.status_calls), 2)

    def test_cancel_creation_and_editing_each_render_one_transition(self):
        item = evidence()
        controller, workspace, _, _, _ = make_controller((item,))
        controller.load()

        controller.start_create()
        workspace.calls.clear()
        controller.cancel()
        self.assertEqual(
            len([
                call for call in workspace.calls
                if call[0] == "set_editor_state"
            ]),
            1,
        )

        controller.select(item.id)
        controller.update_draft(
            replace(controller.current_draft, title="Alterada")
        )
        workspace.calls.clear()
        controller.cancel()
        self.assertEqual(
            len([
                call for call in workspace.calls
                if call[0] == "set_editor_state"
            ]),
            1,
        )
        self.assertEqual(workspace.selected, item.id)
        self.assertEqual(workspace.draft, controller.baseline_draft)

    def test_source_candidate_locks_source_and_manual_create_does_not(self):
        controller, workspace, _, _, _ = make_controller()
        controller.start_create()
        self.assertFalse(workspace.source_locked)
        self.assertEqual(workspace.source_status, None)

        controller.start_create_from_source(
            EvidenceSourceCandidate(
                SHA_A, 4, "Trecho", suggested_title="Documento"
            )
        )
        self.assertTrue(workspace.source_locked)
        self.assertEqual(workspace.source_status, EvidenceSourceStatus.AVAILABLE)
        self.assertEqual(workspace.focus_count, 2)

    def test_controller_projects_source_lock_explicitly_after_transitions(self):
        item = evidence()
        controller, workspace, _, _, _ = make_controller((item,))
        controller.load()

        controller.start_create()
        self.assertFalse(workspace.projection["source_locked"])
        self.assertTrue(workspace.projection["identity_editable"])

        controller.start_create_from_source(
            EvidenceSourceCandidate(SHA_A, 4, "Trecho")
        )
        self.assertTrue(workspace.projection["source_locked"])
        self.assertFalse(workspace.projection["identity_editable"])

        controller.cancel()
        self.assertFalse(workspace.projection["source_locked"])
        controller.select(item.id)
        self.assertTrue(workspace.projection["source_locked"])
        controller.update_draft(
            replace(controller.current_draft, title="Editada")
        )
        self.assertTrue(workspace.projection["source_locked"])
        controller.cancel()
        self.assertTrue(workspace.projection["source_locked"])
        controller.clear()
        self.assertFalse(workspace.source_locked)

    def test_controller_applies_each_visual_state_without_partial_calls(self):
        controller, workspace, _, _, _ = make_controller()
        workspace.calls.clear()

        controller.start_create_from_source(
            EvidenceSourceCandidate(SHA_A, 4, "Trecho")
        )

        self.assertEqual(
            len([
                call for call in workspace.calls
                if call[0] == "set_editor_state"
            ]),
            1,
        )
        self.assertFalse(any(
            call[0] in ("set_draft", "set_source_status")
            for call in workspace.calls
        ))

    def test_service_failures_preserve_or_report_current_state(self):
        for operation in ("list_all", "availability", "create", "update", "delete"):
            with self.subTest(operation=operation):
                item = evidence()
                service = FailingService(operation, (item,))
                controller, workspace, _, messages, _ = make_controller(
                    (item,), service=service
                )
                if operation == "list_all":
                    self.assertFalse(controller.load())
                elif operation == "availability":
                    self.assertFalse(controller.start_create_from_source(
                        EvidenceSourceCandidate(SHA_A, 1)
                    ))
                elif operation == "create":
                    controller.start_create()
                    controller.update_draft(
                        EvidenceDraft(document_identity=SHA_A, title="Nova")
                    )
                    self.assertFalse(controller.save())
                    self.assertTrue(controller.dirty)
                else:
                    controller.load()
                    controller.select(item.id)
                    if operation == "update":
                        controller.update_draft(
                            replace(controller.current_draft, title="Editada")
                        )
                        self.assertFalse(controller.save())
                        self.assertEqual(workspace.selected, item.id)
                    else:
                        self.assertFalse(controller.delete())
                        self.assertEqual(workspace.selected, item.id)
                self.assertEqual(
                    messages[-1],
                    ("error", "Não foi possível concluir a operação."),
                )

    def test_source_status_failure_is_rendered_as_unavailable(self):
        item = evidence()
        service = FailingService("source_status", (item,))
        controller, workspace, _, _, _ = make_controller(service=service)

        self.assertTrue(controller.load())
        self.assertEqual(
            workspace.statuses[item.id], EvidenceSourceStatus.UNAVAILABLE
        )

    def test_navigation_contract_guards_returns_and_callback_exception(self):
        item = evidence()
        received = []
        controller, _, _, _, _ = make_controller(
            (item,), navigation=lambda request: received.append(request) or True
        )
        self.assertFalse(controller.request_document_navigation())
        controller.load()
        controller.select(item.id)
        self.assertTrue(controller.request_document_navigation())
        self.assertEqual(
            received,
            [DocumentNavigationRequest(item.document_identity, item.page_number)],
        )

        controller.set_document_navigation_requested(None)
        self.assertFalse(controller.request_document_navigation())
        controller.set_document_navigation_requested(lambda _request: False)
        self.assertFalse(controller.request_document_navigation())
        controller.set_document_navigation_requested(
            lambda _request: (_ for _ in ()).throw(ValueError("recusada"))
        )
        self.assertFalse(controller.request_document_navigation())
        controller.set_document_navigation_requested(
            lambda _request: (_ for _ in ()).throw(RuntimeError("inesperada"))
        )
        with self.assertRaises(RuntimeError):
            controller.request_document_navigation()

    def test_confirmation_callback_exceptions_currently_propagate_once(self):
        item = evidence()

        controller, _, _, _, _ = make_controller((item,))
        controller.load()
        controller.select(item.id)
        controller.confirm_delete = lambda _item: (_ for _ in ()).throw(
            RuntimeError("confirmação")
        )
        with self.assertRaises(RuntimeError):
            controller.delete()

        controller, _, service, _, _ = make_controller()
        service.duplicates = (item,)
        controller.start_create()
        controller.update_draft(
            EvidenceDraft(document_identity=SHA_A, title="Nova")
        )
        controller.confirm_duplicates = lambda _items: (
            _ for _ in ()
        ).throw(RuntimeError("confirmação"))
        with self.assertRaises(RuntimeError):
            controller.save()
        self.assertEqual(service.calls.count("create"), 0)

        controller, _, _, _, _ = make_controller()
        controller.start_create()
        controller.update_draft(EvidenceDraft(title="alterada"))
        controller.confirm_unsaved = lambda: (_ for _ in ()).throw(
            RuntimeError("confirmação")
        )
        with self.assertRaises(RuntimeError):
            controller.can_leave()


if __name__ == "__main__":
    unittest.main()
