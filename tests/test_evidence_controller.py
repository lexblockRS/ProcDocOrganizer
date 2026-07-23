from dataclasses import replace
import unittest
from uuid import uuid4

from controllers.evidence_controller import EvidenceController, EvidenceEditorMode
from models import Evidence, EvidenceDraft
from services import EvidenceSourceStatus, EvidenceValidationError


SHA_A = "a" * 64
SHA_B = "b" * 64


def evidence(title="Portaria", sha=SHA_A, evidence_id=None, notes=None):
    return Evidence.create(
        sha, title, page_number=2, user_notes=notes,
        evidence_id=evidence_id or str(uuid4()),
        timestamp="2026-01-01T10:00:00",
    )


class SignalDouble:
    def __init__(self):
        self.callbacks = []

    def connect(self, callback):
        self.callbacks.append(callback)

    def emit(self, *args):
        for callback in self.callbacks:
            callback(*args)


class WorkspaceDouble:
    def __init__(self):
        for name in (
            "new_requested", "save_requested", "cancel_requested",
            "delete_requested", "refresh_requested", "evidence_selected",
            "draft_changed",
        ):
            setattr(self, name, SignalDouble())
        self.items = ()
        self.statuses = {}
        self.selected = None
        self.draft = EvidenceDraft.empty()
        self.state = None
        self.message = ""

    def set_evidences(self, items, statuses=None):
        self.items = tuple(items)
        self.statuses = dict(statuses or {})

    def set_draft(self, draft, creating=False, source_locked=False):
        self.draft = draft
        self.creating = creating
        self.source_locked = source_locked

    def set_source_status(self, status):
        self.source_status = status

    def select_evidence(self, evidence_id):
        self.selected = evidence_id

    def set_editor_state(self, mode, dirty, valid, **projection):
        self.state = (mode, dirty, valid)
        if "draft" in projection:
            self.draft = projection["draft"]
        if "source_status" in projection:
            self.source_status = projection["source_status"]
        if "source_locked" in projection:
            self.source_locked = projection["source_locked"]
        self.projection = projection

    def _apply_editor_projection(self, mode, dirty, valid, **projection):
        self.set_editor_state(mode, dirty, valid, **projection)

    def show_message(self, message):
        self.message = message

    def focus_title(self):
        self.focused = True

    def clear(self):
        self.items = ()
        self.selected = None


class ServiceDouble:
    def __init__(self, items=()):
        self.items = list(items)
        self.available = {item.id: True for item in items}
        self.duplicates = ()
        self.calls = []

    def list_all(self):
        self.calls.append("list_all")
        return tuple(self.items)

    def is_source_available(self, item):
        return self.available.get(item.id, False)

    def is_document_available(self, sha):
        self.calls.append("source_available")
        return sha == SHA_A

    def find_potential_duplicates(self, sha, page, title):
        self.calls.append("duplicates")
        return self.duplicates

    def create(self, request):
        self.calls.append("create")
        item = Evidence.create(
            request.document_sha256, request.title,
            page_number=request.page_number, source_snippet=request.source_snippet,
            user_notes=request.user_notes, category=request.category,
            start_date=request.start_date, end_date=request.end_date,
            timestamp="2026-01-01T10:00:00",
        )
        self.items.append(item)
        self.available[item.id] = True
        return item

    def update(self, request):
        self.calls.append("update")
        current = next(item for item in self.items if item.id == request.evidence_id)
        updated = Evidence(
            id=current.id, created_at=current.created_at,
            updated_at="2026-01-02T10:00:00",
            document_sha256=request.document_sha256,
            page_number=request.page_number, title=request.title,
            source_snippet=request.source_snippet, user_notes=request.user_notes,
            category=request.category, start_date=request.start_date,
            end_date=request.end_date,
        )
        self.items[self.items.index(current)] = updated
        return updated

    def delete(self, evidence_id):
        self.calls.append("delete")
        previous = len(self.items)
        self.items = [item for item in self.items if item.id != evidence_id]
        return len(self.items) != previous


