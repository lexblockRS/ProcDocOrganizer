import os
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

from presentation.activities import (
    ActivitiesProjection,
    ActivitiesViewState,
    ActivityDetailsProjection,
    ActivityListItemProjection,
)
from ui.views import ActivitiesView


def ready_projection(selected="a"):
    items = tuple(
        ActivityListItemProjection(
            activity_id=identifier,
            description=description,
            state="lembrada",
            state_label="Lembrada",
            evidence_count=index,
            exercise_count=index,
            is_selected=identifier == selected,
        )
        for index, (identifier, description) in enumerate(
            (("a", "Fiscalização"), ("b", "Coordenação"))
        )
    )
    selected_item = next(
        item for item in items if item.activity_id == selected
    )
    return ActivitiesProjection(
        state=ActivitiesViewState.READY,
        project_name="Projeto",
        items=items,
        selected_activity_id=selected,
        selected_activity=ActivityDetailsProjection(
            activity_id=selected_item.activity_id,
            description=selected_item.description,
            state=selected_item.state,
            state_label=selected_item.state_label,
            evidence_ids=("evidence-1",),
            exercise_ids=("exercise-1",),
            evidence_count=1,
            exercise_count=1,
            state_options=(
                ("lembrada", "Lembrada"),
                ("em_investigacao", "Em investigação"),
            ),
        ),
        total=2,
        remembered_count=2,
    )


class ActivitiesViewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.view = ActivitiesView()

    def tearDown(self):
        self.view.close()

    def test_state_pages(self):
        cases = (
            (ActivitiesViewState.NO_PROJECT, self.view.no_project_page),
            (ActivitiesViewState.LOADING, self.view.loading_page),
            (ActivitiesViewState.EMPTY, self.view.empty_page),
            (ActivitiesViewState.ERROR, self.view.error_page),
        )
        for state, page in cases:
            with self.subTest(state=state):
                self.view.set_projection(ActivitiesProjection(
                    state=state,
                    project_name="Projeto",
                    error_message="Falha",
                ))
                self.assertIs(
                    self.view.state_stack.currentWidget(), page
                )

    def test_empty_creation_button_is_available(self):
        self.view.set_projection(ActivitiesProjection(
            state=ActivitiesViewState.EMPTY
        ))
        self.assertTrue(self.view.new_activity_button.isEnabled())
        self.assertEqual(
            self.view.new_activity_button.toolTip(),
            "Criar uma Activity",
        )

    def test_ready_renders_list_totals_and_details(self):
        self.view.set_projection(ready_projection())

        self.assertEqual(self.view.activity_list.count(), 2)
        self.assertEqual(self.view.total_label.text(), "2 atividade(s)")
        self.assertEqual(
            self.view.summary_cards["remembered"].value_label.text(),
            "2",
        )
        self.assertEqual(
            self.view.details_description_label.text(), "Fiscalização"
        )
        self.assertIn(
            "evidence-1", self.view.evidence_ids_label.text()
        )

    def test_selection_emits_identifier(self):
        received = []
        self.view.activity_selected.connect(received.append)
        self.view.set_projection(ready_projection())

        self.view.activity_list.setCurrentRow(1)

        self.assertEqual(received, ["b"])

    def test_inspector_edits_description_and_state_and_can_cancel(self):
        self.view.set_projection(ready_projection())
        saved = []
        self.view.save_requested.connect(
            lambda description, state: saved.append(
                (description, state)
            )
        )

        self.view.edit_action.trigger()
        self.assertTrue(self.view.is_editing)
        self.view.description_editor.setText("Nova descrição")
        self.view.state_editor.setCurrentIndex(1)
        self.assertTrue(self.view.has_unsaved_changes)
        self.view.save_button.click()
        self.assertEqual(
            saved,
            [("Nova descrição", "em_investigacao")],
        )

        self.view.cancel_edit()
        self.assertFalse(self.view.is_editing)
        self.assertEqual(
            self.view.description_editor.text(),
            "Fiscalização",
        )
        self.assertEqual(
            self.view.state_editor.currentData(),
            "lembrada",
        )

    def test_buttons_emit_neutral_signals(self):
        counts = {"open": 0, "refresh": 0, "retry": 0}
        self.view.open_project_requested.connect(
            lambda: counts.__setitem__("open", counts["open"] + 1)
        )
        self.view.refresh_requested.connect(
            lambda: counts.__setitem__(
                "refresh", counts["refresh"] + 1
            )
        )
        self.view.retry_requested.connect(
            lambda: counts.__setitem__("retry", counts["retry"] + 1)
        )
        self.view.open_project_button.click()
        self.view.refresh_button.click()
        self.view.retry_button.click()
        self.assertEqual(counts, {"open": 1, "refresh": 1, "retry": 1})

    def test_accessibility_and_horizontal_scroll(self):
        self.assertTrue(self.view.activity_list.accessibleName())
        self.assertTrue(self.view.refresh_button.accessibleName())
        self.assertTrue(self.view.retry_button.accessibleName())
        self.assertEqual(
            self.view.activity_list.horizontalScrollBarPolicy(),
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff,
        )


if __name__ == "__main__":
    unittest.main()
