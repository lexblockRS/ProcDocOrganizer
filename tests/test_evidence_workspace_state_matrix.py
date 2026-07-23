"""Caracterização do estado visual observável do Evidence Workspace."""

from dataclasses import asdict, dataclass
import os
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication, QPushButton

from controllers import EvidenceEditorMode
from models import EvidenceDraft
from services import EvidenceSourceStatus
from tests.test_evidence_workspace import make_evidence
from ui.views import EvidenceWorkspace


@dataclass(frozen=True)
class WorkspaceSnapshot:
    draft: EvidenceDraft
    evidence_id: str | None
    selected_id: str | None
    evidence_count: int
    new_enabled: bool
    save_enabled: bool
    cancel_enabled: bool
    delete_enabled: bool
    refresh_enabled: bool
    identity_read_only: bool
    source_status: str
    message: str
    dirty_text: str


def snapshot(workspace):
    draft = workspace.editor_widget.draft()
    return WorkspaceSnapshot(
        draft=draft,
        evidence_id=draft.evidence_id,
        selected_id=workspace.list_widget.current_evidence_id(),
        evidence_count=workspace.list_widget.visible_count(),
        new_enabled=workspace.new_button.isEnabled(),
        save_enabled=workspace.save_button.isEnabled(),
        cancel_enabled=workspace.cancel_button.isEnabled(),
        delete_enabled=workspace.delete_button.isEnabled(),
        refresh_enabled=workspace.refresh_button.isEnabled(),
        identity_read_only=workspace.editor_widget.sha_edit.isReadOnly(),
        source_status=workspace.source_status_widget.label.text(),
        message=workspace.message_label.text(),
        dirty_text=workspace.dirty_label.text(),
    )


def apply_projection(workspace, mode, dirty, valid, draft, locked=False):
    creating = mode == EvidenceEditorMode.CREATING
    workspace._apply_editor_projection(
        mode,
        dirty,
        valid,
        draft=draft,
        source_status=None,
        source_locked=locked,
        editor_enabled=mode != EvidenceEditorMode.EMPTY,
        identity_editable=creating and not locked,
        save_enabled=dirty and valid,
        cancel_enabled=dirty or creating,
        delete_enabled=mode in (
            EvidenceEditorMode.VIEWING, EvidenceEditorMode.EDITING
        ),
    )


class EvidenceWorkspaceStateMatrixTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.workspace = EvidenceWorkspace()

    def tearDown(self):
        self.workspace.close()

    def test_reachable_visual_state_matrix(self):
        valid = EvidenceDraft(document_identity="a" * 64, title="Título")
        cases = (
            (
                "empty", EvidenceEditorMode.EMPTY, False, False, False,
                (False, False, False, True),
            ),
            (
                "creating-invalid", EvidenceEditorMode.CREATING, False, False,
                False, (False, True, False, False),
            ),
            (
                "creating-valid-dirty", EvidenceEditorMode.CREATING, True, True,
                False, (True, True, False, False),
            ),
            (
                "creating-source-locked", EvidenceEditorMode.CREATING, True,
                True, True, (True, True, False, True),
            ),
            (
                "viewing", EvidenceEditorMode.VIEWING, False, True, False,
                (False, False, True, True),
            ),
            (
                "editing-valid", EvidenceEditorMode.EDITING, True, True, False,
                (True, True, True, True),
            ),
            (
                "editing-invalid", EvidenceEditorMode.EDITING, True, False,
                False, (False, True, True, True),
            ),
        )
        for name, mode, dirty, valid_flag, locked, expected in cases:
            with self.subTest(name=name):
                self.workspace.clear()
                draft = valid if valid_flag else EvidenceDraft.empty()
                apply_projection(
                    self.workspace, mode, dirty, valid_flag, draft, locked
                )
                state = snapshot(self.workspace)
                self.assertEqual(
                    (
                        state.save_enabled,
                        state.cancel_enabled,
                        state.delete_enabled,
                        state.identity_read_only,
                    ),
                    expected,
                )
                self.assertTrue(state.new_enabled)
                self.assertTrue(state.refresh_enabled)
                self.assertEqual(bool(state.dirty_text), dirty)

    def test_programmatic_render_and_clear_do_not_emit_draft_changed(self):
        emitted = []
        self.workspace.draft_changed.connect(emitted.append)
        draft = EvidenceDraft(document_identity="a" * 64, title="Título")

        self.workspace.set_draft(draft, creating=True)
        self.workspace.set_editor_state(
            EvidenceEditorMode.CREATING, True, True
        )
        self.workspace.clear()

        self.assertEqual(emitted, [])
        self.assertEqual(snapshot(self.workspace).draft, EvidenceDraft.empty())

    def test_all_visual_intent_signals_emit_once_from_current_controls(self):
        counts = {
            name: 0 for name in
            ("new", "save", "cancel", "delete", "refresh")
        }
        for name in counts:
            signal = getattr(self.workspace, f"{name}_requested")
            signal.connect(lambda name=name: counts.__setitem__(
                name, counts[name] + 1
            ))
        self.workspace.set_draft(
            EvidenceDraft(document_identity="a" * 64, title="Título"),
            creating=True,
        )
        self.workspace.set_editor_state(
            EvidenceEditorMode.CREATING, True, True
        )

        self.workspace.new_button.click()
        self.workspace.save_button.click()
        self.workspace.cancel_button.click()
        self.workspace.delete_button.setEnabled(True)
        self.workspace.delete_button.click()
        self.workspace.refresh_button.click()

        self.assertEqual(counts, {name: 1 for name in counts})

    def test_draft_changed_contains_complete_visible_form(self):
        emitted = []
        self.workspace.draft_changed.connect(emitted.append)
        self.workspace.set_draft(
            EvidenceDraft(
                document_identity="a" * 64, title="Original", page_number=3
            ),
            creating=True,
        )
        self.workspace.set_editor_state(
            EvidenceEditorMode.CREATING, True, True
        )

        self.workspace.editor_widget.title_edit.setText("Alterado")

        self.assertEqual(len(emitted), 1)
        self.assertEqual(emitted[0].title, "Alterado")
        self.assertEqual(emitted[0].document_identity, "a" * 64)
        self.assertEqual(emitted[0].page_number, 3)

    def test_selection_filter_reload_and_source_lock_transitions(self):
        first, second = make_evidence("Primeira"), make_evidence("Segunda")
        self.workspace.set_evidences(
            (first, second),
            {
                first.id: EvidenceSourceStatus.AVAILABLE,
                second.id: EvidenceSourceStatus.UNAVAILABLE,
            },
        )
        self.workspace.select_evidence(second.id)
        self.workspace.list_widget.filter_edit.setText("Segunda")
        self.assertEqual(snapshot(self.workspace).selected_id, second.id)

        self.workspace.set_evidences((first, second))
        self.assertEqual(snapshot(self.workspace).selected_id, second.id)

        apply_projection(
            self.workspace,
            EvidenceEditorMode.CREATING,
            True,
            True,
            EvidenceDraft.from_evidence(second),
            True,
        )
        self.assertTrue(snapshot(self.workspace).identity_read_only)

        apply_projection(
            self.workspace,
            EvidenceEditorMode.VIEWING,
            False,
            True,
            EvidenceDraft.from_evidence(first),
            True,
        )
        self.assertTrue(snapshot(self.workspace).identity_read_only)
        self.workspace.clear()
        self.assertTrue(snapshot(self.workspace).identity_read_only)

    def test_workspace_does_not_infer_lock_from_draft_identity(self):
        draft = EvidenceDraft(
            document_identity="a" * 64, title="Documento"
        )

        apply_projection(
            self.workspace,
            EvidenceEditorMode.CREATING,
            True,
            True,
            draft,
            False,
        )
        self.assertFalse(snapshot(self.workspace).identity_read_only)

        apply_projection(
            self.workspace,
            EvidenceEditorMode.CREATING,
            True,
            True,
            draft,
            True,
        )
        self.assertTrue(snapshot(self.workspace).identity_read_only)
        self.assertFalse(hasattr(self.workspace, "_source_locked"))

    def test_project_hooks_preserve_open_state_and_clear_closed_state(self):
        item = make_evidence()
        self.workspace.set_evidences((item,))
        before = snapshot(self.workspace)

        self.workspace.on_project_opened(object())
        self.assertEqual(snapshot(self.workspace), before)

        self.workspace.on_project_closed()
        state = snapshot(self.workspace)
        self.assertEqual(state.evidence_count, 0)
        self.assertIsNone(state.selected_id)
        self.assertEqual(state.draft, EvidenceDraft.empty())

    def test_open_document_signal_exists_but_no_current_button_emits_it(self):
        emitted = []
        self.workspace.open_document_requested.connect(
            lambda: emitted.append("open")
        )

        for button in self.workspace.findChildren(QPushButton):
            button.click()

        # Comportamento atual a reavaliar na IS-9.1.5: não há emissor visual.
        self.assertEqual(emitted, [])


if __name__ == "__main__":
    unittest.main()
