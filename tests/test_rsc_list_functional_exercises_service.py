from dataclasses import fields
from datetime import date
import unittest

from applications.rsc.assemblers import ManualFunctionalExerciseAssembler
from applications.rsc.commands import CreateFunctionalExerciseCommand
from applications.rsc.dto import FunctionalExerciseDTO
from applications.rsc.repositories import (
    InMemoryFunctionalExerciseRepository,
)
from applications.rsc.services import (
    CreateFunctionalExerciseService,
    ListFunctionalExercisesService,
)


def command(
    *,
    person_id="person-1",
    role="Fiscal titular",
    start_date=date(2024, 1, 1),
    end_date=None,
    context_unit="Unidade",
    context_reference="Contrato 123",
):
    return CreateFunctionalExerciseCommand(
        person_id=person_id,
        exercise_type_code="fiscal contrato",
        exercise_type_label="Fiscalização de contrato",
        role=role,
        context_organization="Instituição",
        start_date=start_date,
        end_date=end_date,
        context_unit=context_unit,
        context_reference=context_reference,
    )


class ReadOnlyRepositorySpy:
    def __init__(self, exercises=()):
        self.exercises = tuple(exercises)
        self.list_calls = 0

    def list_all(self):
        self.list_calls += 1
        return self.exercises


class ListFunctionalExercisesServiceTests(unittest.TestCase):
    def test_empty_repository_returns_empty_tuple(self):
        result = ListFunctionalExercisesService(
            InMemoryFunctionalExerciseRepository()
        ).execute()

        self.assertEqual(result, ())
        self.assertIsInstance(result, tuple)

    def test_one_exercise_returns_one_dto(self):
        exercise = ManualFunctionalExerciseAssembler().assemble(command())

        result = ListFunctionalExercisesService(
            ReadOnlyRepositorySpy((exercise,))
        ).execute()

        self.assertEqual(len(result), 1)
        self.assertIsInstance(result[0], FunctionalExerciseDTO)

    def test_multiple_exercises_preserve_repository_order(self):
        assembler = ManualFunctionalExerciseAssembler()
        first = assembler.assemble(command(role="Primeiro"))
        second = assembler.assemble(command(role="Segundo"))

        result = ListFunctionalExercisesService(
            ReadOnlyRepositorySpy((first, second))
        ).execute()

        self.assertEqual(
            tuple(item.id for item in result),
            (str(first.id), str(second.id)),
        )

    def test_dto_preserves_all_fields(self):
        exercise = ManualFunctionalExerciseAssembler().assemble(
            command(
                person_id="person-2",
                role="Presidente",
                start_date=date(2023, 2, 1),
                end_date=date(2023, 11, 30),
                context_unit=None,
                context_reference=None,
            )
        )

        result = ListFunctionalExercisesService(
            ReadOnlyRepositorySpy((exercise,))
        ).execute()[0]

        self.assertEqual(result.id, str(exercise.id))
        self.assertEqual(result.person_id, exercise.person_id)
        self.assertEqual(
            result.exercise_type_code,
            exercise.exercise_type.code,
        )
        self.assertEqual(
            result.exercise_type_label,
            exercise.exercise_type.label,
        )
        self.assertEqual(result.role, exercise.role.name)
        self.assertEqual(
            result.context_organization,
            exercise.context.organization,
        )
        self.assertEqual(result.context_unit, exercise.context.unit)
        self.assertEqual(
            result.context_reference,
            exercise.context.reference,
        )
        self.assertEqual(result.start_date, exercise.period.start_date)
        self.assertEqual(result.end_date, exercise.period.end_date)
        self.assertEqual(result.status, exercise.status.value)

    def test_dto_contains_no_domain_value_objects(self):
        exercise = ManualFunctionalExerciseAssembler().assemble(command())

        result = ListFunctionalExercisesService(
            ReadOnlyRepositorySpy((exercise,))
        ).execute()[0]

        for field in fields(result):
            value = getattr(result, field.name)
            self.assertNotEqual(
                value.__class__.__module__,
                "applications.rsc.models.functional_exercise",
            )

    def test_does_not_change_repository_or_entities(self):
        repository = InMemoryFunctionalExerciseRepository()
        exercise = ManualFunctionalExerciseAssembler().assemble(command())
        repository.save(exercise)
        original_items = repository.list_all()

        ListFunctionalExercisesService(repository).execute()

        self.assertEqual(repository.list_all(), original_items)
        self.assertIs(repository.list_all()[0], exercise)

    def test_uses_only_list_all_without_writing(self):
        exercise = ManualFunctionalExerciseAssembler().assemble(command())
        repository = ReadOnlyRepositorySpy((exercise,))

        ListFunctionalExercisesService(repository).execute()

        self.assertEqual(repository.list_calls, 1)

    def test_execute_requires_no_assembler_and_generates_no_identity(self):
        exercise = ManualFunctionalExerciseAssembler().assemble(command())
        repository = ReadOnlyRepositorySpy((exercise,))
        service = ListFunctionalExercisesService(repository)

        first = service.execute()
        second = service.execute()

        self.assertEqual(first[0].id, str(exercise.id))
        self.assertEqual(second[0].id, str(exercise.id))
        self.assertEqual(repository.list_calls, 2)

    def test_create_service_continues_to_share_repository(self):
        repository = InMemoryFunctionalExerciseRepository()
        created = CreateFunctionalExerciseService(
            repository,
            ManualFunctionalExerciseAssembler(),
        ).execute(command())

        listed = ListFunctionalExercisesService(repository).execute()

        self.assertEqual(len(listed), 1)
        self.assertEqual(listed[0], created)

    def test_service_is_exported(self):
        self.assertTrue(ListFunctionalExercisesService)


if __name__ == "__main__":
    unittest.main()