class EvidenceDraftTests(unittest.TestCase):
    def test_empty_is_comparable_and_allows_incomplete_fields(self):
        empty = EvidenceDraft.empty()
        self.assertEqual(empty, EvidenceDraft())
        self.assertNotEqual(empty, replace(empty, title="Em edição"))
        self.assertFalse(empty.is_minimally_valid())

    def test_from_evidence_and_request_conversions(self):
        item = evidence(notes="Nota")
        draft = EvidenceDraft.from_evidence(item)
        self.assertEqual(draft.evidence_id, item.id)
        self.assertEqual(draft.to_update_request().user_notes, "Nota")
        create = replace(draft, evidence_id=None).to_create_request()
        self.assertEqual(create.document_sha256, SHA_A)

    def test_create_rejects_id_update_requires_id_and_validation_is_final(self):
        with self.assertRaises(ValueError):
            EvidenceDraft(evidence_id=str(uuid4())).to_create_request()
        with self.assertRaises(ValueError):
            EvidenceDraft.empty().to_update_request()
        with self.assertRaises(ValueError):
            EvidenceDraft(title="incompleto").to_create_request()

    def test_source_candidate_conversion_preserves_search_fields(self):
        from models import EvidenceSourceCandidate
        candidate = EvidenceSourceCandidate(
            SHA_A, 7, "Trecho da busca", suggested_title="Documento encontrado"
        )
        draft = EvidenceDraft.from_source_candidate(candidate)
        self.assertIsNone(draft.evidence_id)
        self.assertEqual(draft.document_sha256, SHA_A)
        self.assertEqual(draft.page_number, 7)
        self.assertEqual(draft.source_snippet, "Trecho da busca")
        self.assertEqual(draft.title, "Documento encontrado")
        self.assertEqual(draft.category, "")


