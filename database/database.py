"""Ciclo de vida e transações do SQLite de um projeto."""

from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path
import sqlite3
from typing import Iterator

from .migrations import DatabaseError, apply_migrations, get_schema_version


class ProjectDatabase:
    """Conexão explícita com o banco pertencente a um projeto."""

    def __init__(self, database_path: str | Path):
        self.database_path = Path(database_path)
        self._connection: sqlite3.Connection | None = None

    @property
    def connection(self) -> sqlite3.Connection:
        if self._connection is None:
            raise DatabaseError("A conexão com o banco não está aberta.")
        return self._connection

    def open(self) -> sqlite3.Connection:
        if self._connection is not None:
            return self._connection
        try:
            self.database_path.parent.mkdir(parents=True, exist_ok=True)
            connection = sqlite3.connect(self.database_path)
            connection.row_factory = sqlite3.Row
            connection.execute("PRAGMA foreign_keys = ON")
            self._connection = connection
            return connection
        except (OSError, sqlite3.Error) as exc:
            raise DatabaseError(
                f"Não foi possível abrir o banco '{self.database_path}': {exc}"
            ) from exc

    def initialize(self) -> sqlite3.Connection:
        connection = self.open()
        try:
            apply_migrations(connection)
            return connection
        except Exception:
            self.close()
            raise

    @contextmanager
    def transaction(self) -> Iterator[sqlite3.Connection]:
        connection = self.connection
        try:
            connection.execute("BEGIN")
            yield connection
            connection.commit()
        except Exception:
            connection.rollback()
            raise

    def close(self) -> None:
        if self._connection is not None:
            self._connection.close()
            self._connection = None

    def __enter__(self) -> "ProjectDatabase":
        self.initialize()
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        self.close()


def initialize_database(database_path: str | Path) -> None:
    with ProjectDatabase(database_path):
        pass


__all__ = ["ProjectDatabase", "get_schema_version", "initialize_database"]
