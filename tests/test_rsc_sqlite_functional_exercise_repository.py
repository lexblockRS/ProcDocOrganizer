from dataclasses import replace
from datetime import date
from pathlib import Path
import sqlite3
from tempfile import TemporaryDirectory
import unittest

from applications.rsc.commands import (
    CreateFunctionalAssignmentEvidenceCommand,
    CreateFunctionalExerciseCommand,
)
from applications.rsc.composition import (
    create_rsc_project_session,
    create_sqlite_rsc_repositories,
)
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
from applications.rsc.ports import (
    FunctionalExerciseAssignmentEvidenceNotFoundError,
    FunctionalExercisePersistenceError,
)
from applications.rsc.repositories import (
    SQLiteFunctionalAssignmentEvidenceRepository,
    SQLiteFunctionalExerciseRepository,
)
from database import ProjectDatabase, initialize_database


def uuid_for(index):
    return f"20000000-0000-4000-8000-{index:012d}"


def assignment(index):
    return FunctionalAssignmentEvidence(
        id=FunctionalAssignmentEvidenceId(uuid_for(100 + index)),
        person_id="person-1",
        source_evidence_reference=SourceEvidenceReference(
            f"host-evidence-{index}"
        ),
        exercise_type_code="coordenacao",
        exercise_type_label="Coordenação",
        role=f"Documento {index}",
        organization="Universidade",
        start_date=date(2024, 1, index),
        status=FunctionalAssignmentEvidenceStatus.NORMALIZED,
    )


def exercise(index=1, assignment_indexes=(1,), *, role="Coordenador"):
    return FunctionalExercise(
        id=FunctionalExerciseId(uuid_for(index)),
        person_id="person-1",
        exercise_type=FunctionalExerciseType(
            "coordenacao",
            "Coordenação Acadêmica",
        ),
        role=FunctionalRole(role),
        context=FunctionalContext(
            organization="Universidade Federal do Pampa",
            unit="Campus São Borja",
            reference="Portaria nº 10/2024 — RSC",
        ),
        period=FunctionalPeriod(date(2024, 1, 1)),
        status=FunctionalExerciseStatus.ACTIVE,
        functional_assignment_evidence_ids=tuple(
            FunctionalAssignmentEvidenceId(uuid_for(100 + item))
            for item in assignment_indexes
        ),
    )


class EvidenceLookupStub:
    def __init__(self, existing):
        self.existing = set(existing)

    def exists(self, evidence_id):
        return evidence_id in self.existing


