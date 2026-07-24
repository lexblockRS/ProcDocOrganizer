import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import unittest
from uuid import uuid4

from PySide6.QtWidgets import QApplication

from controllers import EvidenceController, SearchController
from models import Evidence
from services.search import SearchHit, SearchResultPage
from ui.views import EvidenceWorkspace, SearchWorkspace


SHA = "a" * 64


class SearchServiceDouble:
    def __init__(self, hit):
        self.page = SearchResultPage((hit,), 0, 1, None, False)

    def search(self, _query):
        return self.page


class EvidenceServiceDouble:
    def __init__(self):
        self.items = []
        self.create_calls = 0

    def list_all(self):
        return tuple(self.items)

    def is_source_available(self, _evidence):
        return True

    def is_document_available(self, sha):
        return sha == SHA

    def find_potential_duplicates(self, _sha, _page, _title):
        return ()

    def create(self, request):
        self.create_calls += 1
        item = Evidence.create(
            request.document_identity, request.title,
            page_number=request.page_number,
            source_snippet=request.source_snippet,
            user_notes=request.user_notes, category=request.category,
            start_date=request.start_date, end_date=request.end_date,
            evidence_id=str(uuid4()), timestamp="2026-01-01T10:00:00",
        )
        self.items.append(item)
        return item


class SearchToEvidenceFlowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.hit = SearchHit(
            document_identity=SHA,
            document_name="Portaria 42/2026",
            page_number=12,
            snippet="Participação em comissão institucional",
            score=1.0,
        )
        self.search_workspace = SearchWorkspace()
        self.evidence_workspace = EvidenceWorkspace()
        self.evidence_service = EvidenceServiceDouble()
        self.evidence_controller = EvidenceController(
            self.evidence_workspace, self.evidence_service,
            confirm_duplicates=lambda _items: True,
        )
        self.current_workspace = "search"

        def coordinate(candidate):
            accepted = self.evidence_controller.start_create_from_source(
                candidate
            )
            if accepted:
                self.current_workspace = "evidence"
            return accepted

        self.search_controller = SearchController(
            self.search_workspace, SearchServiceDouble(self.hit), coordinate
        )

    def tearDown(self):
        self.search_workspace.close()
        self.evidence_workspace.close()

    def _prepare_from_search(self):
        self.search_controller.search("comissão")
        self.search_workspace.results_widget.results_list.setCurrentRow(0)
        self.search_workspace.search_panel.create_evidence_button.click()

    def test_full_flow_prepares_edits_and_saves_once(self):
        self._prepare_from_search()
        self.assertEqual(self.current_workspace, "evidence")
        self.assertIs(self.search_workspace.selected_result(), self.hit)
        draft = self.evidence_controller.current_draft
        self.assertEqual(draft.document_identity, SHA)
        self.assertEqual(draft.page_number, 12)
        self.assertEqual(draft.source_snippet, self.hit.snippet)
        self.assertTrue(self.evidence_controller.dirty)
        self.assertTrue(
            self.evidence_workspace.editor_widget.sha_edit.isReadOnly()
        )

        self.evidence_workspace.editor_widget.title_edit.setText(
            "Título revisado"
        )
        self.evidence_workspace.editor_widget.notes_edit.setPlainText(
            "Nota do usuário"
        )
        self.assertTrue(self.evidence_controller.save())

        self.assertEqual(self.evidence_service.create_calls, 1)
        self.assertEqual(
            self.evidence_controller.selected_evidence.title,
            "Título revisado",
        )
        self.assertFalse(self.evidence_controller.dirty)
        self.assertIs(self.search_workspace.selected_result(), self.hit)

    def test_cancel_does_not_persist_and_preserves_search(self):
        self._prepare_from_search()
        self.evidence_controller.cancel()
        self.assertEqual(self.evidence_service.create_calls, 0)
        self.assertEqual(self.evidence_service.items, [])
        self.assertIs(self.search_workspace.selected_result(), self.hit)


if __name__ == "__main__":
    unittest.main()
