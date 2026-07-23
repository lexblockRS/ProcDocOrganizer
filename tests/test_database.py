import sqlite3
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from database import (
    ProjectDatabase,
    FTS5UnavailableError,
    INDEX_VERSION,
    MigrationError,
    SUPPORTED_SCHEMA_VERSION,
    SchemaVersionError,
    get_schema_version,
    initialize_database,
)


class ProjectDatabaseTests(unittest.TestCase):
    def test_creates_current_schema_with_operational_fts5(self):
        with TemporaryDirectory() as temporary_directory:
            database_path = Path(temporary_directory) / "database.db"
            initialize_database(database_path)

            with ProjectDatabase(database_path) as database:
                connection = database.connection
                self.assertEqual(
                    get_schema_version(connection), SUPPORTED_SCHEMA_VERSION
                )
                self.assertEqual(
                    connection.execute("PRAGMA foreign_keys").fetchone()[0], 1
                )
                names = {
                    row["name"]
                    for row in connection.execute(
                        "SELECT name FROM sqlite_master "
                        "WHERE name IN (?, ?, ?, ?, ?)",
                        (
                            "documents", "document_pages",
                            "document_pages_fts", "index_state",
                            "search_index_metadata",
                        ),
                    )
                }
                self.assertEqual(
                    names,
                    {
                        "documents", "document_pages",
                        "document_pages_fts", "index_state",
                        "search_index_metadata",
                    },
                )
                state = dict(
                    connection.execute("SELECT key, value FROM index_state")
                )
                self.assertEqual(
                    state["schema_version"], str(SUPPORTED_SCHEMA_VERSION)
                )
                self.assertEqual(state["index_version"], str(INDEX_VERSION))
                connection.execute(
                    "INSERT INTO document_pages_fts"
                    "(text, document_id, page_number) VALUES (?, ?, ?)",
                    ("Administração", 1, 1),
                )
                match = connection.execute(
                    "SELECT COUNT(*) FROM document_pages_fts "
                    "WHERE document_pages_fts MATCH ?",
                    ("administracao",),
                ).fetchone()[0]
                self.assertEqual(match, 1)

    def test_rejects_schema_newer_than_supported(self):
        with TemporaryDirectory() as temporary_directory:
            database_path = Path(temporary_directory) / "database.db"
            connection = sqlite3.connect(database_path)
            connection.execute(
                f"PRAGMA user_version = {SUPPORTED_SCHEMA_VERSION + 1}"
            )
            connection.close()

            with self.assertRaises(SchemaVersionError):
                initialize_database(database_path)

    def test_migration_failure_rolls_back_schema_integrally(self):
        with TemporaryDirectory() as temporary_directory:
            database_path = Path(temporary_directory) / "database.db"
            statements = (
                "CREATE TABLE partial_table(id INTEGER)",
                "CREATE TABL invalid_statement(id INTEGER)",
            )
            with patch(
                "database.migrations.MIGRATION_V1_STATEMENTS", statements
            ):
                with self.assertRaises(MigrationError):
                    initialize_database(database_path)

            connection = sqlite3.connect(database_path)
            try:
                table = connection.execute(
                    "SELECT name FROM sqlite_master WHERE name = ?",
                    ("partial_table",),
                ).fetchone()
                self.assertIsNone(table)
                self.assertEqual(
                    connection.execute("PRAGMA user_version").fetchone()[0], 0
                )
            finally:
                connection.close()

    def test_fts5_unavailability_has_clear_domain_error_and_rollback(self):
        with TemporaryDirectory() as temporary_directory:
            database_path = Path(temporary_directory) / "database.db"
            unavailable_fts = (
                "CREATE VIRTUAL TABLE probe USING unavailable_fts5(text)",
            )
            with patch(
                "database.migrations.MIGRATION_V1_STATEMENTS",
                unavailable_fts,
            ):
                with self.assertRaisesRegex(
                    FTS5UnavailableError, "requer FTS5"
                ):
                    initialize_database(database_path)

            connection = sqlite3.connect(database_path)
            try:
                self.assertEqual(
                    connection.execute("PRAGMA user_version").fetchone()[0], 0
                )
            finally:
                connection.close()


if __name__ == "__main__":
    unittest.main()
