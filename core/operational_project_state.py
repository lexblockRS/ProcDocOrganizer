"""Identidade e revisão operacionais persistidas por Project ``.pdop``."""

from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from database import ProjectDatabase


class OperationalProjectStateStore:
    """Mantém o pequeno estado operacional no chave-valor existente."""

    PROJECT_ID_KEY = "operational_project_id"
    REVISION_KEY = "operational_revision"

    def __init__(self, database_path: str | Path) -> None:
        self.database_path = Path(database_path)
        self._bootstrap()

    @property
    def project_id(self) -> str:
        return self._read(self.PROJECT_ID_KEY)

    def current(self) -> int:
        return int(self._read(self.REVISION_KEY))

    def increment(self, reason: str) -> int:
        if not isinstance(reason, str) or not reason.strip():
            raise ValueError("reason deve ser texto não vazio.")
        with ProjectDatabase(self.database_path) as database:
            with database.transaction() as connection:
                row = connection.execute(
                    "SELECT value FROM index_state WHERE key = ?",
                    (self.REVISION_KEY,),
                ).fetchone()
                current = int(row["value"] if row is not None else "0")
                revision = current + 1
                connection.execute(
                    "INSERT INTO index_state(key, value) VALUES (?, ?) "
                    "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
                    (self.REVISION_KEY, str(revision)),
                )
        return revision

    def _bootstrap(self) -> None:
        with ProjectDatabase(self.database_path) as database:
            with database.transaction() as connection:
                connection.execute(
                    "INSERT OR IGNORE INTO index_state(key, value) "
                    "VALUES (?, ?)",
                    (self.PROJECT_ID_KEY, str(uuid4())),
                )
                connection.execute(
                    "INSERT OR IGNORE INTO index_state(key, value) "
                    "VALUES (?, '0')",
                    (self.REVISION_KEY,),
                )

    def _read(self, key: str) -> str:
        with ProjectDatabase(self.database_path) as database:
            row = database.connection.execute(
                "SELECT value FROM index_state WHERE key = ?", (key,)
            ).fetchone()
        if row is None:
            raise RuntimeError(f"Estado operacional ausente: {key}.")
        return str(row["value"])


__all__ = ["OperationalProjectStateStore"]
