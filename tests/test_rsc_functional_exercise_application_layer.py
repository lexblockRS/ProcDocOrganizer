from dataclasses import FrozenInstanceError, fields
from datetime import date
from uuid import UUID
import unittest

from applications.rsc.assemblers import ManualFunctionalExerciseAssembler
from applications.rsc.commands import (
    CreateActivityCommand,
    CreateFunctionalExerciseCommand,
    CreateProjectCommand,
)
from applications.rsc.dto import (
    ActivityDTO,
    FunctionalExerciseDTO,
    ProjectDTO,
)
from applications.rsc.models import (
    Activity,
    FunctionalExercise,
    FunctionalExerciseId,
    Project,
)
from applications.rsc.ports import (
    ActivityRepository,
    FunctionalExerciseRepository,
    ProjectRepository,
)
from applications.rsc.repositories import (
    InMemoryActivityRepository,
    InMemoryFunctionalExerciseRepository,
    InMemoryProjectRepository,
)
from applications.rsc.services import (
    CreateActivityService,
    CreateFunctionalExerciseService,
    CreateProjectService,
)


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


class CreateFunctionalExerciseServiceTests(unittest.TestCase):
    def setUp(self):
        self.repository = InMemoryFunctionalExerciseRepository()
        self.service = CreateFunctionalExerciseService(
            self.repository,
            ManualFunctionalExerciseAssembler(),
        )

    def test_creates_valid_closed_exercise(self):
        result = self.service.execute(
            command(end_date=date(2024, 12, 31))
        )

        self.assertIsInstance(result, FunctionalExerciseDTO)
        self.assertEqual(result.start_date, date(2024, 1, 1))
        self.assertEqual(result.end_date, date(2024, 12, 31))
        self.assertEqual(result.status, "ended")

    def test_creates_valid_open_exercise(self):
        result = self.service.execute(command())

        self.assertIsNone(result.end_date)
        self.assertEqual(result.status, "active")

    def test_generates_valid_uuid(self):
        result = self.service.execute(command())

        self.assertEqual(str(UUID(result.id)), result.id)

    def test_generates_distinct_ids(self):
        first = self.service.execute(command())
        second = self.service.execute(command())

        self.assertNotEqual(first.id, second.id)

    def test_persists_created_exercise(self):
        result = self.service.execute(command())

        stored = self.repository.get_by_id(
            FunctionalExerciseId(result.id)
        )

        self.assertIsInstance(stored, FunctionalExercise)
        self.assertEqual(str(stored.id), result.id)

    def test_returns_dto_with_normalized_simple_values(self):
        result = self.service.execute(
            command(
                person_id="  person-1  ",
                exercise_type_code="  Fiscal Contrato  ",
                exercise_type_label=" Fiscalização   de contrato ",
                role=" Fiscal   titular ",
                context_organization=" Instituto   Federal ",
                context_unit=" Unidade   Central ",
                context_reference=" Contrato   123 ",
            )
        )

        self.assertEqual(result.person_id, "person-1")
        self.assertEqual(result.exercise_type_code, "fiscal_contrato")
        self.assertEqual(
            result.exercise_type_label,
            "Fiscalização de contrato",
        )
        self.assertEqual(result.role, "Fiscal titular")
        self.assertEqual(
            result.context_organization,
            "Instituto Federal",
        )
        self.assertEqual(result.context_unit, "Unidade Central")
        self.assertEqual(result.context_reference, "Contrato 123")

    def test_propagates_type_error_from_domain(self):
        with self.assertRaises(TypeError):
            self.service.execute(command(start_date="2024-01-01"))

    def test_rejects_invalid_command_type(self):
        with self.assertRaises(TypeError):
            self.service.execute(object())

    def test_propagates_value_error_from_domain(self):
        with self.assertRaises(ValueError):
            self.service.execute(command(role=" "))

    def test_rejects_end_before_start(self):
        with self.assertRaises(ValueError):
            self.service.execute(
                command(end_date=date(2023, 12, 31))
            )

    def test_does_not_associate_exercise_with_project(self):
        result = self.service.execute(command())
        stored = self.repository.get_by_id(
            FunctionalExerciseId(result.id)
        )

        self.assertFalse(hasattr(stored, "project"))
        self.assertFalse(hasattr(stored, "project_id"))


