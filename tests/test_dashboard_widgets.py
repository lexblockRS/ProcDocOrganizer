import os
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication, QLabel

from ui.widgets.dashboard_widgets import (
    DashboardHeader,
    DashboardSection,
    ResponsiveCardGrid,
    ShortcutButton,
    SummaryCard,
)


class DashboardWidgetTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_summary_card_renders_and_updates_value(self):
        card = SummaryCard("Documentos", 3)
        self.assertEqual(card.title_label.text(), "Documentos")
        self.assertEqual(card.value_label.text(), "3")

        card.set_value(8)

        self.assertEqual(card.value_label.text(), "8")

    def test_header_renders_only_received_values(self):
        header = DashboardHeader()
        header.set_values(
            project_name="Projeto",
            application_name="RSC",
            project_path="C:/projeto.pdop",
            created_at="2026-01-01",
            last_opened_at="2026-01-02",
        )

        self.assertEqual(header.project_name_label.text(), "Projeto")
        self.assertIn("RSC", header.application_label.text())
        self.assertIn("C:/projeto.pdop", header.path_label.text())
        self.assertEqual(
            header.path_label.toolTip(), "C:/projeto.pdop"
        )

    def test_section_owns_title_and_received_content(self):
        content = QLabel("Conteúdo")
        section = DashboardSection("Resumo", content)

        self.assertEqual(section.title_label.text(), "Resumo")
        self.assertIs(content.parent(), section)

    def test_shortcut_has_accessibility_metadata(self):
        button = ShortcutButton("Pesquisa", "Pesquisar documentos")

        self.assertEqual(button.accessibleName(), "Pesquisa")
        self.assertEqual(button.toolTip(), "Pesquisar documentos")

    def test_card_grid_reflows_without_fixed_coordinates(self):
        grid = ResponsiveCardGrid()
        cards = [SummaryCard(str(index)) for index in range(4)]
        grid.resize(170, 300)
        grid.set_cards(cards)
        self.assertEqual(grid._columns, 1)

        grid.resize(500, 300)
        grid._relayout()
        self.assertGreaterEqual(grid._columns, 2)

    def test_card_grid_preserves_order_at_representative_widths(self):
        grid = ResponsiveCardGrid()
        cards = [SummaryCard(str(index)) for index in range(6)]
        grid.set_cards(cards)

        column_counts = []
        for width in (140, 360, 760):
            grid.resize(width, 300)
            grid._relayout(force=True)
            column_counts.append(grid._columns)
            arranged = [
                grid._layout.itemAt(index).widget()
                for index in range(grid._layout.count())
            ]
            self.assertEqual(arranged, cards)

        self.assertLess(column_counts[0], column_counts[1])
        self.assertLess(column_counts[1], column_counts[2])

    def test_hidden_cards_are_removed_without_deletion(self):
        grid = ResponsiveCardGrid()
        first = SummaryCard("Primeiro")
        hidden = SummaryCard("Oculto")
        last = SummaryCard("Último")
        grid.set_cards((first, hidden, last))

        grid.set_card_visible(hidden, False)

        arranged = [
            grid._layout.itemAt(index).widget()
            for index in range(grid._layout.count())
        ]
        self.assertEqual(arranged, [first, last])
        self.assertIn(hidden, grid._cards)


if __name__ == "__main__":
    unittest.main()
