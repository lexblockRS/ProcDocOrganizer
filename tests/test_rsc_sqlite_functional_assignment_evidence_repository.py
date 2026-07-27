from dataclasses import replace
from datetime import date
from pathlib import Path
import sqlite3
from tempfile import TemporaryDirectory
import unittest

from applications.rsc.assemblers import (
    FunctionalAssignmentEvidenceAssembler,
)
from applications.rsc.commands import (
    CreateFunctionalAssignmentEvidenceCommand,
)
from applications.rsc.composition import (
    create_rsc_project_session,
    create_sqlite_rsc_repositories,
)
from applications.rsc.models import (
    FunctionalAssignmentEvidence,
    FunctionalAssignmentEvidenceId,
    FunctionalAssignmentEvidenceStatus,
    SourceEvidenceReference,
)
from applications.rsc.ports import (
    DuplicateFunctionalAssignmentEvidenceError,
    FunctionalAssignmentEvidencePersistenceError,
)
from applications.rsc.repositories import (
    SQLiteFunctionalAssignmentEvidenceRepository,
    SQLiteFunctionalExerciseRepository,
)
from applications.rsc.services import FunctionalAssignmentNormalizer
from database import (
    ProjectDatabase,
    SUPPORTED_SCHEMA_VERSION,
    get_schema_version,
    initialize_database,
)


def uuid_for(index):
    return f"10000000-0000-4000-8000-{index:012d}"


def assignment(
    index=1,
    *,
    start_date=date(2024, 1, 2),
    end_date=date(2024, 12, 31),
    unit="Campus São Borja",
    administrative_reference="Portaria nº 10/2024 — RSC",
):
    return FunctionalAssignmentEvidence(
        id=FunctionalAssignmentEvidenceId(uuid_for(index)),
        person_id=f"pessoa-{index}",
        source_evidence_reference=SourceEvidenceReference(
            f"evidence-{index}"
        ),
        exercise_type_code="coordenacao_academica",
        exercise_type_label="Coordenação Acadêmica",
        role="Coordenador(a) — titular",
        organization="Universidade Federal do Pampa",
        start_date=start_date,
        end_date=end_date,
        unit=unit,
        administrative_reference=administrative_reference,
        status=FunctionalAssignmentEvidenceStatus.NORMALIZED,
    )


class EvidenceLookupStub:
    def __init__(self, existing):
        self.existing = set(existing)

    def exists(self, evidence_id):
        return evidence_id in self.existing


