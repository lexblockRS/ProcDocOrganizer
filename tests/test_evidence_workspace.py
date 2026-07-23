import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import unittest
from uuid import uuid4

from PySide6.QtWidgets import QApplication

from controllers import EvidenceEditorMode
from models import Evidence, EvidenceDraft
from services import EvidenceSourceStatus
from ui.main_window import MainWindow
from ui.views import EvidenceWorkspace
from ui.widgets import EvidenceEditorWidget, EvidenceListWidget, EvidenceSourceStatusWidget


def make_evidence(title="Portaria", category="Ensino", notes="Nota relevante"):
    return Evidence.create(
        "a" * 64, title, page_number=3, category=category, user_notes=notes,
        start_date="2025-01-01", evidence_id=str(uuid4()),
        timestamp="2026-01-01T10:00:00",
    )


class EvidenceWidgetTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_list_empty_content_filter_selection_and_count(self):
        workspace = EvidenceWorkspace()
        first = make_evidence("Portaria de ensino")
        second = make_evidence("Projeto", "Pesquisa")
        selected = []
        workspace.evidence_selected.connect(selected.append)
        workspace.set_evidences(
            (first, second),
            {first.id: EvidenceSourceStatus.AVAILABLE,
             second.id: EvidenceSourceStatus.UNAVAILABLE},
        )
        self.assertEqual(workspace.list_widget.visible_count(), 2)
        self.assertEqual(workspace.count_label.text(), "2 evidências")
        self.assertIn("Disponível", workspace.list_widget.list_widget.item(0).text())
        workspace.list_widget.filter_edit.setText("pesquisa")
        self.assertEqual(workspace.list_widget.visible_count(), 1)
        workspace.list_widget.list_widget.setCurrentRow(0)
        self.assertEqual(selected[-1], second.id)
        workspace.set_evidences(())
        self.assertTrue(workspace.list_widget.empty_label.isVisibleTo(workspace.list_widget))
        workspace.close()

    def test_editor_fill_does_not_emit_but_user_change_emits_draft(self):
        editor = EvidenceEditorWidget()
        emitted = []
        editor.draft_changed.connect(emitted.append)
        draft = EvidenceDraft(
            evidence_id=str(uuid4()), document_sha256="a" * 64,
            page_number=4, title="Título", source_snippet="Trecho",
            user_notes="Notas", category="Ensino", start_date="2025-01-01",
        )
        editor.set_draft(draft)
        self.assertEqual(emitted, [])
        self.assertEqual(editor.draft(), draft)
        self.assertTrue(editor.sha_edit.isReadOnly())
        editor.title_edit.setText("Novo título")
        self.assertEqual(emitted[-1].title, "Novo título")
        editor.clear()
        self.assertEqual(editor.title_edit.text(), "")
        editor.close()

    def test_source_status_messages(self):
        widget = EvidenceSourceStatusWidget()
        widget.set_status(EvidenceSourceStatus.AVAILABLE)
        self.assertIn("disponível", widget.label.text())
        widget.set_status(EvidenceSourceStatus.UNAVAILABLE)
        self.assertIn("indisponível", widget.label.text())
        widget.set_status(None)
        self.assertIn("Nenhuma", widget.label.text())
        widget.close()

    def test_workspace_button_and_dirty_states(self):
        workspace = EvidenceWorkspace()
        workspace.set_editor_state(EvidenceEditorMode.EMPTY, False, False)
        self.assertTrue(workspace.new_button.isEnabled())
        self.assertFalse(workspace.save_button.isEnabled())
        self.assertFalse(workspace.delete_button.isEnabled())
        workspace.set_editor_state(EvidenceEditorMode.CREATING, True, True)
        self.assertTrue(workspace.save_button.isEnabled())
        self.assertTrue(workspace.cancel_button.isEnabled())
        self.assertFalse(workspace.delete_button.isEnabled())
        self.assertIn("não salvas", workspace.dirty_label.text())
        workspace.set_editor_state(EvidenceEditorMode.VIEWING, False, True)
        self.assertFalse(workspace.save_button.isEnabled())
        self.assertTrue(workspace.delete_button.isEnabled())
        workspace.close()

    def test_main_window_contains_central_evidence_workspace(self):
        window = MainWindow()
        self.assertIs(window.views["evidence"], window.evidence_workspace)
        window.show_evidences()
        self.assertIs(window.stack.currentWidget(), window.evidence_workspace)
        window.close()

    def test_project_close_hook_does_not_clear_evidence_twice(self):
        window = MainWindow()
        calls = []
        window.evidence_workspace.on_project_closed = (
            lambda: calls.append("evidence")
        )
        window.documents_workspace.on_project_closed = (
            lambda: calls.append("documents")
        )

        window.clear_project()

        self.assertNotIn("evidence", calls)
        self.assertIn("documents", calls)
        window.close()


if __name__ == "__main__":
    unittest.main()
