import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import unittest
from dataclasses import replace

from PySide6.QtCore import Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication

from models import (
    DocumentAvailability, DocumentDetails, DocumentPageSummary, DocumentSummary,
)
from ui.widgets import (
    DocumentListWidget, DocumentMetadataWidget, DocumentPageListWidget,
    DocumentTextWidget,
)


SHA = "a" * 64


def summary(identity=SHA, name="Portaria.pdf", pages=3, status="processed"):
    return DocumentSummary(
        identity, SHA if identity == SHA else "", name,
        "documents/Meu  Documento.pdf", "portaria", "2026-01-01", pages,
        status, DocumentAvailability.AVAILABLE, status == "processed",
        imported_at="2026-01-01",
    )


def details(processed=True):
    item = summary(status="processed" if processed else "not_processed")
    return DocumentDetails(
        item, "2026-01-01", "2026-01-02" if processed else None,
        "mixed" if processed else None, processed, None, {}, item.page_count,
        processed,
    )


def page(number=1, text="Linha  um\nLinha dois"):
    return DocumentPageSummary(SHA, SHA, number, text, "native", len(text))


class DocumentWidgetTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_catalog_content_hides_technical_fields_and_emits_selection(self):
        widget = DocumentListWidget()
        selected = []
        widget.document_selected.connect(selected.append)
        widget.set_catalog((summary(),))
        row = widget.list_widget.item(0)
        self.assertEqual(
            [row.text(column) for column in range(3)],
            ["Portaria.pdf", "portaria", "2026-01-01"],
        )
        visible_text = " ".join(
            row.text(column) for column in range(3)
        )
        self.assertNotIn(SHA, visible_text)
        self.assertNotIn("documents/", visible_text)
        self.assertNotIn("páginas", visible_text)
        self.assertNotIn("Processado", visible_text)
        widget.list_widget.setCurrentRow(0)
        self.assertEqual(selected, [SHA])
        widget.close()

    def test_catalog_keyboard_navigation_and_removed_selection(self):
        widget = DocumentListWidget()
        items = (summary(SHA, "A.pdf"), summary("documents/B.pdf", "B.pdf"))
        widget.set_catalog(items)
        widget.list_widget.setCurrentRow(0)
        widget.list_widget.setFocus()
        QTest.keyClick(widget.list_widget, Qt.Key.Key_Down)
        self.assertEqual(widget.current_identity(), "documents/B.pdf")
        widget.set_catalog((items[0],))
        self.assertIsNone(widget.current_identity())
        widget.close()

    def test_catalog_uses_qt_sorting_for_all_visible_columns(self):
        widget = DocumentListWidget()
        items = (
            replace(
                summary("documents/B.pdf", "B.pdf"),
                document_type="ofício",
                imported_at="2026-02-01",
            ),
            replace(
                summary(SHA, "A.pdf"),
                document_type="portaria",
                imported_at="2026-01-01",
            ),
        )
        widget.set_catalog(items)
        tree = widget.list_widget
        tree.sortItems(0, Qt.SortOrder.AscendingOrder)
        self.assertEqual(tree.item(0).text(0), "A.pdf")
        tree.sortItems(1, Qt.SortOrder.AscendingOrder)
        self.assertEqual(tree.item(0).text(1), "ofício")
        tree.sortItems(2, Qt.SortOrder.DescendingOrder)
        self.assertEqual(tree.item(0).text(2), "2026-02-01")
        widget.close()

    def test_metadata_values_missing_fields_unprocessed_and_clear(self):
        widget = DocumentMetadataWidget()
        widget.set_details(details())
        self.assertEqual(widget.values["name"].text(), "Portaria.pdf")
        self.assertEqual(
            widget.values["path"].text(),
            "documents/Meu  Documento.pdf",
        )
        self.assertEqual(widget.values["hash"].text(), SHA)
        self.assertEqual(widget.values["imported"].text(), "2026-01-01")
        self.assertEqual(widget.values["ocr"].text(), "Sim")
        self.assertEqual(widget.values["source"].text(), "mixed")
        widget.set_details(details(False))
        widget.show_unprocessed()
        self.assertIn("ainda não foi processado", widget.values["status"].text())
        self.assertEqual(widget.values["name"].text(), "Portaria.pdf")
        self.assertEqual(widget.values["processed"].text(), "Não informado")
        widget.clear()
        self.assertEqual(widget.values["name"].text(), "Não informado")
        widget.close()

    def test_page_list_preserves_real_nonsequential_numbers_and_clears(self):
        widget = DocumentPageListWidget()
        selected = []
        widget.page_selected.connect(selected.append)
        widget.set_pages((page(1), page(4)))
        self.assertEqual(widget.list_widget.item(0).text(), "Página 1")
        self.assertEqual(widget.list_widget.item(1).text(), "Página 4")
        widget.list_widget.setCurrentRow(1)
        self.assertEqual(selected, [4])
        widget.clear()
        self.assertEqual(widget.list_widget.count(), 0)
        self.assertTrue(widget.empty_label.isVisibleTo(widget))
        widget.close()

    def test_text_is_read_only_copyable_exact_and_empty_friendly(self):
        widget = DocumentTextWidget()
        text = "Linha  um\n  Linha dois\n"
        widget.set_page(page(7, text))
        self.assertTrue(widget.text_edit.isReadOnly())
        self.assertEqual(widget.text_edit.toPlainText(), text)
        widget.text_edit.selectAll()
        widget.text_edit.copy()
        self.assertEqual(QApplication.clipboard().text(), text)
        widget.set_page(page(8, ""))
        self.assertIn("Nenhum texto", widget.message_label.text())
        widget.clear()
        self.assertEqual(widget.text_edit.toPlainText(), "")
        widget.close()


if __name__ == "__main__":
    unittest.main()
