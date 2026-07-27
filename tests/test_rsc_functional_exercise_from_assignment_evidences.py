from dataclasses import FrozenInstanceError, fields
from datetime import date
import unittest

from applications.rsc.assemblers import (
    FunctionalAssignmentEvidenceAssembler,
    ManualFunctionalExerciseAssembler,
)
from applications.rsc.commands import (
    CreateFunctionalAssignmentEvidenceCommand,
    CreateFunctionalExerciseCommand,
)
from applications.rsc.models import (
    FunctionalAssignmentEvidenceStatus,
)
from applications.rsc.repositories import (
    InMemoryFunctionalAssignmentEvidenceRepository,
    InMemoryFunctionalExerciseRepository,
)
from applications.rsc.services import (
    CreateFunctionalExerciseService,
    DuplicateFunctionalAssignmentEvidenceReferenceError,
    FunctionalAssignmentEvidenceNotFoundError,
    FunctionalAssignmentEvidenceRequiredError,
    FunctionalAssignmentNormalizer,
    IncompatibleFunctionalAssignmentEvidenceError,
    ListFunctionalExercisesService,
)


SOURCE_ID = "host-evidence-1"


def assignment_command(role="Coordenador"):
    return CreateFunctionalAssignmentEvidenceCommand(
        person_id="person-1",
        source_evidence_reference=SOURCE_ID,
        exercise_type_code="coordenacao",
        exercise_type_label="Coordenação",
        role=role,
        organization="Universidade",
        start_date=date(2024, 1, 1),
        administrative_reference="Portaria 10/2024",
    )


def exercise_command(*assignment_ids):
    return CreateFunctionalExerciseCommand(
        person_id="person-1",
        exercise_type_code="coordenacao",
        exercise_type_label="Coordenação",
        role="Coordenador",
        context_organization="Universidade",
        start_date=date(2024, 1, 1),
        functional_assignment_evidence_ids=tuple(assignment_ids),
    )


class AssemblerSpy:
    def __init__(self):
        self.delegate = ManualFunctionalExerciseAssembler()
        self.commands = []

    def assemble(self, command):
        self.commands.append(command)
        return self.delegate.assemble(command)


class ExerciseFlowFixture:
    def __init__(self):
        self.assignment_repository = (
            InMemoryFunctionalAssignmentEvidenceRepository()
        )
        self.exercise_repository = InMemoryFunctionalExerciseRepository()
        self.assembler = AssemblerSpy()
        self.create_service = CreateFunctionalExerciseService(
            self.exercise_repository,
            self.assembler,
            self.assignment_repository,
        )
        self.list_service = ListFunctionalExercisesService(
            self.exercise_repository
        )

    def add_assignment(self, role="Coordenador"):
        raw = FunctionalAssignmentEvidenceAssembler().assemble(
            assignment_command(role)
        )
        normalized = FunctionalAssignmentNormalizer().normalize(raw)
        self.assignment_repository.save(normalized)
        return normalized


