"""Caracterização do lifecycle de Evidence entre projetos."""

import unittest

from controllers.evidence_controller import EvidenceController, EvidenceEditorMode
from models import EvidenceDraft
from services import EvidenceServiceError
from tests.test_evidence_controller import ServiceDouble, WorkspaceDouble, evidence


class LifecycleWorkspace(WorkspaceDouble):
    def __init__(self):
        super().__init__()
        self.clear_count = 0

    def clear(self):
        super().clear()
        self.clear_count += 1

    def on_project_closed(self):
        self.clear()


class EvidenceLifecycleCharacterizationTests(unittest.TestCase):
    def controller(self, decisions=()):
        workspace = LifecycleWorkspace()
        decisions = list(decisions)
        prompts = []

        def confirm():
            prompts.append("unsaved")
            return decisions.pop(0)

        controller = EvidenceController(
            workspace, confirm_unsaved=confirm
        )
        return controller, workspace, prompts

    def test_open_and_switch_project_without_dirty_replaces_all_state(self):
        old, new = evidence("Antiga"), evidence("Nova")
        controller, workspace, prompts = self.controller()
        old_service, new_service = ServiceDouble((old,)), ServiceDouble((new,))

        controller.set_service(old_service)
        controller.select(old.id)
        controller.set_service(new_service)

        self.assertEqual(prompts, [])
        self.assertIs(controller.service, new_service)
        self.assertEqual(tuple(item.id for item in workspace.items), (new.id,))
        self.assertIsNone(workspace.selected)
        self.assertEqual(controller.mode, EvidenceEditorMode.EMPTY)
        self.assertEqual(controller.current_draft, EvidenceDraft.empty())

    def test_switch_project_dirty_save_discard_or_cancel(self):
        old, new = evidence("Antiga"), evidence("Nova")
        for decision in ("save", "discard", "cancel"):
            with self.subTest(decision=decision):
                controller, workspace, prompts = self.controller((decision,))
                old_service = ServiceDouble((old,))
                new_service = ServiceDouble((new,))
                controller.set_service(old_service)
                controller.select(old.id)
                controller.update_draft(
                    EvidenceDraft.from_evidence(old).__class__(
                        evidence_id=old.id,
                        document_identity=old.document_identity,
                        page_number=old.page_number,
                        title="Alterada",
                    )
                )

                # ProjectController chama can_leave antes de trocar o service.
                accepted = controller.can_leave()
                if accepted:
                    controller.set_service(new_service)

                self.assertEqual(prompts, ["unsaved"])
                self.assertEqual(accepted, decision != "cancel")
                if decision == "save":
                    self.assertEqual(old_service.calls.count("update"), 1)
                if accepted:
                    self.assertIs(controller.service, new_service)
                    self.assertEqual(
                        tuple(item.id for item in workspace.items), (new.id,)
                    )
                    self.assertEqual(controller.mode, EvidenceEditorMode.EMPTY)
                else:
                    self.assertIs(controller.service, old_service)
                    self.assertEqual(workspace.selected, old.id)

    def test_close_project_clears_once_without_additional_ui_hook(self):
        item = evidence()
        controller, workspace, prompts = self.controller()
        controller.set_service(ServiceDouble((item,)))
        before = workspace.clear_count

        self.assertTrue(controller.can_leave())
        controller.set_service(None)

        self.assertEqual(prompts, [])
        self.assertEqual(workspace.clear_count, before + 1)
        self.assertIsNone(controller.service)
        self.assertEqual(workspace.items, ())
        self.assertEqual(controller.mode, EvidenceEditorMode.EMPTY)
        self.assertEqual(controller.current_draft, EvidenceDraft.empty())
        self.assertEqual(controller.baseline_draft, EvidenceDraft.empty())

    def test_repeated_set_service_none_is_observably_idempotent(self):
        controller, workspace, _ = self.controller()
        controller.set_service(ServiceDouble())
        controller.set_service(None)
        after_first = workspace.clear_count

        controller.set_service(None)

        self.assertEqual(workspace.clear_count, after_first)

    def test_set_service_none_clears_state_created_without_service(self):
        controller, workspace, _ = self.controller()
        controller.start_create()
        controller.update_draft(EvidenceDraft(title="Rascunho"))
        before = workspace.clear_count

        controller.set_service(None)

        self.assertEqual(workspace.clear_count, before + 1)
        self.assertEqual(controller.mode, EvidenceEditorMode.EMPTY)
        self.assertEqual(controller.current_draft, EvidenceDraft.empty())

    def test_clear_preserves_service_without_listing_and_clears_once(self):
        item = evidence()
        controller, workspace, _ = self.controller()
        service = ServiceDouble((item,))
        controller.set_service(service)
        calls_before = tuple(service.calls)
        clears_before = workspace.clear_count

        controller.clear()

        self.assertIs(controller.service, service)
        self.assertEqual(tuple(service.calls), calls_before)
        self.assertEqual(workspace.clear_count, clears_before + 1)
        self.assertEqual(controller.mode, EvidenceEditorMode.EMPTY)

    def test_service_activation_lists_once(self):
        controller, _, _ = self.controller()
        service = ServiceDouble((evidence(),))

        controller.set_service(service)

        self.assertEqual(service.calls.count("list_all"), 1)

    def test_same_id_in_new_project_does_not_preserve_selection_or_draft(self):
        shared_id = evidence().id
        old = evidence("Antiga", evidence_id=shared_id)
        new = evidence("Nova", evidence_id=shared_id)
        controller, workspace, _ = self.controller()
        controller.set_service(ServiceDouble((old,)))
        controller.select(shared_id)

        controller.set_service(ServiceDouble((new,)))

        self.assertIsNone(workspace.selected)
        self.assertEqual(controller.current_draft, EvidenceDraft.empty())
        self.assertEqual(tuple(item.title for item in workspace.items), ("Nova",))

    def test_only_new_project_source_statuses_are_recalculated(self):
        old, new = evidence("Antiga"), evidence("Nova")

        class CountingService(ServiceDouble):
            def __init__(self, items):
                super().__init__(items)
                self.status_calls = []

            def is_source_available(self, item):
                self.status_calls.append(item.id)
                return super().is_source_available(item)

        old_service = CountingService((old,))
        new_service = CountingService((new,))
        controller, _, _ = self.controller()
        controller.set_service(old_service)
        old_count = len(old_service.status_calls)

        controller.set_service(new_service)

        self.assertEqual(len(old_service.status_calls), old_count)
        self.assertEqual(new_service.status_calls, [new.id])

    def test_new_project_list_failure_leaves_new_service_and_empty_state(self):
        old = evidence("Antiga")

        class FailingListService(ServiceDouble):
            def list_all(self):
                raise EvidenceServiceError("falha")

        controller, workspace, _ = self.controller()
        controller.set_service(ServiceDouble((old,)))
        controller.select(old.id)
        failing = FailingListService()

        controller.set_service(failing)

        self.assertIs(controller.service, failing)
        self.assertEqual(workspace.items, ())
        self.assertIsNone(workspace.selected)
        self.assertEqual(controller.mode, EvidenceEditorMode.EMPTY)

    def test_failed_save_guard_prevents_service_switch(self):
        old, new = evidence("Antiga"), evidence("Nova")

        class FailingSaveService(ServiceDouble):
            def update(self, request):
                raise EvidenceServiceError("falha")

        controller, workspace, prompts = self.controller(("save",))
        old_service = FailingSaveService((old,))
        controller.set_service(old_service)
        controller.select(old.id)
        controller.update_draft(
            EvidenceDraft.from_evidence(old).__class__(
                evidence_id=old.id,
                document_identity=old.document_identity,
                title="Alterada",
            )
        )

        accepted = controller.can_leave()
        if accepted:
            controller.set_service(ServiceDouble((new,)))

        self.assertFalse(accepted)
        self.assertEqual(prompts, ["unsaved"])
        self.assertIs(controller.service, old_service)
        self.assertEqual(workspace.selected, old.id)

    def test_discard_guard_switches_with_one_final_clear_and_one_prompt(self):
        old, new = evidence("Antiga"), evidence("Nova")
        controller, workspace, prompts = self.controller(("discard",))
        controller.set_service(ServiceDouble((old,)))
        controller.select(old.id)
        controller.update_draft(
            EvidenceDraft(
                evidence_id=old.id,
                document_identity=old.document_identity,
                title="Alterada",
            )
        )
        before = workspace.clear_count

        self.assertTrue(controller.can_leave())
        controller.set_service(ServiceDouble((new,)))

        self.assertEqual(prompts, ["unsaved"])
        self.assertEqual(workspace.clear_count, before + 1)

    def test_close_project_dirty_cancel_preserves_old_project_state(self):
        item = evidence()
        controller, workspace, prompts = self.controller(("cancel",))
        service = ServiceDouble((item,))
        controller.set_service(service)
        controller.select(item.id)
        controller.update_draft(
            EvidenceDraft(
                evidence_id=item.id,
                document_identity=item.document_identity,
                title="Alterada",
            )
        )

        self.assertFalse(controller.can_leave())

        self.assertEqual(prompts, ["unsaved"])
        self.assertIs(controller.service, service)
        self.assertEqual(workspace.selected, item.id)
        self.assertTrue(controller.dirty)


if __name__ == "__main__":
    unittest.main()
