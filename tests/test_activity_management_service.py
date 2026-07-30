import unittest
from unittest.mock import Mock

from applications.rsc.models import (
    Activity,
    ActivityState,
    FunctionalContext,
    FunctionalExercise,
    FunctionalExerciseId,
    FunctionalExerciseStatus,
    FunctionalExerciseType,
    FunctionalPeriod,
    FunctionalRole,
)
from applications.rsc.repositories import (
    InMemoryFunctionalExerciseRepository,
)
from datetime import date
from uuid import uuid4
from applications.rsc.services import (
    ActivityManagementError,
    ActivityManagementService,
)


class ActivityManagementServiceTests(unittest.TestCase):
    def setUp(self):
        self.repository = Mock()
        self.service = ActivityManagementService(self.repository)

    def test_create_uses_only_consolidated_initial_attributes(self):
        created = self.service.create("  Coordenação   acadêmica  ")
        self.assertTrue(created.activity_id)
        self.assertEqual(created.description, "Coordenação acadêmica")
        self.assertIs(created.state, ActivityState.REMEMBERED)
        self.assertEqual(
            created.functional_assignment_evidence_ids,
            (),
        )
        self.assertEqual(created.functional_exercise_ids, ())
        self.repository.add.assert_called_once_with(created)

    def test_update_preserves_identity_state_and_empty_relations(self):
        original = Activity("activity-1", "Descrição inicial")
        self.repository.get.return_value = original
        updated = self.service.update_description(
            original.activity_id,
            "Descrição atualizada",
        )
        self.assertEqual(updated.activity_id, original.activity_id)
        self.assertIs(updated.state, original.state)
        self.assertEqual(updated.functional_assignment_evidence_ids, ())
        self.assertEqual(updated.functional_exercise_ids, ())
        self.repository.save.assert_called_once_with(updated)

    def test_update_advances_only_through_aggregate_transition(self):
        original = Activity("activity-1", "Descrição inicial")
        self.repository.get.return_value = original

        updated = self.service.update(
            original.activity_id,
            "Descrição investigada",
            ActivityState.UNDER_INVESTIGATION.value,
        )

        self.assertEqual(updated.description, "Descrição investigada")
        self.assertIs(updated.state, ActivityState.UNDER_INVESTIGATION)
        self.repository.save.assert_called_once_with(updated)

    def test_update_rejects_state_jump_before_persistence(self):
        original = Activity("activity-1", "Descrição inicial")
        self.repository.get.return_value = original

        with self.assertRaisesRegex(
            ActivityManagementError,
            "ciclo sequencial",
        ):
            self.service.update(
                original.activity_id,
                original.description,
                ActivityState.PROVEN,
            )

        self.repository.save.assert_not_called()

    def test_empty_description_and_missing_activity_are_rejected(self):
        with self.assertRaisesRegex(
            ActivityManagementError,
            "não pode ser vazio",
        ):
            self.service.create(" ")
        self.repository.add.assert_not_called()

        self.repository.get.return_value = None
        with self.assertRaisesRegex(
            ActivityManagementError,
            "não foi localizada",
        ):
            self.service.update_description("missing", "Descrição")

    def test_delete_delegates_to_repository(self):
        activity = Activity("activity-1", "Descrição")
        self.repository.delete.return_value = activity
        self.assertIs(self.service.delete(activity.activity_id), activity)
        self.repository.delete.assert_called_once_with(activity.activity_id)

    def test_production_creation_requires_unique_existing_exercises(self):
        exercises = InMemoryFunctionalExerciseRepository()
        exercise = FunctionalExercise(
            id=FunctionalExerciseId(str(uuid4())),
            person_id="person-1",
            exercise_type=FunctionalExerciseType("gestao", "Gestão"),
            role=FunctionalRole("Coordenador"),
            context=FunctionalContext("Universidade"),
            period=FunctionalPeriod(date(2024, 1, 1)),
            status=FunctionalExerciseStatus.ACTIVE,
        )
        exercises.save(exercise)
        service = ActivityManagementService(self.repository, exercises)

        created = service.create(
            "Fato funcional consolidado",
            (str(exercise.id),),
        )
        self.assertEqual(
            created.functional_exercise_ids,
            (exercise.id,),
        )
        with self.assertRaisesRegex(
            ActivityManagementError,
            "ao menos um",
        ):
            service.create("Sem exercício", ())
        with self.assertRaisesRegex(
            ActivityManagementError,
            "não podem se repetir",
        ):
            service.create(
                "Duplicada",
                (str(exercise.id), str(exercise.id)),
            )


if __name__ == "__main__":
    unittest.main()
