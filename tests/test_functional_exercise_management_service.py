from datetime import date
import unittest
from uuid import uuid4

from applications.rsc.models import (
    FunctionalAssignmentEvidence,
    FunctionalAssignmentEvidenceId,
    FunctionalContext,
    FunctionalExercise,
    FunctionalExerciseId,
    FunctionalExerciseStatus,
    FunctionalExerciseType,
    FunctionalPeriod,
    FunctionalRole,
    SourceEvidenceReference,
)
from applications.rsc.repositories import (
    InMemoryFunctionalAssignmentEvidenceRepository,
    InMemoryFunctionalExerciseRepository,
)
from applications.rsc.services import (
    FunctionalExerciseManagementError,
    FunctionalExerciseManagementService,
)


def assignment():
    return FunctionalAssignmentEvidence(
        id=FunctionalAssignmentEvidenceId(str(uuid4())),
        person_id="person-1",
        source_evidence_reference=SourceEvidenceReference("evidence-1"),
        exercise_type_code="gestao",
        exercise_type_label="Gestão",
        role="Coordenador",
        organization="Universidade",
    )


def exercise(reference):
    return FunctionalExercise(
        id=FunctionalExerciseId(str(uuid4())),
        person_id="person-1",
        exercise_type=FunctionalExerciseType("gestao", "Gestão"),
        role=FunctionalRole("Coordenador"),
        context=FunctionalContext("Universidade"),
        period=FunctionalPeriod(date(2024, 1, 1)),
        status=FunctionalExerciseStatus.ACTIVE,
        functional_assignment_evidence_ids=(reference.id,),
    )


class FunctionalExerciseManagementServiceTests(unittest.TestCase):
    def setUp(self):
        self.assignments = InMemoryFunctionalAssignmentEvidenceRepository()
        self.exercises = InMemoryFunctionalExerciseRepository()
        self.assignment = assignment()
        self.assignments.save(self.assignment)
        self.exercise = exercise(self.assignment)
        self.exercises.save(self.exercise)
        self.service = FunctionalExerciseManagementService(
            self.exercises,
            self.assignments,
        )

    def test_update_preserves_identity_and_references(self):
        updated = self.service.update(
            str(self.exercise.id),
            person_id="person-2",
            exercise_type_code="direcao",
            exercise_type_label="Direção",
            role="Diretor",
            context_organization="Campus",
            start_date=date(2024, 1, 1),
            end_date=date(2024, 12, 31),
            functional_assignment_evidence_ids=(str(self.assignment.id),),
        )
        self.assertEqual(updated.id, self.exercise.id)
        self.assertEqual(
            updated.functional_assignment_evidence_ids,
            (self.assignment.id,),
        )
        self.assertEqual(updated.role.name, "Diretor")
        self.assertIs(updated.status, FunctionalExerciseStatus.ENDED)

    def test_duplicate_and_missing_references_are_rejected(self):
        values = dict(
            person_id="person-1",
            exercise_type_code="gestao",
            exercise_type_label="Gestão",
            role="Coordenador",
            context_organization="Universidade",
            start_date=date(2024, 1, 1),
        )
        with self.assertRaises(FunctionalExerciseManagementError):
            self.service.update(
                str(self.exercise.id),
                functional_assignment_evidence_ids=(
                    str(self.assignment.id),
                    str(self.assignment.id),
                ),
                **values,
            )
        with self.assertRaises(FunctionalExerciseManagementError):
            self.service.update(
                str(self.exercise.id),
                functional_assignment_evidence_ids=(str(uuid4()),),
                **values,
            )

    def test_delete_does_not_modify_assignment(self):
        deleted = self.service.delete(str(self.exercise.id))
        self.assertEqual(deleted.id, self.exercise.id)
        self.assertIsNone(self.exercises.get_by_id(self.exercise.id))
        self.assertEqual(
            self.assignments.get_by_id(self.assignment.id),
            self.assignment,
        )
