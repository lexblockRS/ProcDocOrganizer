import os
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication

from models import DocumentAvailability, DocumentDetails, DocumentSummary
from ui.views import DocumentsWorkspace
from ui.widgets import DocumentListWidget


def summary(
    identity,
    name,
    *,
    kind="portaria",
    path=None,
    sha=None,
    document_date=None,
    imported_at="2026-01-01",
    processing_status="not_processed",
    processed=False,
    ocr_used=False,
    extension=".pdf",
):
    return DocumentSummary(
        identity=identity,
        sha256=sha or identity,
        name=name,
        relative_path=path or f"documents/{name}",
        document_type=kind,
        document_date=document_date,
        page_count=2 if processed else 0,
        processing_status=processing_status,
        availability=DocumentAvailability.AVAILABLE,
        has_processing_result=processed,
        extension=extension,
        imported_at=imported_at,
        ocr_used=ocr_used,
    )


class DocumentWorkspaceProductivityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.items = (
            summary(
                "a" * 64,
                "Portaria Alpha.pdf",
                path="documents/acervo/alpha.pdf",
                document_date="2025-03-10",
                processing_status="processed",
                processed=True,
                ocr_used=True,
            ),
            summary(
                "b" * 64,
                "Ofício Beta.pdf",
                kind="ofício",
                path="documents/beta.pdf",
                processing_status="ocr_required",
                processed=True,
            ),
            summary(
                "c" * 64,
                "Planilha.ods",
                kind="planilha",
                extension=".ods",
            ),
        )

    def test_instant_search_uses_all_required_metadata(self):
        widget = DocumentListWidget()
        widget.set_catalog(self.items)
        for query, expected in (
            ("", 3),
            ("alpha", 1),
            ("OFÍCIO", 1),
            ("acervo/alpha", 1),
            ("b" * 64, 1),
            ("2025-03-10", 1),
            ("inexistente", 0),
        ):
            with self.subTest(query=query):
                widget.set_query(query)
                self.assertEqual(widget.list_widget.count(), expected)
        widget.close()

    def test_extensible_quick_filters_can_be_alternated(self):
        widget = DocumentListWidget()
        widget.set_catalog(self.items)
        expected = {
            "all": 3,
            "pdf": 2,
            "ocr_done": 1,
            "ocr_pending": 2,
            "processed": 1,
            "not_processed": 2,
        }
        for filter_id, count in expected.items():
            with self.subTest(filter_id=filter_id):
                widget.set_filter_id(filter_id)
                self.assertEqual(widget.list_widget.count(), count)
        widget.close()

    def test_keyboard_navigation_and_workspace_shortcuts(self):
        workspace = DocumentsWorkspace()
        workspace.set_catalog(self.items)
        opened = []
        removed = []
        imported = []
        refreshed = []
        workspace.open_requested.connect(lambda: opened.append(True))
        workspace.remove_requested.connect(lambda: removed.append(True))
        workspace.import_requested.connect(lambda: imported.append(True))
        workspace.refresh_requested.connect(lambda: refreshed.append(True))
        workspace.show()
        workspace.activateWindow()
        self.app.processEvents()
        tree = workspace.document_list_widget.list_widget
        tree.setFocus()
        tree.setCurrentRow(0)
        workspace.set_details(
            DocumentDetails(
                self.items[0],
                "2026-01-01",
                None,
                None,
                False,
                None,
            )
        )
        QTest.keyClick(tree, Qt.Key.Key_End)
        self.assertEqual(
            workspace.document_list_widget.current_identity(),
            "a" * 64,
        )
        QTest.keyClick(tree, Qt.Key.Key_Home)
        self.assertEqual(
            workspace.document_list_widget.current_identity(),
            "b" * 64,
        )
        QTest.keyClick(tree, Qt.Key.Key_PageDown)
        self.assertIsNotNone(
            workspace.document_list_widget.current_identity()
        )
        QTest.keyClick(tree, Qt.Key.Key_PageUp)
        self.assertEqual(
            workspace.document_list_widget.current_identity(),
            "b" * 64,
        )
        QTest.keyClick(tree, Qt.Key.Key_Down)
        self.assertEqual(
            workspace.document_list_widget.current_identity(),
            "c" * 64,
        )
        QTest.keyClick(tree, Qt.Key.Key_Up)
        self.assertEqual(
            workspace.document_list_widget.current_identity(),
            "b" * 64,
        )
        QTest.keyClick(tree, Qt.Key.Key_Return)
        QTest.keyClick(tree, Qt.Key.Key_Delete)
        QTest.keyClick(workspace, Qt.Key.Key_O, Qt.KeyboardModifier.ControlModifier)
        QTest.keyClick(workspace, Qt.Key.Key_F5)
        QTest.keyClick(workspace, Qt.Key.Key_F, Qt.KeyboardModifier.ControlModifier)
        self.app.processEvents()
        self.assertEqual(opened, [True])
        self.assertEqual(removed, [True])
        self.assertEqual(imported, [True])
        self.assertEqual(refreshed, [True])
        self.assertTrue(workspace.search_input.hasFocus())
        workspace.close()

    def test_status_bar_tracks_results_filter_and_selection(self):
        workspace = DocumentsWorkspace()
        workspace.set_catalog(self.items)
        workspace.search_input.setText("alpha")
        index = workspace.filter_combo.findData("processed")
        workspace.filter_combo.setCurrentIndex(index)
        workspace.set_details(
            DocumentDetails(
                self.items[0],
                "2026-01-01",
                None,
                "native",
                False,
                None,
            )
        )
        status = workspace.summary_status_label.text()
        self.assertIn("3 documentos", status)
        self.assertIn("1 resultado", status)
        self.assertIn("Filtro: Processado", status)
        self.assertIn("Selecionado: Portaria Alpha.pdf", status)
        workspace.close()

    def test_project_scoped_state_is_restored_automatically(self):
        with TemporaryDirectory() as directory:
            project = SimpleNamespace(project_path=Path(directory))
            first = DocumentsWorkspace()
            first.on_project_opened(project)
            first.set_catalog(self.items)
            first.search_input.setText("beta")
            first.filter_combo.setCurrentIndex(
                first.filter_combo.findData("ocr_pending")
            )
            table = first.document_list_widget.list_widget
            table.sortByColumn(2, Qt.SortOrder.DescendingOrder)
            table.setColumnWidth(0, 417)
            table.setColumnWidth(1, 173)
            table.setCurrentRow(0)
            first._save_ui_state()
            selected = first.document_list_widget.current_identity()
            first.on_project_closed()
            first.close()

            restored_selections = []
            second = DocumentsWorkspace()
            second.document_selected.connect(restored_selections.append)
            second.on_project_opened(project)
            second.set_catalog(self.items)
            header = second.document_list_widget.list_widget.horizontalHeader()
            self.assertEqual(second.search_input.text(), "beta")
            self.assertEqual(
                second.filter_combo.currentData(),
                "ocr_pending",
            )
            self.assertEqual(header.sortIndicatorSection(), 2)
            self.assertIs(
                header.sortIndicatorOrder(),
                Qt.SortOrder.DescendingOrder,
            )
            self.assertEqual(
                second.document_list_widget.list_widget.columnWidth(0),
                417,
            )
            self.assertEqual(
                second.document_list_widget.current_identity(),
                selected,
            )
            self.assertEqual(restored_selections, [selected])
            second.on_project_closed()
            second.close()


if __name__ == "__main__":
    unittest.main()