class SQLiteFunctionalAssignmentEvidenceRepositoryTests(
    unittest.TestCase
):
    def setUp(self):
        self.temporary_directory = TemporaryDirectory()
        self.addCleanup(self.temporary_directory.cleanup)
        self.database_path = (
            Path(self.temporary_directory.name) / "database.db"
        )
        self.repository = (
            SQLiteFunctionalAssignmentEvidenceRepository(
                self.database_path
            )
        )

    def test_round_trip_preserves_complete_entity_and_value_types(self):
        original = assignment()

        self.repository.save(original)
        restored = self.repository.get_by_id(original.id)

        self.assertEqual(restored, original)
        self.assertIsInstance(
            restored.id,
            FunctionalAssignmentEvidenceId,
        )
        self.assertIsInstance(
            restored.source_evidence_reference,
            SourceEvidenceReference,
        )
        self.assertIsInstance(
            restored.status,
            FunctionalAssignmentEvidenceStatus,
        )
        self.assertIsInstance(restored.start_date, date)
        self.assertIsInstance(restored.end_date, date)

    def test_round_trip_preserves_every_scalar_field_and_unicode(self):
        original = assignment()

        self.repository.save(original)
        restored = self.repository.get_by_id(original.id)

        for field in (
            "id",
            "person_id",
            "source_evidence_reference",
            "exercise_type_code",
            "exercise_type_label",
            "role",
            "organization",
            "start_date",
            "end_date",
            "unit",
            "administrative_reference",
            "status",
        ):
            with self.subTest(field=field):
                self.assertEqual(
                    getattr(restored, field),
                    getattr(original, field),
                )

    def test_round_trip_preserves_optional_none_values(self):
        original = assignment(
            start_date=None,
            end_date=None,
            unit=None,
            administrative_reference=None,
        )

        self.repository.save(original)
        restored = self.repository.get_by_id(original.id)

        self.assertIsNone(restored.start_date)
        self.assertIsNone(restored.end_date)
        self.assertIsNone(restored.unit)
        self.assertIsNone(restored.administrative_reference)

    def test_new_repository_instance_recovers_previous_data(self):
        original = assignment()
        self.repository.save(original)

        reopened = SQLiteFunctionalAssignmentEvidenceRepository(
            self.database_path
        )

        self.assertEqual(reopened.get_by_id(original.id), original)
        self.assertEqual(reopened.list_all(), (original,))

    def test_list_all_uses_explicit_insertion_order(self):
        items = (assignment(3), assignment(1), assignment(2))
        for item in items:
            self.repository.save(item)

        self.assertEqual(self.repository.list_all(), items)

        with ProjectDatabase(self.database_path) as database:
            orders = tuple(
                row["insertion_order"]
                for row in database.connection.execute(
                    "SELECT insertion_order FROM "
                    "rsc_functional_assignment_evidences "
                    "ORDER BY insertion_order"
                )
            )
        self.assertEqual(orders, (1, 2, 3))

    def test_duplicate_is_translated_and_preserves_original(self):
        original = assignment()
        self.repository.save(original)
        duplicate = replace(original, role="Outro papel")

        with self.assertRaises(
            DuplicateFunctionalAssignmentEvidenceError
        ):
            self.repository.save(duplicate)

        self.assertEqual(self.repository.list_all(), (original,))

    def test_schema_initialization_is_idempotent_without_data_loss(self):
        original = assignment()
        self.repository.save(original)

        initialize_database(self.database_path)
        initialize_database(self.database_path)

        self.assertEqual(self.repository.list_all(), (original,))
        with ProjectDatabase(self.database_path) as database:
            self.assertEqual(
                get_schema_version(database.connection),
                SUPPORTED_SCHEMA_VERSION,
            )

    def test_corrupt_date_fails_with_driver_independent_error(self):
        original = assignment(end_date=None)
        self.repository.save(original)
        connection = sqlite3.connect(self.database_path)
        try:
            connection.execute(
                "UPDATE rsc_functional_assignment_evidences "
                "SET start_date = ? WHERE id = ?",
                ("data-inválida", str(original.id)),
            )
            connection.commit()
        finally:
            connection.close()

        with self.assertRaisesRegex(
            FunctionalAssignmentEvidencePersistenceError,
            "dados inválidos",
        ):
            self.repository.get_by_id(original.id)

    def test_two_database_files_remain_isolated(self):
        other = SQLiteFunctionalAssignmentEvidenceRepository(
            Path(self.temporary_directory.name) / "other.db"
        )
        original = assignment()

        self.repository.save(original)

        self.assertEqual(self.repository.list_all(), (original,))
        self.assertEqual(other.list_all(), ())

    def test_schema_contains_expected_rsc_tables(self):
        initialize_database(self.database_path)

        with ProjectDatabase(self.database_path) as database:
            rsc_tables = {
                row["name"]
                for row in database.connection.execute(
                    "SELECT name FROM sqlite_master "
                    "WHERE type = 'table' AND name LIKE 'rsc_%'"
                )
            }

        self.assertEqual(
            rsc_tables,
            {
                "rsc_activities",
                "rsc_activity_functional_assignment_evidences",
                "rsc_activity_functional_exercises",
                "rsc_functional_assignment_evidences",
                "rsc_functional_exercises",
                "rsc_functional_exercise_assignment_evidences",
            },
        )

    def test_sqlite_composition_uses_sqlite_for_exercises(self):
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

    def test_vertical_service_flow_survives_reopening_composition(self):
        source_reference = "host-evidence-id"
        lookup = EvidenceLookupStub((source_reference,))
        first = create_rsc_project_session(
            lookup,
            create_sqlite_rsc_repositories(self.database_path),
        )
        command = CreateFunctionalAssignmentEvidenceCommand(
            person_id="person-1",
            source_evidence_reference=source_reference,
            exercise_type_code="coordenacao",
            exercise_type_label="Coordenação",
            role="Coordenador",
            organization="Universidade",
            start_date=date(2024, 1, 1),
        )

        created = (
            first.create_functional_assignment_evidence_service.execute(
                command
            )
        )
        second = create_rsc_project_session(
            lookup,
            create_sqlite_rsc_repositories(self.database_path),
        )
        listed = (
            second.list_functional_assignment_evidences_service.execute()
        )

        self.assertEqual(listed, (created,))
        self.assertEqual(
            listed[0].source_evidence_reference,
            source_reference,
        )
        self.assertFalse(
            hasattr(
                second.functional_assignment_evidence_repository
                .list_all()[0],
                "evidence",
            )
        )

    def test_serialization_helpers_use_iso_dates(self):
        original = assignment()

        row = self.repository._to_row(original)

        self.assertIn("2024-01-02", row)
        self.assertIn("2024-12-31", row)

    def test_existing_empty_database_receives_schema(self):
        sqlite3.connect(self.database_path).close()

        self.assertEqual(self.repository.list_all(), ())

        with ProjectDatabase(self.database_path) as database:
            table = database.connection.execute(
                "SELECT name FROM sqlite_master WHERE name = ?",
                ("rsc_functional_assignment_evidences",),
            ).fetchone()
        self.assertIsNotNone(table)

    def test_version_three_database_migrates_without_host_data_loss(self):
        initialize_database(self.database_path)
        connection = sqlite3.connect(self.database_path)
        try:
            connection.execute(
                "INSERT INTO index_state(key, value) VALUES (?, ?)",
                ("host-preserved-probe", "preservado"),
            )
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
            connection.execute(
                "DROP TABLE rsc_functional_exercises"
            )
            connection.execute(
                "DROP INDEX idx_rsc_assignment_evidences_source"
            )
            connection.execute(
                "DROP TABLE rsc_functional_assignment_evidences"
            )
            connection.execute(
                "UPDATE index_state SET value = '3' "
                "WHERE key = 'schema_version'"
            )
            connection.execute("PRAGMA user_version = 3")
            connection.commit()
        finally:
            connection.close()

        initialize_database(self.database_path)

        with ProjectDatabase(self.database_path) as database:
            preserved = database.connection.execute(
                "SELECT value FROM index_state WHERE key = ?",
                ("host-preserved-probe",),
            ).fetchone()["value"]
            table = database.connection.execute(
                "SELECT name FROM sqlite_master WHERE name = ?",
                ("rsc_functional_assignment_evidences",),
            ).fetchone()
        self.assertEqual(preserved, "preservado")
        self.assertIsNotNone(table)


class SQLiteAssignmentAssemblerCompatibilityTests(unittest.TestCase):
    def test_existing_assembler_and_normalizer_need_no_changes(self):
        raw = FunctionalAssignmentEvidenceAssembler().assemble(
            CreateFunctionalAssignmentEvidenceCommand(
                person_id="person-1",
                source_evidence_reference="evidence-1",
                exercise_type_code="coordenacao",
                exercise_type_label="Coordenação",
                role="Coordenador",
                organization="Universidade",
            )
        )

        normalized = FunctionalAssignmentNormalizer().normalize(raw)

        self.assertIs(
            normalized.status,
            FunctionalAssignmentEvidenceStatus.NORMALIZED,
        )


if __name__ == "__main__":
    unittest.main()
