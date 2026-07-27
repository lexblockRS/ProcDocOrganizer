from dataclasses import replace
from datetime import date
from pathlib import Path
import sqlite3
from tempfile import TemporaryDirectory
import unittest

from applications.rsc.composition import (
    create_rsc_project_session,
    create_sqlite_rsc_repositories,
)
from applications.rsc.commands import CreateActivityCommand
from applications.rsc.models import (
    Activity,
    ActivityState,
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
    ActivityPersistenceError,
    ActivityRelationNotFoundError,
)
from applications.rsc.repositories import (
    SQLiteActivityRepository,
    SQLiteFunctionalAssignmentEvidenceRepository,
    SQLiteFunctionalExerciseRepository,
)
from database import ProjectDatabase, get_schema_version, initialize_database


def uuid_for(index):
    return f"00000000-0000-4000-8000-{index:012d}"


def evidence(index):
    return FunctionalAssignmentEvidence(
        id=FunctionalAssignmentEvidenceId(uuid_for(100 + index)),
        person_id="person-1",
        source_evidence_reference=SourceEvidenceReference(
            f"source-{index}"
        ),
        exercise_type_code="coordenacao",
        exercise_type_label="Coordenação",
        role="Coordenador",
        organization="Universidade",
        start_date=date(2024, 1, index),
        status=FunctionalAssignmentEvidenceStatus.LINKED,
    )


def exercise(index, evidence_ids):
    return FunctionalExercise(
        id=FunctionalExerciseId(uuid_for(200 + index)),
        person_id="person-1",
        exercise_type=FunctionalExerciseType(
            "coordenacao",
            "Coordenação",
        ),
        role=FunctionalRole("Coordenador"),
        context=FunctionalContext("Universidade"),
        period=FunctionalPeriod(date(2024, 1, index)),
        status=FunctionalExerciseStatus.ACTIVE,
        functional_assignment_evidence_ids=tuple(evidence_ids),
    )


class EvidenceLookupStub:
    def exists(self, evidence_id):
        return True


