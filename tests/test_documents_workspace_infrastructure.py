import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import unittest
from unittest.mock import Mock, patch

from PySide6.QtWidgets import QApplication

from controllers import DocumentsController
from contracts import DocumentNavigationRequest
from models import (
    DocumentAvailability, DocumentDetails, DocumentPageSummary, DocumentSummary,
)
from ui.main_window import MainWindow
from ui.views import DocumentsWorkspace
from services.document_service import (
    DocumentNotFoundError,
    DocumentPageNotFoundError,
)


SHA = "a" * 64


def summary():
    return DocumentSummary(
        SHA, SHA, "Documento.pdf", "documents/Meu  Documento.pdf", "portaria",
        None, 1, "processed", DocumentAvailability.AVAILABLE, True,
    )


def details():
    return DocumentDetails(
        summary(), "2026-01-01", "2026-01-02", "native", False, None,
        {}, 1, True,
    )


def page():
    return DocumentPageSummary(SHA, SHA, 1, "Texto integral", "native", 14)


class DocumentsWorkspaceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.workspace = DocumentsWorkspace()

    def tearDown(self):
        self.workspace.close()

    def test_minimal_states_and_public_receivers(self):
        self.assertEqual(self.workspace.state, "no_project")
        self.workspace.set_catalog(())
        self.workspace.set_state("empty")
        self.assertEqual(self.workspace.state, "empty")
        self.workspace.set_catalog((summary(),))
        self.workspace.set_details(details())
        self.workspace.set_pages((page(),))
        self.workspace.set_page(page())
        self.assertEqual(self.workspace.catalog, (summary(),))
        self.assertEqual(self.workspace.details.summary.identity, SHA)
        self.assertEqual(self.workspace.pages[0].page_number, 1)
        self.assertEqual(self.workspace.current_page.text, "Texto integral")

    def test_selection_signals_and_clear_project(self):
        documents = []
        pages = []
        self.workspace.document_selected.connect(documents.append)
        self.workspace.page_selected.connect(pages.append)
        self.workspace.set_catalog((summary(),))
        self.workspace.document_list_widget.list_widget.setCurrentRow(0)
        self.workspace.set_pages((page(),))
        self.workspace.page_list_widget.list_widget.setCurrentRow(0)
        self.assertEqual(documents, [SHA])
        self.assertEqual(pages, [1])
        self.workspace.on_project_closed()
        self.assertEqual(self.workspace.state, "no_project")
        self.assertEqual(self.workspace.catalog, ())

    def test_main_window_registers_and_enables_documents_only_with_project(self):
        window = MainWindow()
        try:
            self.assertIs(window.views["documents"], window.documents_workspace)
            self.assertFalse(window.action_documents_workspace.isEnabled())
            project = Mock(project_name="Projeto")
            window.set_project(project, [])
            self.assertTrue(window.action_documents_workspace.isEnabled())
            window.show_documents()
            self.assertIs(window.stack.currentWidget(), window.documents_workspace)
            window.clear_project()
            self.assertFalse(window.action_documents_workspace.isEnabled())
        finally:
            window.close()


class DocumentsControllerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.workspace = DocumentsWorkspace()
        self.service = Mock()
        self.service.list_documents.return_value = (summary(),)
        self.service.get_document.return_value = details()
        self.service.list_pages.return_value = (page(),)
        self.service.get_page.return_value = page()
        self.controller = DocumentsController(self.workspace, self.service)

    def tearDown(self):
        self.workspace.close()

    def test_load_refresh_select_document_and_page(self):
        self.assertTrue(self.controller.load())
        self.assertEqual(self.controller.catalog, (summary(),))
        self.assertEqual(self.workspace.state, "ready")
        self.assertTrue(self.controller.select_document(SHA))
        self.assertEqual(self.controller.selected_identity, SHA)
        self.assertTrue(self.controller.select_page(1))
        self.assertEqual(self.controller.selected_page_number, 1)
        self.assertTrue(self.controller.refresh())
        self.assertEqual(self.service.list_documents.call_count, 2)

    def test_refresh_preserves_document_and_page_selection(self):
        self.assertTrue(self.controller.load())
        self.assertTrue(self.controller.select_document(SHA))
        self.assertTrue(self.controller.select_page(1))

        self.assertTrue(self.controller.refresh())

        self.assertEqual(self.controller.selected_identity, SHA)
        self.assertEqual(self.controller.selected_page_number, 1)
        self.assertEqual(self.workspace.document_list_widget.current_identity(), SHA)
        self.assertEqual(self.workspace.page_list_widget.current_page_number(), 1)
        self.assertEqual(self.workspace.current_page.text, "Texto integral")

    def test_refresh_clears_only_selection_that_no_longer_exists(self):
        self.controller.load()
        self.controller.select_document(SHA)
        self.controller.select_page(1)
        self.service.list_pages.return_value = ()

        self.assertTrue(self.controller.refresh())
        self.assertEqual(self.controller.selected_identity, SHA)
        self.assertIsNone(self.controller.selected_page_number)
        self.assertIsNone(self.workspace.current_page)

        self.service.list_documents.return_value = ()
        self.assertTrue(self.controller.refresh())
        self.assertIsNone(self.controller.selected_identity)
        self.assertIsNone(self.workspace.details)
        self.assertEqual(self.workspace.pages, ())

    def test_missing_service_and_clear(self):
        self.controller.set_service(None)
        self.assertFalse(self.controller.load())
        self.assertEqual(self.workspace.state, "no_project")
        self.assertIsNone(self.controller.selected_identity)

    def test_navigation_resolves_identity_and_selects_requested_page(self):
        self.assertTrue(self.controller.load())
        request = DocumentNavigationRequest(SHA, 1)
        self.assertTrue(self.controller.navigate(request))
        self.assertEqual(self.controller.selected_identity, SHA)
        self.assertEqual(self.controller.selected_page_number, 1)
        self.assertEqual(
            self.workspace.document_list_widget.current_identity(), SHA
        )
        self.assertEqual(
            self.workspace.page_list_widget.current_page_number(), 1
        )
        self.assertEqual(self.workspace.current_page.text, "Texto integral")

    def test_navigation_without_page_selects_only_document(self):
        self.assertTrue(self.controller.load())
        self.assertTrue(
            self.controller.navigate(DocumentNavigationRequest(SHA))
        )
        self.assertEqual(self.controller.selected_identity, SHA)
        self.assertIsNone(self.controller.selected_page_number)
        self.assertIsNone(self.workspace.current_page)

    def test_navigation_reports_missing_document_and_page(self):
        self.assertTrue(self.controller.load())
        self.service.get_document.side_effect = DocumentNotFoundError()
        self.assertFalse(
            self.controller.navigate(DocumentNavigationRequest("missing", 1))
        )
        self.assertEqual(
            self.workspace.message_label.text(),
            DocumentsController.NAVIGATION_ERROR_MESSAGE,
        )
        self.service.get_document.side_effect = None

        self.service.get_page.side_effect = DocumentPageNotFoundError()
        self.assertFalse(
            self.controller.navigate(DocumentNavigationRequest(SHA, 99))
        )
        self.assertEqual(
            self.workspace.message_label.text(),
            DocumentsController.PAGE_NAVIGATION_ERROR_MESSAGE,
        )

    def test_navigation_rejects_wrong_contract_without_search_dependency(self):
        self.assertFalse(self.controller.navigate(object()))
        self.assertEqual(
            self.workspace.message_label.text(),
            DocumentsController.NAVIGATION_ERROR_MESSAGE,
        )

    def test_errors_are_logged_and_translated(self):
        operations = (
            ("list_documents", self.controller.load,
             "Não foi possível carregar os documentos"),
            ("get_document", lambda: self.controller.select_document(SHA),
             "Não foi possível carregar os detalhes"),
        )
        for method, operation, message in operations:
            with self.subTest(method=method):
                getattr(self.service, method).side_effect = RuntimeError("interno")
                with patch("controllers.documents_controller.logger.exception") as logged:
                    self.assertFalse(operation())
                logged.assert_called_once()
                self.assertIn(message, self.workspace.message_label.text())
                getattr(self.service, method).side_effect = None

        self.controller.selected_identity = SHA
        self.service.get_page.side_effect = RuntimeError("interno")
        with patch("controllers.documents_controller.logger.exception") as logged:
            self.assertFalse(self.controller.select_page(99))
        logged.assert_called_once()
        self.assertIn("página selecionada", self.workspace.message_label.text())


if __name__ == "__main__":
    unittest.main()
