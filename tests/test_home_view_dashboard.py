import os
from types import SimpleNamespace
import unittest
from unittest.mock import Mock

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt

from presentation.dashboard import (
    DashboardProjection,
    DashboardState,
    DocumentSummaryProjection,
    EvidenceSummaryProjection,
    ProjectSummaryProjection,
)
from ui.views.home_view import HomeView


def project_summary():
    return ProjectSummaryProjection(
        project_name="Projeto",
        project_path="C:/projeto.pdop",
        application_id="rsc",
        application_name="RSC",
        created_at="2026-01-01T10:00:00",
        last_opened_at="2026-01-02T10:00:00",
    )


def ready_projection():
    return DashboardProjection(
        state=DashboardState.READY,
        project=project_summary(),
        documents=DocumentSummaryProjection(
            total_documents=7,
            processed_documents=4,
            pending_documents=1,
            ocr_required_documents=1,
            failed_documents=1,
            processed_pages=28,
        ),
        evidences=EvidenceSummaryProjection(total_evidences=3),
    )


def application_session():
    return SimpleNamespace(
        rsc_session=SimpleNamespace(
            list_functional_assignment_evidences_service=(
                SimpleNamespace(execute=lambda: (object(), object()))
            ),
            list_functional_exercises_service=(
                SimpleNamespace(execute=lambda: (object(),))
            ),
        )
    )


class HomeViewDashboardTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.view = HomeView()

    def tearDown(self):
        self.view.close()

    def test_no_project_shows_empty_state_and_actions(self):
        self.assertIs(
            self.view.state_stack.currentWidget(),
            self.view.no_project_page,
        )
        self.assertEqual(
            self.view.new_project_button.text(), "Novo Projeto"
        )
        self.assertEqual(
            self.view.open_project_button.text(), "Abrir Projeto"
        )

    def test_loading_shows_project_name(self):
        self.view.set_projection(DashboardProjection(
            state=DashboardState.LOADING,
            project=project_summary(),
        ))

        self.assertIs(
            self.view.state_stack.currentWidget(),
            self.view.loading_page,
        )
        self.assertIn("Projeto", self.view.loading_label.text())

    def test_ready_renders_header_and_all_document_indicators(self):
        self.view.set_projection(ready_projection())

        self.assertIs(
            self.view.state_stack.currentWidget(),
            self.view.ready_page,
        )
        self.assertEqual(
            self.view.dashboard_header.project_name_label.text(),
            "Projeto",
        )
        expected = {
            "total": "7",
            "processed": "4",
            "pending": "1",
            "ocr": "1",
            "failed": "1",
            "pages": "28",
        }
        for key, value in expected.items():
            with self.subTest(card=key):
                self.assertEqual(
                    self.view.document_cards[key].value_label.text(),
                    value,
                )
        self.assertEqual(
            self.view.evidence_total_card.value_label.text(), "3"
        )

    def test_rsc_section_is_hidden_when_unavailable(self):
        self.view.refresh_dashboard_contributions(None)
        self.view.set_projection(ready_projection())

        self.assertTrue(self.view.rsc_section.isHidden())
        self.assertTrue(
            self.view.summary_cards["assignments"].isHidden()
        )
        self.assertTrue(
            self.view.summary_cards["exercises"].isHidden()
        )
        self.assertEqual(
            self.view.summary_grid._layout.indexOf(
                self.view.summary_cards["assignments"]
            ),
            -1,
        )

    def test_rsc_section_is_rendered_when_available(self):
        self.view.refresh_dashboard_contributions(application_session())
        self.view.set_projection(ready_projection())

        self.assertFalse(self.view.rsc_section.isHidden())
        self.assertEqual(
            self.view.rsc_cards["assignments"].value_label.text(),
            "2",
        )
        self.assertEqual(
            self.view.rsc_cards["exercises"].value_label.text(),
            "1",
        )

    def test_rsc_section_returns_after_projection_alternation(self):
        self.view.refresh_dashboard_contributions(application_session())
        self.view.set_projection(ready_projection())
        self.view.refresh_dashboard_contributions(None)
        self.view.refresh_dashboard_contributions(application_session())
        self.view.set_projection(ready_projection())

        self.assertFalse(self.view.rsc_section.isHidden())
        self.assertGreaterEqual(
            self.view.summary_grid._layout.indexOf(
                self.view.summary_cards["assignments"]
            ),
            0,
        )

    def test_error_shows_message_and_retry(self):
        self.view.set_projection(DashboardProjection(
            state=DashboardState.ERROR,
            project=project_summary(),
            error_message="Não foi possível carregar o resumo.",
        ))

        self.assertIs(
            self.view.state_stack.currentWidget(),
            self.view.error_page,
        )
        self.assertIn(
            "Não foi possível carregar",
            self.view.error_message_label.text(),
        )
        self.assertEqual(
            self.view.retry_button.text(), "Tentar novamente"
        )

    def test_shortcuts_emit_neutral_signals(self):
        checks = (
            ("documents", self.view.documents_requested),
            ("search", self.view.search_requested),
            ("evidences", self.view.evidences_requested),
            ("import", self.view.import_documents_requested),
            ("process", self.view.process_documents_requested),
        )
        for key, signal in checks:
            callback = Mock()
            signal.connect(callback)
            self.view.shortcut_buttons[key].click()
            with self.subTest(shortcut=key):
                callback.assert_called_once_with()

    def test_shortcuts_keep_logical_order_and_accessibility(self):
        self.assertEqual(
            list(self.view.shortcut_buttons),
            ["documents", "search", "evidences", "import", "process"],
        )
        for button in self.view.shortcut_buttons.values():
            self.assertTrue(button.toolTip())
            self.assertTrue(button.accessibleName())

    def test_empty_state_actions_emit_neutral_signals(self):
        new_callback = Mock()
        open_callback = Mock()
        self.view.new_project_requested.connect(new_callback)
        self.view.open_project_requested.connect(open_callback)

        self.view.new_project_button.click()
        self.view.open_project_button.click()

        new_callback.assert_called_once_with()
        open_callback.assert_called_once_with()

    def test_retry_emits_refresh_intention(self):
        callback = Mock()
        self.view.retry_requested.connect(callback)

        self.view.retry_button.click()

        callback.assert_called_once_with()

    def test_no_project_projection_clears_ready_state(self):
        self.view.set_projection(ready_projection())
        self.view.set_projection(DashboardProjection())

        self.assertIs(
            self.view.state_stack.currentWidget(),
            self.view.no_project_page,
        )

    def test_ready_has_no_horizontal_scrollbar(self):
        self.assertEqual(
            self.view.ready_scroll.horizontalScrollBarPolicy(),
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff,
        )

    def test_header_preserves_full_path_in_tooltip(self):
        self.view.set_projection(ready_projection())

        self.assertEqual(
            self.view.dashboard_header.path_label.toolTip(),
            "C:/projeto.pdop",
        )


if __name__ == "__main__":
    unittest.main()