class SQLiteActivityRepositoryTests(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = TemporaryDirectory()
        self.addCleanup(self.temporary_directory.cleanup)
        self.database_path = (
            Path(self.temporary_directory.name) / "project.db"
        )
        initialize_database(self.database_path)
        self.repository = SQLiteActivityRepository(self.database_path)
        self.evidence_repository = (
            SQLiteFunctionalAssignmentEvidenceRepository(self.database_path)
        )
        self.exercise_repository = SQLiteFunctionalExerciseRepository(
            self.database_path
        )

    def save_dependencies(self, evidence_indexes=(1,), exercise_indexes=(1,)):
        evidences = tuple(evidence(index) for index in evidence_indexes)
        for item in evidences:
            self.evidence_repository.save(item)
        exercises = tuple(
            exercise(index, tuple(item.id for item in evidences))
            for index in exercise_indexes
        )
        for item in exercises:
            self.exercise_repository.save(item)
        return evidences, exercises

    def test_add_and_get_remembered_activity(self):
        original = Activity("activity-1", "Fiscalização")

        self.repository.add(original)

        self.assertEqual(self.repository.get("activity-1"), original)

    def test_get_missing_activity_returns_none(self):
        self.assertIsNone(self.repository.get("missing"))

    def test_list_all_uses_insertion_order_and_save_preserves_it(self):
        first = Activity("activity-b", "Segunda")
        second = Activity("activity-a", "Primeira")
        self.repository.add(first)
        self.repository.add(second)

        self.repository.save(replace(first, description="Atualizada"))

        self.assertEqual(
            tuple(item.activity_id for item in self.repository.list_all()),
            ("activity-b", "activity-a"),
        )

    def test_save_preserves_evolved_state_and_ordered_relations(self):
        evidences, exercises = self.save_dependencies(
            evidence_indexes=(1, 2),
            exercise_indexes=(1, 2),
        )
        original = Activity("activity-1", "Coordenação")
        evolved = replace(
            original,
            state=ActivityState.PROVEN,
            functional_assignment_evidence_ids=tuple(
                item.id for item in reversed(evidences)
            ),
            functional_exercise_ids=tuple(
                item.id for item in reversed(exercises)
            ),
        )
        self.repository.add(original)

        self.repository.save(evolved)

        self.assertEqual(self.repository.get(original.activity_id), evolved)

    def test_save_replaces_relations_atomically(self):
        evidences, exercises = self.save_dependencies(
            evidence_indexes=(1, 2),
            exercise_indexes=(1, 2),
        )
        original = Activity(
            "activity-1",
            "Coordenação",
            ActivityState.PROVEN,
            tuple(item.id for item in evidences),
            tuple(item.id for item in exercises),
        )
        replacement = replace(
            original,
            functional_assignment_evidence_ids=(evidences[1].id,),
            functional_exercise_ids=(exercises[1].id,),
        )
        self.repository.save(original)

        self.repository.save(replacement)

        self.assertEqual(self.repository.get("activity-1"), replacement)
        with ProjectDatabase(self.database_path) as database:
            evidence_count = database.connection.execute(
                "SELECT COUNT(*) FROM "
                "rsc_activity_functional_assignment_evidences"
            ).fetchone()[0]
            exercise_count = database.connection.execute(
                "SELECT COUNT(*) FROM rsc_activity_functional_exercises"
            ).fetchone()[0]
        self.assertEqual((evidence_count, exercise_count), (1, 1))

    def test_missing_relation_rejects_insert(self):
        invalid = Activity(
            "activity-1",
            "Fiscalização",
            ActivityState.PARTIALLY_PROVEN,
            (FunctionalAssignmentEvidenceId(uuid_for(999)),),
        )

        with self.assertRaises(ActivityRelationNotFoundError):
            self.repository.save(invalid)

        self.assertIsNone(self.repository.get("activity-1"))

    def test_failed_update_rolls_back_row_and_relations(self):
        evidences, exercises = self.save_dependencies()
        original = Activity(
            "activity-1",
            "Coordenação",
            ActivityState.PROVEN,
            (evidences[0].id,),
            (exercises[0].id,),
        )
        self.repository.save(original)
        invalid = replace(
            original,
            description="Não deve persistir",
            functional_exercise_ids=(
                FunctionalExerciseId(uuid_for(999)),
            ),
        )

        with self.assertRaises(ActivityRelationNotFoundError):
            self.repository.save(invalid)

        self.assertEqual(self.repository.get("activity-1"), original)

    def test_duplicate_add_is_rejected_and_original_is_preserved(self):
        original = Activity("activity-1", "Original")
        self.repository.add(original)

        with self.assertRaises(ActivityPersistenceError):
            self.repository.add(
                Activity("activity-1", "Substituição indevida")
            )

        self.assertEqual(self.repository.get("activity-1"), original)

    def test_repositories_using_different_databases_are_isolated(self):
        other_path = Path(self.temporary_directory.name) / "other.db"
        other = SQLiteActivityRepository(other_path)
        self.repository.add(Activity("activity-1", "Fiscalização"))

        self.assertEqual(other.list_all(), ())

    def test_reopening_project_restores_state_and_relations(self):
        evidences, exercises = self.save_dependencies()
        expected = Activity(
            "activity-1",
            "Coordenação",
            ActivityState.PROVEN,
            (evidences[0].id,),
            (exercises[0].id,),
        )
        self.repository.save(expected)

        reopened = SQLiteActivityRepository(self.database_path)

        self.assertEqual(reopened.get("activity-1"), expected)

    def test_sqlite_composition_uses_sqlite_activity_repository(self):
        repositories = create_sqlite_rsc_repositories(self.database_path)

        self.assertIsInstance(
            repositories.activity,
            SQLiteActivityRepository,
        )

    def test_session_creation_survives_reopening(self):
        first = create_rsc_project_session(
            EvidenceLookupStub(),
            create_sqlite_rsc_repositories(self.database_path),
        )
        created = first.create_activity_service.execute(
            CreateActivityCommand("Fiscalização")
        )

        second = create_rsc_project_session(
            EvidenceLookupStub(),
            create_sqlite_rsc_repositories(self.database_path),
        )

        self.assertEqual(
            second.activity_repository.get(created.activity_id).description,
            created.description,
        )

    def test_migration_v6_upgrades_old_database_idempotently(self):
        initialize_database(self.database_path)
        connection = sqlite3.connect(self.database_path)
        try:
            for table in (
                "rsc_activity_functional_exercises",
                "rsc_activity_functional_assignment_evidences",
                "rsc_activities",
            ):
                connection.execute(f"DROP TABLE {table}")
            connection.execute(
                "UPDATE index_state SET value = '5' "
                "WHERE key = 'schema_version'"
            )
            connection.execute("PRAGMA user_version = 5")
            connection.commit()
        finally:
            connection.close()

        initialize_database(self.database_path)
        initialize_database(self.database_path)

        with ProjectDatabase(self.database_path) as database:
            self.assertEqual(get_schema_version(database.connection), 7)
            tables = {
                row[0]
                for row in database.connection.execute(
                    "SELECT name FROM sqlite_master WHERE type = 'table'"
                )
            }
        self.assertIn("rsc_activities", tables)


if __name__ == "__main__":
    unittest.main()
