"""Caracterização do lifecycle de Evidence entre projetos."""

import unittest

from controllers.evidence_controller import EvidenceController, EvidenceEditorMode
from models import EvidenceDraft
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

    def test_close_project_and_additional_ui_hook_clear_twice(self):
        item = evidence()
        controller, workspace, prompts = self.controller()
        controller.set_service(ServiceDouble((item,)))
        before = workspace.clear_count

        self.assertTrue(controller.can_leave())
        controller.set_service(None)
        workspace.on_project_closed()

        self.assertEqual(prompts, [])
        self.assertEqual(workspace.clear_count, before + 2)
        self.assertIsNone(controller.service)
        self.assertEqual(workspace.items, ())
        self.assertEqual(controller.mode, EvidenceEditorMode.EMPTY)
        self.assertEqual(controller.current_draft, EvidenceDraft.empty())
        self.assertEqual(controller.baseline_draft, EvidenceDraft.empty())

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
