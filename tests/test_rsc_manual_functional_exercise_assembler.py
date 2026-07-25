from datetime import date
from uuid import UUID
import unittest

from applications.rsc.assemblers import ManualFunctionalExerciseAssembler
from applications.rsc.commands import CreateFunctionalExerciseCommand
from applications.rsc.dto import FunctionalExerciseDTO
from applications.rsc.models import (
    FunctionalExercise,
    FunctionalExerciseId,
    FunctionalExerciseStatus,
)
from applications.rsc.services import CreateFunctionalExerciseService


def command(
    *,
    person_id="person-1",
    exercise_type_code="fiscal contrato",
    exercise_type_label="Fiscalização de contrato",
    role="Fiscal titular",
    context_organization="Instituição",
    start_date=date(2024, 1, 1),
    end_date=None,
    context_unit="Unidade",
    context_reference="Contrato 123",
):
    return CreateFunctionalExerciseCommand(
        person_id=person_id,
        exercise_type_code=exercise_type_code,
        exercise_type_label=exercise_type_label,
        role=role,
        context_organization=context_organization,
        start_date=start_date,
        end_date=end_date,
        context_unit=context_unit,
        context_reference=context_reference,
    )


class ManualFunctionalExerciseAssemblerTests(unittest.TestCase):
    def setUp(self):
        self.assembler = ManualFunctionalExerciseAssembler()

    def test_assembles_valid_closed_exercise(self):
        exercise = self.assembler.assemble(
            command(end_date=date(2024, 12, 31))
        )

        self.assertIsInstance(exercise, FunctionalExercise)
        self.assertEqual(exercise.period.end_date, date(2024, 12, 31))
        self.assertIs(
            exercise.status,
            FunctionalExerciseStatus.ENDED,
        )

    def test_assembles_valid_open_exercise(self):
        exercise = self.assembler.assemble(command())

        self.assertIsNone(exercise.period.end_date)
        self.assertIs(
            exercise.status,
            FunctionalExerciseStatus.ACTIVE,
        )

    def test_generates_valid_uuid(self):
        exercise = self.assembler.assemble(command())

        self.assertEqual(str(UUID(str(exercise.id))), str(exercise.id))

    def test_generates_distinct_ids(self):
        first = self.assembler.assemble(command())
        second = self.assembler.assemble(command())

        self.assertNotEqual(first.id, second.id)

    def test_projects_all_command_fields_into_value_objects(self):
        exercise = self.assembler.assemble(
            command(
                person_id="  person-2  ",
                exercise_type_code="  Gestão Colegiada ",
                exercise_type_label=" Gestão   colegiada ",
                role=" Presidente   titular ",
                context_organization=" Instituto   Federal ",
                start_date=date(2023, 2, 1),
                end_date=date(2023, 11, 30),
                context_unit=" Conselho   Superior ",
                context_reference=" Portaria   123 ",
            )
        )

        self.assertEqual(exercise.person_id, "person-2")
        self.assertEqual(
            exercise.exercise_type.code,
            "gestão_colegiada",
        )
        self.assertEqual(
            exercise.exercise_type.label,
            "Gestão colegiada",
        )
        self.assertEqual(exercise.role.name, "Presidente titular")
        self.assertEqual(
            exercise.context.organization,
            "Instituto Federal",
        )
        self.assertEqual(exercise.context.unit, "Conselho Superior")
        self.assertEqual(exercise.context.reference, "Portaria 123")
        self.assertEqual(exercise.period.start_date, date(2023, 2, 1))
        self.assertEqual(exercise.period.end_date, date(2023, 11, 30))

    def test_preserves_none_context_unit(self):
        exercise = self.assembler.assemble(
            command(context_unit=None)
        )

        self.assertIsNone(exercise.context.unit)

    def test_preserves_none_context_reference(self):
        exercise = self.assembler.assemble(
            command(context_reference=None)
        )

        self.assertIsNone(exercise.context.reference)

    def test_rejects_end_before_start_through_domain(self):
        with self.assertRaises(ValueError):
            self.assembler.assemble(
                command(end_date=date(2023, 12, 31))
            )

    def test_propagates_type_error(self):
        with self.assertRaises(TypeError):
            self.assembler.assemble(command(start_date="2024-01-01"))

    def test_rejects_invalid_command_type(self):
        with self.assertRaises(TypeError):
            self.assembler.assemble(object())

    def test_propagates_value_error(self):
        with self.assertRaises(ValueError):
            self.assembler.assemble(command(role=" "))

    def test_requires_no_repository_and_returns_entity_not_dto(self):
        exercise = ManualFunctionalExerciseAssembler().assemble(command())

        self.assertIsInstance(exercise, FunctionalExercise)
        self.assertNotIsInstance(exercise, FunctionalExerciseDTO)

    def test_does_not_associate_project(self):
        exercise = self.assembler.assemble(command())

        self.assertFalse(hasattr(exercise, "project"))
        self.assertFalse(hasattr(exercise, "project_id"))


class AssemblerSpy:
    def __init__(self, result=None, error=None):
        self.result = result
        self.error = error
        self.commands = []

    def assemble(self, received_command):
        self.commands.append(received_command)
        if self.error is not None:
            raise self.error
        return self.result


class RepositorySpy:
    def __init__(self):
        self.saved = []

    def save(self, exercise):
        self.saved.append(exercise)


class CreateFunctionalExerciseDelegationTests(unittest.TestCase):
    def setUp(self):
        self.created = ManualFunctionalExerciseAssembler().assemble(
            command()
        )
        self.repository = RepositorySpy()
        self.assembler = AssemblerSpy(result=self.created)
        self.service = CreateFunctionalExerciseService(
            self.repository,
            self.assembler,
        )

    def test_service_delegates_creation_once(self):
        request = command()

        self.service.execute(request)

        self.assertEqual(self.assembler.commands, [request])

    def test_service_saves_exact_assembler_entity(self):
        self.service.execute(command())

        self.assertEqual(self.repository.saved, [self.created])
        self.assertIs(self.repository.saved[0], self.created)

    def test_service_returns_correct_dto(self):
        result = self.service.execute(command())

        self.assertIsInstance(result, FunctionalExerciseDTO)
        self.assertEqual(result.id, str(self.created.id))
        self.assertEqual(result.person_id, self.created.person_id)
        self.assertEqual(
            result.exercise_type_code,
            self.created.exercise_type.code,
        )
        self.assertEqual(result.role, self.created.role.name)
        self.assertEqual(result.status, self.created.status.value)

    def test_repository_is_not_called_when_assembler_fails(self):
        error = ValueError("falha controlada")
        service = CreateFunctionalExerciseService(
            self.repository,
            AssemblerSpy(error=error),
        )

        with self.assertRaisesRegex(ValueError, "falha controlada"):
            service.execute(command())

        self.assertEqual(self.repository.saved, [])

    def test_assembler_is_exported_by_package(self):
        self.assertTrue(ManualFunctionalExerciseAssembler)


if __name__ == "__main__":
    unittest.main()