class CreateExerciseFromAssignmentsTests(unittest.TestCase):
    def setUp(self):
        self.flow = ExerciseFlowFixture()

    def test_creates_exercise_from_one_assignment(self):
        assignment = self.flow.add_assignment()

        result = self.flow.create_service.execute(
            exercise_command(str(assignment.id))
        )

        self.assertEqual(
            result.functional_assignment_evidence_ids,
            (str(assignment.id),),
        )

    def test_creates_exercise_from_multiple_assignments_in_input_order(self):
        first = self.flow.add_assignment("Coordenador")
        second = self.flow.add_assignment("Coordenador substituto")

        result = self.flow.create_service.execute(
            exercise_command(str(second.id), str(first.id))
        )

        self.assertEqual(
            result.functional_assignment_evidence_ids,
            (str(second.id), str(first.id)),
        )

    def test_rejects_empty_selection_before_assembler(self):
        with self.assertRaises(
            FunctionalAssignmentEvidenceRequiredError
        ):
            self.flow.create_service.execute(exercise_command())

        self.assertEqual(self.flow.assembler.commands, [])
        self.assertEqual(self.flow.exercise_repository.list_all(), ())

    def test_rejects_missing_assignment_before_assembler(self):
        missing = "11111111-1111-4111-8111-111111111111"

        with self.assertRaises(FunctionalAssignmentEvidenceNotFoundError):
            self.flow.create_service.execute(exercise_command(missing))

        self.assertEqual(self.flow.assembler.commands, [])

    def test_rejects_duplicate_references_before_assembler(self):
        assignment = self.flow.add_assignment()
        reference = str(assignment.id)

        with self.assertRaises(
            DuplicateFunctionalAssignmentEvidenceReferenceError
        ):
            self.flow.create_service.execute(
                exercise_command(reference, reference)
            )

        self.assertEqual(self.flow.assembler.commands, [])

    def test_rejects_raw_assignment_as_incompatible_current_stage(self):
        raw = FunctionalAssignmentEvidenceAssembler().assemble(
            assignment_command()
        )
        self.flow.assignment_repository.save(raw)

        with self.assertRaises(
            IncompatibleFunctionalAssignmentEvidenceError
        ):
            self.flow.create_service.execute(
                exercise_command(str(raw.id))
            )

        self.assertIs(
            raw.status,
            FunctionalAssignmentEvidenceStatus.RAW,
        )

    def test_delegates_creation_to_existing_manual_assembler(self):
        assignment = self.flow.add_assignment()
        command = exercise_command(str(assignment.id))

        self.flow.create_service.execute(command)

        self.assertEqual(self.flow.assembler.commands, [command])

    def test_persists_exercise_and_gets_it_by_id(self):
        assignment = self.flow.add_assignment()

        result = self.flow.create_service.execute(
            exercise_command(str(assignment.id))
        )
        stored = self.flow.exercise_repository.list_all()[0]

        self.assertIs(
            self.flow.exercise_repository.get_by_id(stored.id),
            stored,
        )
        self.assertEqual(str(stored.id), result.id)

    def test_lists_created_dto_with_provenance(self):
        assignment = self.flow.add_assignment()
        created = self.flow.create_service.execute(
            exercise_command(str(assignment.id))
        )

        listed = self.flow.list_service.execute()

        self.assertEqual(listed, (created,))
        self.assertEqual(
            listed[0].functional_assignment_evidence_ids,
            (str(assignment.id),),
        )

    def test_dto_is_immutable_and_contains_only_stable_reference_values(self):
        assignment = self.flow.add_assignment()
        result = self.flow.create_service.execute(
            exercise_command(str(assignment.id))
        )

        with self.assertRaises(FrozenInstanceError):
            result.status = "ended"
        self.assertTrue(
            all(
                not field.name.startswith("source_evidence")
                for field in fields(result)
            )
        )
        self.assertTrue(
            all(
                isinstance(reference, str)
                for reference
                in result.functional_assignment_evidence_ids
            )
        )

    def test_exercise_stores_ids_not_assignment_objects(self):
        assignment = self.flow.add_assignment()
        self.flow.create_service.execute(
            exercise_command(str(assignment.id))
        )

        stored = self.flow.exercise_repository.list_all()[0]

        self.assertEqual(
            tuple(str(item) for item in stored.functional_assignment_evidence_ids),
            (str(assignment.id),),
        )
        self.assertFalse(
            hasattr(stored, "functional_assignment_evidences")
        )
        self.assertNotIn(
            assignment,
            stored.functional_assignment_evidence_ids,
        )

    def test_exercise_does_not_copy_host_evidence(self):
        assignment = self.flow.add_assignment()
        self.flow.create_service.execute(
            exercise_command(str(assignment.id))
        )

        stored = self.flow.exercise_repository.list_all()[0]

        self.assertFalse(hasattr(stored, "evidence"))
        self.assertFalse(hasattr(stored, "source_evidence"))
        self.assertEqual(
            str(assignment.source_evidence_reference),
            SOURCE_ID,
        )

    def test_validation_failure_does_not_store_partial_exercise(self):
        valid = self.flow.add_assignment()
        missing = "22222222-2222-4222-8222-222222222222"

        with self.assertRaises(FunctionalAssignmentEvidenceNotFoundError):
            self.flow.create_service.execute(
                exercise_command(str(valid.id), missing)
            )

        self.assertEqual(self.flow.exercise_repository.list_all(), ())

    def test_legacy_manual_service_without_assignment_repository_still_works(
        self,
    ):
        repository = InMemoryFunctionalExerciseRepository()
        service = CreateFunctionalExerciseService(
            repository,
            ManualFunctionalExerciseAssembler(),
        )

        result = service.execute(exercise_command())

        self.assertEqual(result.functional_assignment_evidence_ids, ())
        self.assertEqual(len(repository.list_all()), 1)


if __name__ == "__main__":
    unittest.main()