class SQLiteFunctionalExerciseRepositoryTests(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = TemporaryDirectory()
        self.addCleanup(self.temporary_directory.cleanup)
        self.database_path = (
            Path(self.temporary_directory.name) / "database.db"
        )
        self.assignment_repository = (
            SQLiteFunctionalAssignmentEvidenceRepository(
                self.database_path
            )
        )
        self.repository = SQLiteFunctionalExerciseRepository(
            self.database_path
        )

    def save_assignments(self, *indexes):
        items = tuple(assignment(index) for index in indexes)
        for item in items:
            self.assignment_repository.save(item)
        return items

    def test_round_trip_reconstructs_complete_exercise_and_value_objects(self):
        self.save_assignments(1, 2)
        original = exercise(assignment_indexes=(2, 1))

        self.repository.save(original)
        restored = self.repository.get_by_id(original.id)

        self.assertEqual(restored, original)
        self.assertIsInstance(restored.id, FunctionalExerciseId)
        self.assertIsInstance(
            restored.exercise_type,
            FunctionalExerciseType,
        )
        self.assertIsInstance(restored.role, FunctionalRole)
        self.assertIsInstance(restored.context, FunctionalContext)
        self.assertIsInstance(restored.period, FunctionalPeriod)
        self.assertIsInstance(
            restored.status,
            FunctionalExerciseStatus,
        )
        self.assertTrue(
            all(
                isinstance(item, FunctionalAssignmentEvidenceId)
                for item in restored.functional_assignment_evidence_ids
            )
        )

    def test_provenance_supports_one_two_and_five_references(self):
        self.save_assignments(1, 2, 3, 4, 5)
        exercises = (
            exercise(1, (1,)),
            exercise(2, (1, 2)),
            exercise(3, (5, 4, 3, 2, 1)),
        )

        for item in exercises:
            self.repository.save(item)

        self.assertEqual(self.repository.list_all(), exercises)

    def test_upsert_reorders_abc_to_cab_and_replaces_other_fields(self):
        self.save_assignments(1, 2, 3)
        original = exercise(assignment_indexes=(1, 2, 3))
        replacement = replace(
            original,
            role=FunctionalRole("Coordenador substituto"),
            functional_assignment_evidence_ids=(
                original.functional_assignment_evidence_ids[2],
                original.functional_assignment_evidence_ids[0],
                original.functional_assignment_evidence_ids[1],
            ),
        )

        self.repository.save(original)
        self.repository.save(replacement)

        self.assertEqual(
            self.repository.get_by_id(original.id),
            replacement,
        )
        self.assertEqual(self.repository.list_all(), (replacement,))

    def test_upsert_preserves_exercise_insertion_position(self):
        self.save_assignments(1, 2)
        first = exercise(1, (1,))
        second = exercise(2, (2,))
        replacement = replace(
            first,
            role=FunctionalRole("Papel atualizado"),
        )
        self.repository.save(first)
        self.repository.save(second)

        self.repository.save(replacement)

        self.assertEqual(
            self.repository.list_all(),
            (replacement, second),
        )

    def test_empty_provenance_is_rejected_without_partial_insert(self):
        invalid = exercise(assignment_indexes=())

        with self.assertRaises(FunctionalExercisePersistenceError):
            self.repository.save(invalid)

        self.assertEqual(self.repository.list_all(), ())

    def test_missing_assignment_is_rejected_without_partial_insert(self):
        invalid = exercise(assignment_indexes=(99,))

        with self.assertRaises(
            FunctionalExerciseAssignmentEvidenceNotFoundError
        ):
            self.repository.save(invalid)

        self.assertEqual(self.repository.list_all(), ())

    def test_duplicate_assignment_id_is_rejected_by_unchanged_domain(self):
        identifier = FunctionalAssignmentEvidenceId(uuid_for(101))

        with self.assertRaises(ValueError):
            replace(
                exercise(),
                functional_assignment_evidence_ids=(
                    identifier,
                    identifier,
                ),
            )

    def test_failed_upsert_rolls_back_main_row_and_provenance(self):
        self.save_assignments(1)
        original = exercise(assignment_indexes=(1,))
        self.repository.save(original)
        invalid = replace(
            original,
            role=FunctionalRole("Não deve persistir"),
            functional_assignment_evidence_ids=(
                FunctionalAssignmentEvidenceId(uuid_for(199)),
            ),
        )

        with self.assertRaises(
            FunctionalExerciseAssignmentEvidenceNotFoundError
        ):
            self.repository.save(invalid)

        self.assertEqual(
            self.repository.get_by_id(original.id),
            original,
        )

    def test_reopening_recovers_exercise_and_ordered_provenance(self):
        self.save_assignments(1, 2, 3)
        original = exercise(assignment_indexes=(3, 1, 2))
        self.repository.save(original)

        reopened = SQLiteFunctionalExerciseRepository(
            self.database_path
        )

        self.assertEqual(reopened.get_by_id(original.id), original)
        self.assertEqual(reopened.list_all(), (original,))

    def test_saving_same_exercise_three_times_is_idempotent(self):
        assignments = self.save_assignments(1, 2, 3, 4, 5)
        original = exercise(assignment_indexes=(5, 3, 1, 4, 2))

        self.repository.save(original)
        self.repository.save(original)
        self.repository.save(original)

        reopened = SQLiteFunctionalExerciseRepository(
            self.database_path
        )
        self.assertEqual(reopened.list_all(), (original,))
        self.assertEqual(
            self.assignment_repository.list_all(),
            assignments,
        )
        with ProjectDatabase(self.database_path) as database:
            exercise_count = database.connection.execute(
                "SELECT COUNT(*) FROM rsc_functional_exercises"
            ).fetchone()[0]
            assignment_count = database.connection.execute(
                "SELECT COUNT(*) FROM "
                "rsc_functional_assignment_evidences"
            ).fetchone()[0]
            provenance_count = database.connection.execute(
                "SELECT COUNT(*) FROM "
                "rsc_functional_exercise_assignment_evidences"
            ).fetchone()[0]
        self.assertEqual(exercise_count, 1)
        self.assertEqual(assignment_count, len(assignments))
        self.assertEqual(provenance_count, len(assignments))

    def test_corrupt_provenance_is_reported_as_persistence_error(self):
        self.save_assignments(1)
        original = exercise()
        self.repository.save(original)
        connection = sqlite3.connect(self.database_path)
        try:
            connection.execute("PRAGMA foreign_keys = ON")
            connection.execute(
                "DELETE FROM "
                "rsc_functional_exercise_assignment_evidences "
                "WHERE exercise_id = ?",
                (str(original.id),),
            )
            connection.commit()
        finally:
            connection.close()

        with self.assertRaisesRegex(
            FunctionalExercisePersistenceError,
            "dados inválidos",
        ):
            self.repository.get_by_id(original.id)

    def test_migration_v5_preserves_v4_assignment_data(self):
        existing = self.save_assignments(1)[0]
        connection = sqlite3.connect(self.database_path)
        try:
            connection.execute(
                "DROP INDEX idx_rsc_activity_functional_exercise"
            )
            connection.execute(
                "DROP TABLE rsc_activity_functional_exercises"
            )
            connection.execute(
                "DROP INDEX idx_rsc_activity_assignment_evidence"
            )
            connection.execute(
                "DROP TABLE "
                "rsc_activity_functional_assignment_evidences"
            )
            connection.execute("DROP TABLE rsc_activities")
            connection.execute(
                "DROP INDEX idx_rsc_exercise_assignment_evidence"
            )
            connection.execute(
                "DROP TABLE "
                "rsc_functional_exercise_assignment_evidences"
            )
            connection.execute("DROP TABLE rsc_functional_exercises")
            connection.execute(
                "UPDATE index_state SET value = '4' "
                "WHERE key = 'schema_version'"
            )
            connection.execute("PRAGMA user_version = 4")
            connection.commit()
        finally:
            connection.close()

        initialize_database(self.database_path)

        self.assertEqual(
            self.assignment_repository.get_by_id(existing.id),
            existing,
        )
        self.assertEqual(self.repository.list_all(), ())

    def test_sqlite_composition_provides_both_sqlite_repositories(self):
        repositories = create_sqlite_rsc_repositories(
            self.database_path
        )

        self.assertIsInstance(
            repositories.functional_assignment_evidence,
            SQLiteFunctionalAssignmentEvidenceRepository,
        )
        self.assertIsInstance(
            repositories.functional_exercise,
            SQLiteFunctionalExerciseRepository,
        )

    def test_vertical_flow_survives_new_composition(self):
        source_ids = ("source-a", "source-b")
        lookup = EvidenceLookupStub(source_ids)
        first = create_rsc_project_session(
            lookup,
            create_sqlite_rsc_repositories(self.database_path),
        )
        assignments = tuple(
            first.create_functional_assignment_evidence_service.execute(
                CreateFunctionalAssignmentEvidenceCommand(
                    person_id="person-1",
                    source_evidence_reference=source_id,
                    exercise_type_code="coordenacao",
                    exercise_type_label="Coordenação",
                    role="Coordenador",
                    organization="Universidade",
                    start_date=date(2024, 1, index),
                )
            )
            for index, source_id in enumerate(source_ids, start=1)
        )
        command = CreateFunctionalExerciseCommand(
            person_id="person-1",
            exercise_type_code="coordenacao",
            exercise_type_label="Coordenação",
            role="Coordenador",
            context_organization="Universidade",
            start_date=date(2024, 1, 1),
            functional_assignment_evidence_ids=tuple(
                item.id for item in reversed(assignments)
            ),
        )
        created = first.create_functional_exercise_service.execute(command)

        second = create_rsc_project_session(
            lookup,
            create_sqlite_rsc_repositories(self.database_path),
        )
        listed = second.list_functional_exercises_service.execute()

        self.assertEqual(listed, (created,))
        self.assertEqual(
            listed[0].functional_assignment_evidence_ids,
            tuple(item.id for item in reversed(assignments)),
        )


if __name__ == "__main__":
    unittest.main()
