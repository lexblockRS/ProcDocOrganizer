"""Migrations versionadas do banco de cada projeto."""

import sqlite3

from .schema import (
    MIGRATION_V1_STATEMENTS,
    MIGRATION_V2_STATEMENTS,
    MIGRATION_V3_STATEMENTS,
    MIGRATION_V4_STATEMENTS,
    MIGRATION_V5_STATEMENTS,
    MIGRATION_V6_STATEMENTS,
    MIGRATION_V7_STATEMENTS,
    SUPPORTED_SCHEMA_VERSION,
)


class DatabaseError(RuntimeError):
    """Erro de infraestrutura do banco do projeto."""


class SchemaVersionError(DatabaseError):
    """O banco usa uma versão incompatível do schema."""


class FTS5UnavailableError(DatabaseError):
    """O SQLite em uso não oferece o módulo FTS5 requerido."""


class MigrationError(DatabaseError):
    """Uma migration não pôde ser aplicada integralmente."""


def get_schema_version(connection: sqlite3.Connection) -> int:
    row = connection.execute("PRAGMA user_version").fetchone()
    return int(row[0])


def _apply_migration_v1(connection: sqlite3.Connection) -> None:
    for statement in MIGRATION_V1_STATEMENTS:
        try:
            connection.execute(statement)
        except sqlite3.OperationalError as exc:
            if "fts5" in str(exc).lower():
                raise FTS5UnavailableError(
                    "O SQLite deste ambiente não possui suporte a FTS5. "
                    "O índice textual do ProcDoc Organizer requer FTS5."
                ) from exc
            raise
    connection.execute("PRAGMA user_version = 1")


def _apply_migration_v2(connection: sqlite3.Connection) -> None:
    for statement in MIGRATION_V2_STATEMENTS:
        connection.execute(statement)
    connection.execute("PRAGMA user_version = 2")


def _apply_migration_v3(connection: sqlite3.Connection) -> None:
    for statement in MIGRATION_V3_STATEMENTS:
        connection.execute(statement)
    connection.execute("PRAGMA user_version = 3")


def _apply_migration_v4(connection: sqlite3.Connection) -> None:
    for statement in MIGRATION_V4_STATEMENTS:
        connection.execute(statement)
    connection.execute("PRAGMA user_version = 4")


def _apply_migration_v5(connection: sqlite3.Connection) -> None:
    for statement in MIGRATION_V5_STATEMENTS:
        connection.execute(statement)
    connection.execute("PRAGMA user_version = 5")


def _apply_migration_v6(connection: sqlite3.Connection) -> None:
    for statement in MIGRATION_V6_STATEMENTS:
        connection.execute(statement)
    connection.execute("PRAGMA user_version = 6")


def _apply_migration_v7(connection: sqlite3.Connection) -> None:
    existing_columns = {
        row[1]
        for row in connection.execute(
            "PRAGMA table_info(documents)"
        ).fetchall()
    }
    for statement in MIGRATION_V7_STATEMENTS:
        if statement.startswith("ALTER TABLE documents ADD COLUMN"):
            column = statement.split()[5]
            if column in existing_columns:
                continue
            existing_columns.add(column)
        if statement.startswith("CREATE UNIQUE INDEX"):
            statement = statement.replace(
                "CREATE UNIQUE INDEX",
                "CREATE UNIQUE INDEX IF NOT EXISTS",
                1,
            )
        connection.execute(statement)
    connection.execute("PRAGMA user_version = 7")


def apply_migrations(connection: sqlite3.Connection) -> None:
    """Aplica migrations pendentes em uma transação única."""

    current_version = get_schema_version(connection)
    if current_version > SUPPORTED_SCHEMA_VERSION:
        raise SchemaVersionError(
            f"Versão do banco incompatível: {current_version}. "
            f"Esta aplicação suporta até a versão "
            f"{SUPPORTED_SCHEMA_VERSION}."
        )
    if current_version == SUPPORTED_SCHEMA_VERSION:
        return

    try:
        connection.execute("BEGIN")
        if current_version < 1:
            _apply_migration_v1(connection)
        if current_version < 2:
            _apply_migration_v2(connection)
        if current_version < 3:
            _apply_migration_v3(connection)
        if current_version < 4:
            _apply_migration_v4(connection)
        if current_version < 5:
            _apply_migration_v5(connection)
        if current_version < 6:
            _apply_migration_v6(connection)
        if current_version < 7:
            _apply_migration_v7(connection)
        connection.commit()
    except (FTS5UnavailableError, SchemaVersionError):
        connection.rollback()
        raise
    except sqlite3.Error as exc:
        connection.rollback()
        raise MigrationError(
            f"Falha ao migrar o banco da versão {current_version}: {exc}"
        ) from exc
