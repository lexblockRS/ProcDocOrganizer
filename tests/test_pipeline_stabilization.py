import os
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

from applications.rsc.models import (
    Activity,
    FunctionalAssignmentEvidenceId,
    FunctionalExerciseId,
)
from applications.rsc.repositories import InMemoryActivityRepository
from presentation.activities import ActivitiesService
from ui.views import ActivitiesView


class MissingRepository:
    def get_by_id(self, _identifier):
        return None


class PipelineStabilizationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_unavailable_historical_relations_are_not_omitted(self):
        exercise_id = FunctionalExerciseId(
            "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"
        )
        assignment_id = FunctionalAssignmentEvidenceId(
            "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb"
        )
        repository = InMemoryActivityRepository()
        repository.save(Activity(
            activity_id="activity-1",
            description="Histórica",
            functional_assignment_evidence_ids=(assignment_id,),
            functional_exercise_ids=(exercise_id,),
        ))

        details = ActivitiesService(
            repository,
            "Projeto",
            MissingRepository(),
            MissingRepository(),
        ).build().selected_activity

        self.assertEqual(
            details.related_exercises[0].exercise_id, str(exercise_id)
        )
        self.assertFalse(details.related_exercises[0].available)
        self.assertEqual(
            details.related_interpretations[0].assignment_id,
            str(assignment_id),
        )
        self.assertFalse(
            details.related_interpretations[0].assignment_available
        )

        view = ActivitiesView()
        self.addCleanup(view.close)
        view.set_projection(ActivitiesService(
            repository,
            "Projeto",
            MissingRepository(),
            MissingRepository(),
        ).build())
        exercise_row = view.exercise_list.item(0)
        assignment_row = view.related_list.item(0)
        self.assertIn(str(exercise_id), exercise_row.text())
        self.assertIn("indisponível", exercise_row.text().lower())
        self.assertIn(str(assignment_id), assignment_row.text())
        self.assertIn("indisponível", assignment_row.text().lower())
        view.exercise_list.setCurrentItem(exercise_row)
        view.related_list.setCurrentItem(assignment_row)
        self.assertFalse(view.open_exercise_button.isEnabled())
        self.assertFalse(view.open_assignment_button.isEnabled())


if __name__ == "__main__":
    unittest.main()
