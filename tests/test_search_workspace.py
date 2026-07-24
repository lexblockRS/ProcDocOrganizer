import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from unittest.mock import Mock, patch
import unittest

from PySide6.QtWidgets import QApplication

from controllers import SearchController
from contracts import DocumentNavigationRequest
from services.search import (
    InvalidSearchQueryError,
    SearchExecutionError,
    SearchHit,
    SearchIndexCorruptedError,
    SearchIndexUnavailableError,
    SearchMatchMode,
    SearchOptions,
    SearchQuery,
    SearchResultPage,
    SearchSort,
    UnsupportedSearchFeatureError,
)
from ui.main_window import MainWindow
from ui.views import SearchWorkspace


class SearchWorkspaceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.workspace = SearchWorkspace()
        self.service = Mock()
        self.controller = SearchController(self.workspace, self.service)
        self.hit = SearchHit(
            document_identity="a" * 64,
            document_name="Portaria 42/2026",
            page_number=1,
            snippet="…jabuticaba federal…",
            score=1.0,
        )
        self.page = SearchResultPage(
            (self.hit,), offset=0, page_size=1,
            total_hits=None, has_more=False,
        )

    def tearDown(self):
        self.workspace.close()

    def test_public_signals_are_preserved(self):
        for signal in (
            "search_requested", "clear_requested", "result_selected",
            "create_evidence_requested",
        ):
            self.assertTrue(hasattr(self.workspace, signal))

    def test_empty_search_is_validated_without_calling_service(self):
        self.controller.search("   ")
        self.service.search.assert_not_called()
        self.assertEqual(
            self.workspace.search_panel.message_label.text(),
            SearchController.EMPTY_MESSAGE,
        )
        self.assertEqual(self.workspace.results_widget.result_count(), 0)

    def test_valid_search_builds_query_and_passes_page_to_workspace(self):
        self.service.search.return_value = self.page
        self.controller.search("  jabuticaba  ")
        self.service.search.assert_called_once()
        query = self.service.search.call_args.args[0]
        self.assertIsInstance(query, SearchQuery)
        self.assertEqual(query.text, "jabuticaba")
        self.assertEqual(
            query.options.match_mode, SearchMatchMode.ALL_TERMS
        )
        self.assertIs(self.workspace.result_page, self.page)
        self.assertEqual(self.workspace.results_widget.result_count(), 1)
        self.assertEqual(
            self.workspace.search_panel.result_count_label.text(),
            "Resultados: 1",
        )

    def test_controller_preserves_modes_filters_limit_offset_and_sort(self):
        self.service.search.return_value = self.page
        options = SearchOptions(
            limit=12,
            offset=4,
            sort=SearchSort.DOCUMENT_DATE_DESC,
            match_mode=SearchMatchMode.EXACT_PHRASE,
            document_type="portaria",
            start_date="2025-01-01",
            end_date="2026-12-31",
        )
        self.controller.search("ato administrativo", options)
        query = self.service.search.call_args.args[0]
        self.assertIs(query.options, options)
        self.assertEqual(query.options.limit, 12)
        self.assertEqual(query.options.offset, 4)
        self.assertEqual(query.options.document_type, "portaria")
        self.assertEqual(
            query.options.match_mode, SearchMatchMode.EXACT_PHRASE
        )

        any_options = SearchOptions(match_mode=SearchMatchMode.ANY_TERM)
        self.controller.search("ato portaria", any_options)
        self.assertEqual(
            self.service.search.call_args.args[0].options.match_mode,
            SearchMatchMode.ANY_TERM,
        )
        self.assertEqual(self.service.search.call_count, 2)

    def test_search_without_results_shows_friendly_message(self):
        empty = SearchResultPage((), 0, 0, None, False)
        self.service.search.return_value = empty
        self.controller.search("ausente")
        self.assertEqual(
            self.workspace.search_panel.message_label.text(),
            SearchController.NO_RESULTS_MESSAGE,
        )

    def test_public_search_errors_have_specific_safe_messages(self):
        cases = (
            (InvalidSearchQueryError("interno"), SearchController.INVALID_QUERY_MESSAGE),
            (
                UnsupportedSearchFeatureError("interno"),
                SearchController.UNSUPPORTED_FEATURE_MESSAGE,
            ),
            (
                SearchIndexUnavailableError("caminho secreto"),
                SearchController.INDEX_UNAVAILABLE_MESSAGE,
            ),
            (
                SearchIndexCorruptedError("schema secreto"),
                SearchController.INDEX_CORRUPTED_MESSAGE,
            ),
            (
                SearchExecutionError("SELECT secreto"),
                SearchController.EXECUTION_ERROR_MESSAGE,
            ),
        )
        for error, message in cases:
            with self.subTest(error=type(error).__name__):
                self.service.search.side_effect = error
                self.controller.search("consulta")
                self.assertEqual(
                    self.workspace.search_panel.message_label.text(), message
                )
                self.assertEqual(self.workspace.results_widget.result_count(), 0)
                self.assertNotIn(str(error), message)
        self.assertEqual(self.service.search.call_count, len(cases))

    def test_unexpected_search_error_is_logged_and_friendly(self):
        self.service.search.side_effect = RuntimeError("detalhe interno")
        with patch("controllers.search_controller.logger.exception") as logged:
            self.controller.search("consulta")
        logged.assert_called_once()
        self.assertEqual(
            self.workspace.search_panel.message_label.text(),
            SearchController.ERROR_MESSAGE,
        )
        self.assertNotIn(
            "detalhe interno",
            self.workspace.search_panel.message_label.text(),
        )

    def test_enter_and_button_request_search_once_each(self):
        self.service.search.return_value = SearchResultPage(
            (), 0, 0, None, False
        )
        self.workspace.search_panel.search_input.setText("portaria")
        self.workspace.search_panel.search_input.returnPressed.emit()
        self.workspace.search_panel.search_button.click()
        self.assertEqual(self.service.search.call_count, 2)

    def test_clear_button_resets_query_results_counter_preview_and_page(self):
        self.workspace.search_panel.search_input.setText("portaria")
        self.workspace.set_results(self.page)
        self.workspace.show_result(self.hit)
        self.workspace.search_panel.clear_button.click()
        self.assertEqual(self.workspace.search_panel.search_input.text(), "")
        self.assertEqual(self.workspace.results_widget.result_count(), 0)
        self.assertEqual(
            self.workspace.search_panel.result_count_label.text(),
            "Resultados: 0",
        )
        self.assertEqual(self.workspace.preview_widget.title_value.text(), "—")
        self.assertIsNone(self.workspace.result_page)

    def test_workspace_accepts_page_or_hit_sequence(self):
        self.workspace.set_results(self.page)
        self.assertIs(self.workspace.result_page, self.page)
        self.assertEqual(self.workspace.results_widget.result_count(), 1)
        self.workspace.set_results((self.hit,))
        self.assertIsNone(self.workspace.result_page)
        self.assertEqual(self.workspace.results_widget.result_count(), 1)

    def test_result_item_uses_only_search_hit_fields(self):
        self.workspace.set_results(self.page)
        text = self.workspace.results_widget.results_list.item(0).text()
        for expected in ("Portaria 42/2026", "Página 1", "jabuticaba federal"):
            self.assertIn(expected, text)
        self.assertNotIn("Tipo não informado", text)
        self.assertNotIn("Data não informada", text)

    def test_selection_updates_preview_without_opening_document(self):
        self.workspace.set_results(self.page)
        self.workspace.results_widget.results_list.setCurrentRow(0)
        preview = self.workspace.preview_widget
        self.assertEqual(preview.title_value.text(), "Portaria 42/2026")
        self.assertEqual(preview.type_value.text(), "—")
        self.assertEqual(preview.date_value.text(), "—")
        self.assertEqual(preview.page_value.text(), "1")
        self.assertEqual(preview.file_value.text(), "—")

    def test_selection_keeps_and_returns_the_same_hit(self):
        requested = []
        self.workspace.create_evidence_requested.connect(requested.append)
        self.workspace.set_results(self.page)
        button = self.workspace.search_panel.create_evidence_button
        self.assertFalse(button.isEnabled())
        self.workspace.results_widget.results_list.setCurrentRow(0)
        self.assertTrue(button.isEnabled())
        self.assertIs(self.workspace.selected_result(), self.hit)
        button.click()
        self.assertEqual(requested, [self.hit])
        self.workspace.results_widget.results_list.setCurrentItem(None)
        self.assertFalse(button.isEnabled())

    def test_selection_alone_does_not_request_document_navigation(self):
        requests = []
        self.controller.set_document_navigation_requested(
            lambda request: requests.append(request) or True
        )
        self.workspace.set_results(self.page)
        self.workspace.results_widget.results_list.setCurrentRow(0)
        self.assertEqual(requests, [])

    def test_explicit_activation_requests_navigation_once(self):
        requests = []
        self.controller.set_document_navigation_requested(
            lambda request: requests.append(request) or True
        )
        self.workspace.set_results(self.page)
        item = self.workspace.results_widget.results_list.item(0)
        self.workspace.results_widget.results_list.itemActivated.emit(item)
        self.assertEqual(len(requests), 1)
        self.assertIsInstance(requests[0], DocumentNavigationRequest)
        self.assertEqual(
            requests[0].document_identity, self.hit.document_identity
        )
        self.assertEqual(requests[0].page_number, self.hit.page_number)

    def test_navigation_failure_is_friendly_and_logged_when_unexpected(self):
        self.controller.set_document_navigation_requested(
            lambda _request: False
        )
        self.assertFalse(self.controller.request_document_navigation(self.hit))
        self.assertEqual(
            self.workspace.search_panel.message_label.text(),
            SearchController.NAVIGATION_ERROR_MESSAGE,
        )

        def fail(_request):
            raise RuntimeError("interno")

        self.controller.set_document_navigation_requested(fail)
        with patch("controllers.search_controller.logger.exception") as logged:
            self.assertFalse(
                self.controller.request_document_navigation(self.hit)
            )
        logged.assert_called_once()

    def test_search_controller_maps_selected_hit_to_evidence_candidate(self):
        candidates = []
        self.controller.set_evidence_source_requested(
            lambda candidate: candidates.append(candidate) or True
        )
        self.workspace.set_results(self.page)
        self.workspace.results_widget.results_list.setCurrentRow(0)
        self.assertTrue(
            self.controller.request_create_evidence_from_selected_result()
        )
        candidate = candidates[0]
        self.assertEqual(candidate.document_identity, self.hit.document_identity)
        self.assertEqual(candidate.page_number, self.hit.page_number)
        self.assertEqual(candidate.source_snippet, self.hit.snippet)
        self.assertEqual(candidate.document_name, self.hit.document_name)

    def test_create_evidence_without_selection_or_valid_identity_is_friendly(self):
        self.assertFalse(
            self.controller.request_create_evidence_from_selected_result()
        )
        self.assertEqual(
            self.workspace.search_panel.message_label.text(),
            SearchController.NO_SELECTION_MESSAGE,
        )
        invalid_for_evidence = type("InvalidHit", (), {
            "document_identity": "",
            "document_name": "Documento",
            "page_number": 1,
            "snippet": "",
        })()
        self.assertFalse(
            self.controller.request_create_evidence_from_result(
                invalid_for_evidence
            )
        )
        self.assertEqual(
            self.workspace.search_panel.message_label.text(),
            SearchController.INVALID_RESULT_MESSAGE,
        )

    def test_unexpected_evidence_coordination_error_is_logged(self):
        def fail(_candidate):
            raise RuntimeError("detalhe interno do coordenador")

        self.controller.set_evidence_source_requested(fail)
        self.workspace.set_results(self.page)
        self.workspace.results_widget.results_list.setCurrentRow(0)
        with patch("controllers.search_controller.logger.exception") as logged:
            self.assertFalse(
                self.controller.request_create_evidence_from_selected_result()
            )
        logged.assert_called_once()
        self.assertEqual(
            self.workspace.search_panel.message_label.text(),
            SearchController.PREPARE_EVIDENCE_ERROR_MESSAGE,
        )
        self.assertIs(self.workspace.selected_result(), self.hit)

    def test_replacing_results_clears_previous_preview(self):
        self.workspace.show_result(self.hit)
        self.workspace.set_results(SearchResultPage((), 0, 0, None, False))
        self.assertEqual(self.workspace.preview_widget.title_value.text(), "—")

    def test_main_window_opens_search_as_central_workspace(self):
        window = MainWindow()
        try:
            window.show_search()
            self.assertIs(
                window.stack.currentWidget(), window.search_workspace
            )
            self.assertIs(window.views["search"], window.search_workspace)
        finally:
            window.close()


if __name__ == "__main__":
    unittest.main()