class EvidenceControllerTests(unittest.TestCase):
    def make_controller(self, items=(), decisions=None, duplicate=True, delete=True):
        workspace = WorkspaceDouble()
        service = ServiceDouble(items)
        decisions = list(decisions or [])
        messages = []
        controller = EvidenceController(
            workspace, service,
            confirm_unsaved=lambda: decisions.pop(0) if decisions else "cancel",
            confirm_duplicates=lambda _items: duplicate,
            confirm_delete=lambda _item: delete,
            notify=lambda kind, message: messages.append((kind, message)),
        )
        return controller, workspace, service, messages

    def test_load_count_selection_editor_and_source_statuses(self):
        first, second = evidence("A"), evidence("B", SHA_B)
        controller, workspace, service, _ = self.make_controller((first, second))
        service.available[second.id] = False
        self.assertTrue(controller.load())
        self.assertEqual(len(workspace.items), 2)
        self.assertEqual(workspace.statuses[first.id], EvidenceSourceStatus.AVAILABLE)
        self.assertEqual(workspace.statuses[second.id], EvidenceSourceStatus.UNAVAILABLE)
        self.assertTrue(controller.select(first.id))
        self.assertEqual(workspace.draft.title, "A")
        self.assertEqual(controller.mode, EvidenceEditorMode.VIEWING)

    def test_create_full_flow_clears_dirty_and_selects_created(self):
        controller, workspace, service, messages = self.make_controller()
        controller.load()
        controller.start_create()
        draft = EvidenceDraft(document_sha256=SHA_A, title="Nova", category="Ensino")
        controller.update_draft(draft)
        self.assertTrue(controller.dirty)
        self.assertTrue(controller.save())
        self.assertEqual(service.calls.count("create"), 1)
        self.assertEqual(controller.mode, EvidenceEditorMode.VIEWING)
        self.assertFalse(controller.dirty)
        self.assertEqual(controller.selected_evidence.title, "Nova")
        self.assertEqual(messages[-1][0], "success")

    def test_invalid_create_has_friendly_error(self):
        controller, _, service, messages = self.make_controller()
        controller.start_create()
        controller.update_draft(EvidenceDraft(title="Sem documento"))
        self.assertFalse(controller.save())
        self.assertNotIn("create", service.calls)
        self.assertEqual(messages[-1], ("error", "Revise os dados da evidência."))

    def test_duplicate_can_continue_or_cancel(self):
        duplicate_item = evidence()
        for allowed in (False, True):
            controller, _, service, _ = self.make_controller(duplicate=allowed)
            service.duplicates = (duplicate_item,)
            controller.start_create()
            controller.update_draft(EvidenceDraft(document_sha256=SHA_A, title="Nova"))
            self.assertEqual(controller.save(), allowed)

    def test_edit_save_preserves_selection_and_cancel_restores_baseline(self):
        item = evidence()
        controller, workspace, service, _ = self.make_controller((item,))
        controller.load()
        controller.select(item.id)
        controller.update_draft(replace(controller.current_draft, user_notes="Mudou"))
        self.assertEqual(controller.mode, EvidenceEditorMode.EDITING)
        controller.cancel()
        self.assertFalse(controller.dirty)
        self.assertIsNone(workspace.draft.user_notes or None)
        controller.update_draft(replace(controller.current_draft, title="Atualizada"))
        self.assertTrue(controller.save())
        self.assertEqual(controller.selected_evidence.id, item.id)
        self.assertEqual(service.calls.count("update"), 1)

    def test_cancel_creation_and_delete_confirmations(self):
        item = evidence()
        controller, _, service, _ = self.make_controller((item,), delete=False)
        controller.load(); controller.select(item.id)
        self.assertFalse(controller.delete())
        self.assertNotIn("delete", service.calls)
        controller.start_create(); controller.update_draft(EvidenceDraft(title="x"))
        controller.cancel()
        self.assertEqual(controller.mode, EvidenceEditorMode.EMPTY)

    def test_dirty_selection_save_discard_and_cancel(self):
        first, second = evidence("A"), evidence("B")
        for decision, expected, changed in (
            ("save", second.id, True),
            ("discard", second.id, False),
            ("cancel", first.id, False),
        ):
            controller, workspace, service, _ = self.make_controller(
                (first, second), decisions=[decision]
            )
            controller.load(); controller.select(first.id)
            controller.update_draft(replace(controller.current_draft, title="Alterada"))
            result = controller.select(second.id)
            self.assertEqual(workspace.selected, expected)
            self.assertEqual("update" in service.calls, changed)
            self.assertEqual(result, decision != "cancel")

    def test_can_leave_and_clear_protect_project_change(self):
        controller, workspace, _, _ = self.make_controller(decisions=["cancel", "discard"])
        controller.start_create(); controller.update_draft(EvidenceDraft(title="x"))
        self.assertFalse(controller.can_leave())
        self.assertTrue(controller.can_leave())
        controller.clear()
        self.assertEqual(controller.mode, EvidenceEditorMode.EMPTY)
        self.assertEqual(workspace.items, ())

    def test_start_create_from_source_is_dirty_locked_and_not_persisted(self):
        from models import EvidenceSourceCandidate
        controller, workspace, service, _ = self.make_controller()
        candidate = EvidenceSourceCandidate(
            SHA_A, 9, "Trecho", suggested_title="Título sugerido"
        )
        self.assertTrue(controller.start_create_from_source(candidate))
        self.assertEqual(controller.mode, EvidenceEditorMode.CREATING)
        self.assertTrue(controller.dirty)
        self.assertTrue(workspace.source_locked)
        self.assertEqual(workspace.source_status, EvidenceSourceStatus.AVAILABLE)
        self.assertEqual(workspace.draft.page_number, 9)
        self.assertNotIn("create", service.calls)

    def test_source_unavailable_is_presented_and_cancel_does_not_persist(self):
        from models import EvidenceSourceCandidate
        controller, workspace, service, _ = self.make_controller()
        candidate = EvidenceSourceCandidate(
            SHA_B, None, "", suggested_title="Sem página"
        )
        self.assertTrue(controller.start_create_from_source(candidate))
        self.assertEqual(workspace.source_status, EvidenceSourceStatus.UNAVAILABLE)
        controller.cancel()
        self.assertEqual(controller.mode, EvidenceEditorMode.EMPTY)
        self.assertNotIn("create", service.calls)

    def test_source_request_protects_previous_dirty_state(self):
        from models import EvidenceSourceCandidate
        candidate = EvidenceSourceCandidate(
            SHA_A, 5, "Novo trecho", suggested_title="Nova origem"
        )
        for decision, accepted, saved in (
            ("save", True, True),
            ("discard", True, False),
            ("cancel", False, False),
        ):
            with self.subTest(decision=decision):
                controller, workspace, service, _ = self.make_controller(
                    decisions=[decision]
                )
                controller.start_create()
                controller.update_draft(
                    EvidenceDraft(document_sha256=SHA_A, title="Anterior")
                )
                self.assertEqual(
                    controller.start_create_from_source(candidate), accepted
                )
                self.assertEqual("create" in service.calls, saved)
                if accepted:
                    self.assertEqual(workspace.draft.title, "Nova origem")
                else:
                    self.assertEqual(controller.current_draft.title, "Anterior")


if __name__ == "__main__":
    unittest.main()
