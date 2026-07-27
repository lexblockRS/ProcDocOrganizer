from datetime import date
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from applications.rsc.models import (
    FunctionalAssignmentEvidence,
    FunctionalAssignmentEvidenceId,
    FunctionalAssignmentEvidenceStatus,
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
    SQLiteFunctionalAssignmentEvidenceRepository,
    SQLiteFunctionalExerciseRepository,
)

from tests.rsc_repository_contracts import (
    FunctionalAssignmentEvidenceRepositoryContract,
    FunctionalExerciseRepositoryContract,
)


def uuid_for(index):
    return f"00000000-0000-4000-8000-{index:012d}"


class InMemoryFunctionalAssignmentEvidenceContractTests(
    FunctionalAssignmentEvidenceRepositoryContract,
    unittest.TestCase,
):
    def make_assignment_repository(self):
        return InMemoryFunctionalAssignmentEvidenceRepository()

    def make_assignment(self, index):
        return FunctionalAssignmentEvidence(
            id=FunctionalAssignmentEvidenceId(uuid_for(index)),
            person_id=f"person-{index}",
            source_evidence_reference=SourceEvidenceReference(
                f"source-{index}"
            ),
            exercise_type_code="coordenacao",
            exercise_type_label="Coordenação",
            role=f"Papel {index}",
            organization="Universidade",
            start_date=date(2024, 1, index),
            status=FunctionalAssignmentEvidenceStatus.NORMALIZED,
        )


class InMemoryFunctionalExerciseContractTests(
    FunctionalExerciseRepositoryContract,
    unittest.TestCase,
):
    def make_exercise_repository(self):
        return InMemoryFunctionalExerciseRepository()

    def make_exercise(self, index, assignment_indexes=(1,)):
        return FunctionalExercise(
            id=FunctionalExerciseId(uuid_for(index)),
            person_id=f"person-{index}",
            exercise_type=FunctionalExerciseType(
                code="coordenacao",
                label="Coordenação",
            ),
            role=FunctionalRole(f"Papel {index}"),
            context=FunctionalContext("Universidade"),
            period=FunctionalPeriod(date(2024, 1, index)),
            status=FunctionalExerciseStatus.ACTIVE,
            functional_assignment_evidence_ids=tuple(
                FunctionalAssignmentEvidenceId(
                    uuid_for(100 + assignment_index)
                )
                for assignment_index in assignment_indexes
            ),
        )


class SQLiteFunctionalAssignmentEvidenceContractTests(
    FunctionalAssignmentEvidenceRepositoryContract,
    unittest.TestCase,
):
    def setUp(self):
        self.temporary_directory = TemporaryDirectory()
        self.addCleanup(self.temporary_directory.cleanup)
        self._database_index = 0

    def make_assignment_repository(self):
        self._database_index += 1
        database_path = (
            Path(self.temporary_directory.name)
            / f"contract-{self._database_index}.db"
        )
        return SQLiteFunctionalAssignmentEvidenceRepository(
            database_path
        )

    def make_assignment(self, index):
        return FunctionalAssignmentEvidence(
            id=FunctionalAssignmentEvidenceId(uuid_for(index)),
            person_id=f"person-{index}",
            source_evidence_reference=SourceEvidenceReference(
                f"source-{index}"
            ),
            exercise_type_code="coordenacao",
            exercise_type_label="Coordenação",
            role=f"Papel {index}",
            organization="Universidade",
            start_date=date(2024, 1, index),
            status=FunctionalAssignmentEvidenceStatus.NORMALIZED,
        )


class SQLiteFunctionalExerciseContractTests(
    FunctionalExerciseRepositoryContract,
    unittest.TestCase,
):
    def setUp(self):
        self.temporary_directory = TemporaryDirectory()
        self.addCleanup(self.temporary_directory.cleanup)
        self._database_index = 0
        self._current_database_path = None

    def make_exercise_repository(self):
        self._database_index += 1
        self._current_database_path = (
            Path(self.temporary_directory.name)
            / f"exercise-contract-{self._database_index}.db"
        )
        return SQLiteFunctionalExerciseRepository(
            self._current_database_path
        )

    def make_exercise(self, index, assignment_indexes=(1,)):
        assignment_repository = (
            SQLiteFunctionalAssignmentEvidenceRepository(
                self._current_database_path
            )
        )
        assignment_ids = tuple(
            FunctionalAssignmentEvidenceId(
                uuid_for(100 + assignment_index)
            )
            for assignment_index in assignment_indexes
        )
        for offset, assignment_id in enumerate(assignment_ids, start=1):
            if assignment_repository.get_by_id(assignment_id) is None:
                assignment_repository.save(
                    FunctionalAssignmentEvidence(
                        id=assignment_id,
                        person_id=f"person-{offset}",
                        source_evidence_reference=SourceEvidenceReference(
                            f"source-{offset}"
                        ),
                        exercise_type_code="coordenacao",
                        exercise_type_label="Coordenação",
                        role=f"Papel {offset}",
                        organization="Universidade",
                        start_date=date(2024, 1, offset),
                        status=(
                            FunctionalAssignmentEvidenceStatus.NORMALIZED
                        ),
                    )
                )
        return FunctionalExercise(
            id=FunctionalExerciseId(uuid_for(index)),
            person_id=f"person-{index}",
            exercise_type=FunctionalExerciseType(
                code="coordenacao",
                label="Coordenação",
            ),
            role=FunctionalRole(f"Papel {index}"),
            context=FunctionalContext("Universidade"),
            period=FunctionalPeriod(date(2024, 1, index)),
            status=FunctionalExerciseStatus.ACTIVE,
            functional_assignment_evidence_ids=assignment_ids,
        )

    def test_contract_exercise_repository_instances_are_isolated(self):
        first_repository = self.make_exercise_repository()
        exercise = self.make_exercise(1)
        second_repository = self.make_exercise_repository()

        first_repository.save(exercise)

        self.assertEqual(first_repository.list_all(), (exercise,))
        self.assertEqual(second_repository.list_all(), ())


if __name__ == "__main__":
    unittest.main()
