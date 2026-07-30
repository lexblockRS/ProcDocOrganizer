from dataclasses import FrozenInstanceError, replace
from types import SimpleNamespace
import unittest

from applications.rsc.models import (
    Activity,
    ActivityState,
    FunctionalAssignmentEvidenceId,
    FunctionalExerciseId,
)
from applications.rsc.repositories import InMemoryActivityRepository
from presentation.activities import (
    ActivitiesController,
    ActivitiesProjection,
    ActivitiesService,
    ActivitiesViewState,
)


EVIDENCE_ID = FunctionalAssignmentEvidenceId(
    "11111111-1111-4111-8111-111111111111"
)
EXERCISE_ID = FunctionalExerciseId(
    "22222222-2222-4222-8222-222222222222"
)


class SignalStub:
    def __init__(self):
        self.callback = None

    def connect(self, callback):
        self.callback = callback


class ViewSpy:
    def __init__(self):
        self.refresh_requested = SignalStub()
        self.retry_requested = SignalStub()
        self.activity_selected = SignalStub()
        self.projections = []

    def set_projection(self, projection):
        self.projections.append(projection)


class ActivitiesPresentationTests(unittest.TestCase):
    def setUp(self):
        self.repository = InMemoryActivityRepository()

    def test_projection_is_immutable(self):
        projection = ActivitiesProjection()
        with self.assertRaises(FrozenInstanceError):
            projection.total = 1

    def test_empty_repository_builds_empty_projection(self):
        result = ActivitiesService(
            self.repository, "Projeto"
        ).build()
        self.assertEqual(result.state, ActivitiesViewState.EMPTY)
        self.assertEqual(result.total, 0)

    def test_service_preserves_order_counts_relations_and_selects_first(self):
        items = (
            Activity("a", "Lembrada"),
            Activity(
                "b",
                "Comprovada",
                ActivityState.PROVEN,
                (EVIDENCE_ID,),
                (EXERCISE_ID,),
            ),
        )
        for item in items:
            self.repository.save(item)

        result = ActivitiesService(
            self.repository, "Projeto"
        ).build()

        self.assertEqual(
            tuple(item.activity_id for item in result.items),
            ("a", "b"),
        )
        self.assertEqual(result.selected_activity_id, "a")
        self.assertEqual(result.remembered_count, 1)
        self.assertEqual(result.proven_count, 1)
        self.assertEqual(result.items[1].state_label, "Comprovada")
        self.assertEqual(result.items[1].evidence_count, 1)
        self.assertEqual(result.items[1].exercise_count, 1)
        self.assertEqual(
            result.selected_activity.state_options,
            (
                ("lembrada", "Lembrada"),
                ("em_investigacao", "Em investigação"),
                (
                    "parcialmente_comprovada",
                    "Parcialmente comprovada",
                ),
                ("comprovada", "Comprovada"),
            ),
        )

    def test_valid_selection_is_preserved_and_invalid_selects_first(self):
        self.repository.save(Activity("a", "Primeira"))
        self.repository.save(Activity("b", "Segunda"))
        service = ActivitiesService(self.repository, "Projeto")

        self.assertEqual(service.build("b").selected_activity_id, "b")
        self.assertEqual(
            service.build("inexistente").selected_activity_id, "a"
        )

    def test_all_state_labels_and_totals(self):
        activities = (
            Activity("a", "A"),
            Activity(
                "b", "B", ActivityState.UNDER_INVESTIGATION
            ),
            Activity(
                "c",
                "C",
                ActivityState.PARTIALLY_PROVEN,
                (EVIDENCE_ID,),
            ),
            Activity(
                "d",
                "D",
                ActivityState.PROVEN,
                (EVIDENCE_ID,),
                (EXERCISE_ID,),
            ),
        )
        for item in activities:
            self.repository.save(item)

        result = ActivitiesService(
            self.repository, "Projeto"
        ).build()

        self.assertEqual(
            tuple(item.state_label for item in result.items),
            (
                "Lembrada",
                "Em investigação",
                "Parcialmente comprovada",
                "Comprovada",
            ),
        )
        self.assertEqual(
            (
                result.remembered_count,
                result.investigating_count,
                result.partially_proven_count,
                result.proven_count,
            ),
            (1, 1, 1, 1),
        )

    def test_controller_lifecycle_loading_selection_refresh_and_close(self):
        self.repository.save(Activity("a", "Primeira"))
        self.repository.save(Activity("b", "Segunda"))
        view = ViewSpy()
        controller = ActivitiesController(view)
        session = SimpleNamespace(
            project=SimpleNamespace(project_name="Projeto"),
            rsc_session=SimpleNamespace(
                activity_repository=self.repository
            ),
        )

        controller.set_session(session)
        controller.select_activity("b")
        controller.refresh()
        controller.clear_session()

        states = tuple(item.state for item in view.projections)
        self.assertIn(ActivitiesViewState.LOADING, states)
        self.assertIn(ActivitiesViewState.READY, states)
        self.assertEqual(
            view.projections[-2].selected_activity_id, "b"
        )
        self.assertEqual(
            view.projections[-1].state,
            ActivitiesViewState.NO_PROJECT,
        )

    def test_controller_controls_read_error_and_retry(self):
        class FailingRepository:
            def list_all(self):
                raise RuntimeError("internal")

        view = ViewSpy()
        controller = ActivitiesController(view)
        controller.set_session(SimpleNamespace(
            project=SimpleNamespace(project_name="Projeto"),
            rsc_session=SimpleNamespace(
                activity_repository=FailingRepository()
            ),
        ))

        self.assertEqual(
            view.projections[-1].state, ActivitiesViewState.ERROR
        )
        self.assertNotIn("internal", view.projections[-1].error_message)
        self.assertFalse(view.retry_requested.callback())


if __name__ == "__main__":
    unittest.main()
