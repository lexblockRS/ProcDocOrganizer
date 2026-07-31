"""Adaptador SQLite da porta de persistência de evidências."""

from __future__ import annotations

from pathlib import Path
import sqlite3
from typing import Callable

from database import ProjectDatabase
from models import Evidence, Project

from .evidence_repository_errors import (
    DuplicateEvidenceError,
    EvidenceNotFoundError,
    EvidenceRepositoryError,
)


class SQLiteEvidenceRepository:
    """CRUD SQLite responsável somente pela persistência de evidências."""

    # Nome físico legado; a API do adapter expõe somente document_identity.
    COLUMNS = (
        "id", "document_sha256", "page_number", "title", "source_snippet",
        "user_notes", "category", "start_date", "end_date", "created_at",
        "updated_at",
    )

    def __init__(
        self,
        project_or_database: Project | str | Path,
        now_factory: Callable[[], str] | None = None,
        revision_store=None,
    ) -> None:
        self.database_path = (
            project_or_database.project_path / project_or_database.database
            if isinstance(project_or_database, Project)
            else Path(project_or_database)
        )
        self._now_factory = now_factory or Evidence.now
        self._revision_store = revision_store

    def add(self, evidence: Evidence) -> Evidence:
        evidence = self._validate_evidence(evidence)
        try:
            with ProjectDatabase(self.database_path) as database:
                with database.transaction() as connection:
                    if self._exists(connection, evidence.id):
                        raise DuplicateEvidenceError("A evidência já existe.")
                    connection.execute(
                        f"INSERT INTO evidences ({', '.join(self.COLUMNS)}) "
                        f"VALUES ({', '.join('?' for _ in self.COLUMNS)})",
                        self._values(evidence),
                    )
            self._increment_revision("evidence.created")
            return evidence
        except EvidenceRepositoryError:
            raise
        except sqlite3.Error as exc:
            raise EvidenceRepositoryError(f"Falha ao inserir evidência: {exc}") from exc

    def get_by_id(self, evidence_id: str) -> Evidence | None:
        normalized = Evidence._uuid(evidence_id)
        with ProjectDatabase(self.database_path) as database:
            row = database.connection.execute(
                "SELECT * FROM evidences WHERE id = ?", (normalized,)
            ).fetchone()
            return self._from_row(row) if row else None

    def list_all(self) -> list[Evidence]:
        with ProjectDatabase(self.database_path) as database:
            rows = database.connection.execute(
                "SELECT * FROM evidences ORDER BY start_date IS NULL, "
                "start_date, created_at, title COLLATE NOCASE, id"
            ).fetchall()
            return [self._from_row(row) for row in rows]

    def list_by_document(self, document_identity: str) -> list[Evidence]:
        stored_identity = self._storage_identity(document_identity)
        with ProjectDatabase(self.database_path) as database:
            rows = database.connection.execute(
                "SELECT * FROM evidences WHERE document_sha256 = ? "
                "ORDER BY page_number IS NULL, page_number, start_date IS NULL, "
                "start_date, title COLLATE NOCASE, id",
                (stored_identity,),
            ).fetchall()
            return [self._from_row(row) for row in rows]

    def update(self, evidence: Evidence) -> Evidence:
        evidence = self._validate_evidence(evidence)
        try:
            with ProjectDatabase(self.database_path) as database:
                with database.transaction() as connection:
                    existing = connection.execute(
                        "SELECT * FROM evidences WHERE id = ?", (evidence.id,)
                    ).fetchone()
                    if existing is None:
                        raise EvidenceNotFoundError("Evidência não encontrada.")
                    persisted = Evidence(
                        **{
                            **self._domain_values(evidence),
                            "created_at": existing["created_at"],
                            "updated_at": evidence.updated_at,
                        }
                    )
                    assignments = ", ".join(f"{field} = ?" for field in self.COLUMNS[1:])
                    connection.execute(
                        f"UPDATE evidences SET {assignments} WHERE id = ?",
                        self._values(persisted)[1:] + (persisted.id,),
                    )
            self._increment_revision("evidence.updated")
            return persisted
        except EvidenceRepositoryError:
            raise
        except sqlite3.Error as exc:
            raise EvidenceRepositoryError(f"Falha ao atualizar evidência: {exc}") from exc

    def delete(self, evidence_id: str) -> bool:
        normalized = Evidence._uuid(evidence_id)
        with ProjectDatabase(self.database_path) as database:
            with database.transaction() as connection:
                cursor = connection.execute("DELETE FROM evidences WHERE id = ?", (normalized,))
                removed = cursor.rowcount > 0
        if removed:
            self._increment_revision("evidence.deleted")
        return removed

    def _increment_revision(self, reason: str) -> None:
        if self._revision_store is not None:
            self._revision_store.increment(reason)

    def exists(self, evidence_id: str) -> bool:
        normalized = Evidence._uuid(evidence_id)
        with ProjectDatabase(self.database_path) as database:
            return self._exists(database.connection, normalized)

    def count(self) -> int:
        with ProjectDatabase(self.database_path) as database:
            return database.connection.execute("SELECT COUNT(*) FROM evidences").fetchone()[0]

    @staticmethod
    def _validate_evidence(evidence: Evidence) -> Evidence:
        if not isinstance(evidence, Evidence):
            raise TypeError("evidence deve ser uma instância de Evidence.")
        return evidence

    @staticmethod
    def _storage_identity(value: object) -> str:
        normalized = value.strip().lower() if isinstance(value, str) else ""
        if len(normalized) != 64 or any(
            character not in "0123456789abcdef" for character in normalized
        ):
            raise ValueError("A infraestrutura requer um SHA-256 válido.")
        return normalized

    @staticmethod
    def _exists(connection, evidence_id: str) -> bool:
        return connection.execute("SELECT 1 FROM evidences WHERE id = ?", (evidence_id,)).fetchone() is not None

    @classmethod
    def _values(cls, evidence: Evidence) -> tuple:
        return tuple(
            cls._storage_identity(evidence.document_identity)
            if field == "document_sha256"
            else getattr(evidence, field)
            for field in cls.COLUMNS
        )

    @classmethod
    def _from_row(cls, row) -> Evidence:
        return Evidence(**{
            "document_identity": row["document_sha256"],
            **{
                field: row[field]
                for field in cls.COLUMNS
                if field != "document_sha256"
            },
        })

    @staticmethod
    def _domain_values(evidence: Evidence) -> dict:
        return {
            "id": evidence.id,
            "document_identity": evidence.document_identity,
            "page_number": evidence.page_number,
            "title": evidence.title,
            "source_snippet": evidence.source_snippet,
            "user_notes": evidence.user_notes,
            "category": evidence.category,
            "start_date": evidence.start_date,
            "end_date": evidence.end_date,
            "created_at": evidence.created_at,
            "updated_at": evidence.updated_at,
        }