class InMemoryFunctionalExerciseRepositoryTests(unittest.TestCase):
    def setUp(self):
        self.repository = InMemoryFunctionalExerciseRepository()
        self.service = CreateFunctionalExerciseService(
            self.repository,
            ManualFunctionalExerciseAssembler(),
        )

    def test_returns_none_for_unknown_id(self):
        self.assertIsNone(
            self.repository.get_by_id(
                FunctionalExerciseId(
                    "12345678-1234-5678-1234-567812345678"
                )
            )
        )

    def test_list_all_is_initially_empty(self):
        self.assertEqual(self.repository.list_all(), ())

    def test_list_all_preserves_insertion_order(self):
        first = self.service.execute(command(role="Primeiro"))
        second = self.service.execute(command(role="Segundo"))

        self.assertEqual(
            tuple(str(item.id) for item in self.repository.list_all()),
            (first.id, second.id),
        )

    def test_save_replaces_same_id_without_changing_order(self):
        first = self.service.execute(command(role="Primeiro"))
        existing = self.repository.get_by_id(
            FunctionalExerciseId(first.id)
        )
        replacement = FunctionalExercise(
            id=existing.id,
            person_id=existing.person_id,
            exercise_type=existing.exercise_type,
            role=existing.role,
            context=existing.context,
            period=existing.period,
            status=existing.status,
        )

        self.repository.save(replacement)

        self.assertIs(
            self.repository.get_by_id(existing.id),
            replacement,
        )
        self.assertEqual(self.repository.list_all(), (replacement,))

    def test_satisfies_structural_repository_protocol(self):
        repository: FunctionalExerciseRepository = self.repository
        result = self.service.execute(command())
        identifier = FunctionalExerciseId(result.id)

        self.assertIsNotNone(repository.get_by_id(identifier))
        self.assertEqual(len(repository.list_all()), 1)


class FunctionalExerciseApplicationContractsTests(unittest.TestCase):
    def test_dto_contains_only_application_types(self):
        result = CreateFunctionalExerciseService(
            InMemoryFunctionalExerciseRepository(),
            ManualFunctionalExerciseAssembler(),
        ).execute(command())

        for field in fields(result):
            value = getattr(result, field.name)
            self.assertNotEqual(
                value.__class__.__module__,
                "applications.rsc.models.functional_exercise",
            )

    def test_dto_does_not_expose_value_objects(self):
        result = CreateFunctionalExerciseService(
            InMemoryFunctionalExerciseRepository(),
            ManualFunctionalExerciseAssembler(),
        ).execute(command())

        self.assertIsInstance(result.id, str)
        self.assertIsInstance(result.exercise_type_code, str)
        self.assertIsInstance(result.exercise_type_label, str)
        self.assertIsInstance(result.role, str)
        self.assertIsInstance(result.context_organization, str)
        self.assertIsInstance(result.start_date, date)
        self.assertIsNone(result.end_date)
        self.assertIsInstance(result.status, str)

    def test_command_and_dto_are_immutable(self):
        request = command()
        result = CreateFunctionalExerciseService(
            InMemoryFunctionalExerciseRepository(),
            ManualFunctionalExerciseAssembler(),
        ).execute(request)

        with self.assertRaises(FrozenInstanceError):
            request.role = "Outro"
        with self.assertRaises(FrozenInstanceError):
            result.role = "Outro"

    def test_preserves_existing_public_exports(self):
        self.assertTrue(Activity)
        self.assertTrue(Project)
        self.assertTrue(FunctionalExercise)
        self.assertTrue(CreateActivityCommand)
        self.assertTrue(CreateProjectCommand)
        self.assertTrue(ActivityDTO)
        self.assertTrue(ProjectDTO)
        self.assertTrue(ActivityRepository)
        self.assertTrue(ProjectRepository)
        self.assertTrue(InMemoryActivityRepository)
        self.assertTrue(InMemoryProjectRepository)
        self.assertTrue(CreateActivityService)
        self.assertTrue(CreateProjectService)


if __name__ == "__main__":
    unittest.main()
