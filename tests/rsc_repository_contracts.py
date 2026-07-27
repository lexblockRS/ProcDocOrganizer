"""Contratos reutilizáveis para implementations de repositories RSC."""

from dataclasses import FrozenInstanceError, replace

from applications.rsc.models import (
    FunctionalAssignmentEvidenceId,
    FunctionalExerciseId,
)
from applications.rsc.ports import (
    DuplicateFunctionalAssignmentEvidenceError,
)


class FunctionalAssignmentEvidenceRepositoryContract:
    """Especificação aplicável a qualquer repository de atribuições."""

    def make_assignment_repository(self):
        raise NotImplementedError

    def make_assignment(self, index):
        raise NotImplementedError

    def test_contract_assignment_repository_starts_empty(self):
        repository = self.make_assignment_repository()

        self.assertEqual(repository.list_all(), ())

    def test_contract_assignment_save_and_get_round_trip(self):
        repository = self.make_assignment_repository()
        evidence = self.make_assignment(1)

        stored = repository.save(evidence)

        self.assertEqual(stored, evidence)
        self.assertEqual(repository.get_by_id(evidence.id), evidence)

    def test_contract_assignment_save_stores_entity(self):
        repository = self.make_assignment_repository()
        evidence = self.make_assignment(1)

        repository.save(evidence)

        self.assertEqual(repository.list_all(), (evidence,))

    def test_contract_assignment_missing_id_returns_none(self):
        repository = self.make_assignment_repository()

        self.assertIsNone(
            repository.get_by_id(
                FunctionalAssignmentEvidenceId(
                    "99999999-9999-4999-8999-999999999999"
                )
            )
        )

    def test_contract_assignment_list_returns_all_in_insertion_order(self):
        repository = self.make_assignment_repository()
        first = self.make_assignment(1)
        second = self.make_assignment(2)

        repository.save(first)
        repository.save(second)

        self.assertEqual(repository.list_all(), (first, second))

    def test_contract_assignment_list_returns_every_saved_entity(self):
        repository = self.make_assignment_repository()
        items = tuple(self.make_assignment(index) for index in (1, 2, 3))

        for item in items:
            repository.save(item)

        self.assertEqual(set(repository.list_all()), set(items))

    def test_contract_assignment_duplicate_uses_stable_error(self):
        repository = self.make_assignment_repository()
        original = self.make_assignment(1)
        repository.save(original)

        with self.assertRaises(
            DuplicateFunctionalAssignmentEvidenceError
        ):
            repository.save(replace(original, role="Outro papel"))

    def test_contract_assignment_duplicate_preserves_original(self):
        repository = self.make_assignment_repository()
        original = self.make_assignment(1)
        repository.save(original)

        with self.assertRaises(
            DuplicateFunctionalAssignmentEvidenceError
        ):
            repository.save(replace(original, role="Outro papel"))

        self.assertEqual(repository.list_all(), (original,))

    def test_contract_assignment_repository_instances_are_isolated(self):
        first_repository = self.make_assignment_repository()
        second_repository = self.make_assignment_repository()
        evidence = self.make_assignment(1)

        first_repository.save(evidence)

        self.assertEqual(first_repository.list_all(), (evidence,))
        self.assertEqual(second_repository.list_all(), ())

    def test_contract_assignment_result_cannot_mutate_stored_state(self):
        repository = self.make_assignment_repository()
        evidence = self.make_assignment(1)
        stored = repository.save(evidence)

        with self.assertRaises(FrozenInstanceError):
            stored.role = "Outro papel"

        self.assertEqual(repository.get_by_id(evidence.id), evidence)


class FunctionalExerciseRepositoryContract:
    """Especificação aplicável a qualquer repository de exercícios."""

    def make_exercise_repository(self):
        raise NotImplementedError

    def make_exercise(self, index, assignment_indexes=(1,)):
        raise NotImplementedError

    def test_contract_exercise_repository_starts_empty(self):
        repository = self.make_exercise_repository()

        self.assertEqual(repository.list_all(), ())

    def test_contract_exercise_save_and_get_round_trip(self):
        repository = self.make_exercise_repository()
        exercise = self.make_exercise(1)

        repository.save(exercise)

        self.assertEqual(repository.get_by_id(exercise.id), exercise)

    def test_contract_exercise_save_stores_entity(self):
        repository = self.make_exercise_repository()
        exercise = self.make_exercise(1)

        repository.save(exercise)

        self.assertEqual(repository.list_all(), (exercise,))

    def test_contract_exercise_missing_id_returns_none(self):
        repository = self.make_exercise_repository()

        self.assertIsNone(
            repository.get_by_id(
                FunctionalExerciseId(
                    "88888888-8888-4888-8888-888888888888"
                )
            )
        )

    def test_contract_exercise_list_returns_all_in_insertion_order(self):
        repository = self.make_exercise_repository()
        first = self.make_exercise(1)
        second = self.make_exercise(2)

        repository.save(first)
        repository.save(second)

        self.assertEqual(repository.list_all(), (first, second))

    def test_contract_exercise_list_returns_every_saved_entity(self):
        repository = self.make_exercise_repository()
        items = tuple(self.make_exercise(index) for index in (1, 2, 3))

        for item in items:
            repository.save(item)

        self.assertEqual(set(repository.list_all()), set(items))

    def test_contract_exercise_existing_id_is_upserted_in_place(self):
        repository = self.make_exercise_repository()
        original = self.make_exercise(1)
        second = self.make_exercise(2)
        replacement = replace(original, person_id="replacement")
        repository.save(original)
        repository.save(second)

        repository.save(replacement)

        self.assertEqual(
            repository.list_all(),
            (replacement, second),
        )

    def test_contract_exercise_provenance_order_survives_round_trip(self):
        repository = self.make_exercise_repository()
        exercise = self.make_exercise(
            1,
            assignment_indexes=(3, 1, 2),
        )

        repository.save(exercise)
        restored = repository.get_by_id(exercise.id)

        self.assertEqual(
            restored.functional_assignment_evidence_ids,
            exercise.functional_assignment_evidence_ids,
        )

    def test_contract_exercise_repository_instances_are_isolated(self):
        first_repository = self.make_exercise_repository()
        second_repository = self.make_exercise_repository()
        exercise = self.make_exercise(1)

        first_repository.save(exercise)

        self.assertEqual(first_repository.list_all(), (exercise,))
        self.assertEqual(second_repository.list_all(), ())

    def test_contract_exercise_retrieved_model_equals_persisted_model(self):
        repository = self.make_exercise_repository()
        exercise = self.make_exercise(1)

        repository.save(exercise)

        self.assertEqual(repository.get_by_id(exercise.id), exercise)
