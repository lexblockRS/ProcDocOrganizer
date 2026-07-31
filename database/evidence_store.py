"""Persistência SQLite específica de Evidence e Document."""

from __future__ import annotations

import json
from pathlib import Path
import sqlite3
from typing import TYPE_CHECKING

from .database import initialize_database

if TYPE_CHECKING:
    from platform_sdk.evidence import Evidence


class EvidencePersistenceError(RuntimeError):
    """Falha ao persistir ou reidratar Evidence."""


class EvidenceNotFoundError(EvidencePersistenceError):
    """A Evidence solicitada não existe."""


class SQLiteEvidenceStore:
    """Store direto, sem ORM ou repository genérico."""

    def __init__(self, database_path: str | Path) -> None:
        self.database_path = Path(database_path)
        initialize_database(self.database_path)
        self._connection = sqlite3.connect(self.database_path)
        self._connection.row_factory = sqlite3.Row
        self._connection.execute("PRAGMA foreign_keys = ON")

    def save(self, evidence: Evidence) -> None:
        Evidence, _Document, _EvidenceState = _evidence_types()
        if not isinstance(evidence, Evidence):
            raise TypeError("evidence deve ser platform_sdk.Evidence.")
        try:
            with self._connection:
                self._connection.execute(
                    """
                    INSERT INTO platform_evidences (
                        evidence_id, project_id, title, description,
                        created_at, updated_at, state, metadata_json
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(evidence_id) DO UPDATE SET
                        project_id = excluded.project_id,
                        title = excluded.title,
                        description = excluded.description,
                        created_at = excluded.created_at,
                        updated_at = excluded.updated_at,
                        state = excluded.state,
                        metadata_json = excluded.metadata_json
                    """,
                    (
                        evidence.evidence_id,
                        evidence.project_id,
                        evidence.title,
                        evidence.description,
                        evidence.created_at.isoformat(),
                        evidence.updated_at.isoformat(),
                        evidence.state.value,
                        _metadata_to_json(evidence.metadata),
                    ),
                )
                self._connection.execute(
                    "DELETE FROM platform_evidence_documents "
                    "WHERE evidence_id = ?",
                    (evidence.evidence_id,),
                )
                for ordinal, document in enumerate(evidence.documents):
                    self._connection.execute(
                        """
                        INSERT INTO platform_documents (
                            document_id, name, relative_path,
                            document_type, sha256, size
                        )
                        VALUES (?, ?, ?, ?, ?, ?)
                        ON CONFLICT(document_id) DO UPDATE SET
                            name = excluded.name,
                            relative_path = excluded.relative_path,
                            document_type = excluded.document_type,
                            sha256 = excluded.sha256,
                            size = excluded.size
                        """,
                        (
                            document.document_id,
                            document.name,
                            document.relative_path,
                            document.document_type,
                            document.sha256,
                            document.size,
                        ),
                    )
                    self._connection.execute(
                        """
                        INSERT INTO platform_evidence_documents (
                            evidence_id, document_id, ordinal
                        )
                        VALUES (?, ?, ?)
                        """,
                        (
                            evidence.evidence_id,
                            document.document_id,
                            ordinal,
                        ),
                    )
                self._delete_orphan_documents()
        except sqlite3.Error as exc:
            raise EvidencePersistenceError(
                "Não foi possível salvar a Evidence."
            ) from exc

    def get(self, evidence_id: str) -> Evidence:
        normalized = _required_text(evidence_id, "evidence_id")
        try:
            row = self._connection.execute(
                "SELECT * FROM platform_evidences WHERE evidence_id = ?",
                (normalized,),
            ).fetchone()
            if row is None:
                raise EvidenceNotFoundError(
                    f"Evidence não encontrada: {normalized}."
                )
            document_rows = self._connection.execute(
                """
                SELECT d.*
                FROM platform_documents AS d
                JOIN platform_evidence_documents AS relation
                  ON relation.document_id = d.document_id
                WHERE relation.evidence_id = ?
                ORDER BY relation.ordinal
                """,
                (normalized,),
            ).fetchall()
        except EvidenceNotFoundError:
            raise
        except sqlite3.Error as exc:
            raise EvidencePersistenceError(
                "Não foi possível abrir a Evidence."
            ) from exc
        try:
            from datetime import datetime

            Evidence, Document, EvidenceState = _evidence_types()
            return Evidence(
                evidence_id=row["evidence_id"],
                project_id=row["project_id"],
                title=row["title"],
                description=row["description"],
                created_at=datetime.fromisoformat(row["created_at"]),
                updated_at=datetime.fromisoformat(row["updated_at"]),
                state=EvidenceState(row["state"]),
                metadata=_metadata_from_json(row["metadata_json"]),
                documents=tuple(
                    Document(
                        document_id=item["document_id"],
                        name=item["name"],
                        relative_path=item["relative_path"],
                        document_type=item["document_type"],
                        sha256=item["sha256"],
                        size=item["size"],
                    )
                    for item in document_rows
                ),
            )
        except (
            KeyError,
            TypeError,
            ValueError,
            json.JSONDecodeError,
        ) as exc:
            raise EvidencePersistenceError(
                "A Evidence persistida contém dados inválidos."
            ) from exc

    def list_for_project(self, project_id: str) -> tuple[Evidence, ...]:
        normalized = _required_text(project_id, "project_id")
        try:
            rows = self._connection.execute(
                """
                SELECT evidence_id
                FROM platform_evidences
                WHERE project_id = ?
                ORDER BY created_at, evidence_id
                """,
                (normalized,),
            ).fetchall()
        except sqlite3.Error as exc:
            raise EvidencePersistenceError(
                "Não foi possível listar Evidences."
            ) from exc
        return tuple(self.get(row["evidence_id"]) for row in rows)

    def delete(self, evidence_id: str) -> None:
        normalized = _required_text(evidence_id, "evidence_id")
        try:
            with self._connection:
                result = self._connection.execute(
                    "DELETE FROM platform_evidences "
                    "WHERE evidence_id = ?",
                    (normalized,),
                )
                if result.rowcount != 1:
                    raise EvidenceNotFoundError(
                        f"Evidence não encontrada: {normalized}."
                    )
                self._delete_orphan_documents()
        except EvidenceNotFoundError:
            raise
        except sqlite3.Error as exc:
            raise EvidencePersistenceError(
                "Não foi possível remover a Evidence."
            ) from exc

    def close(self) -> None:
        if self._connection is not None:
            self._connection.close()
            self._connection = None

    def _delete_orphan_documents(self) -> None:
        self._connection.execute(
            """
            DELETE FROM platform_documents
            WHERE NOT EXISTS (
                SELECT 1
                FROM platform_evidence_documents AS relation
                WHERE relation.document_id =
                      platform_documents.document_id
            )
            """
        )

    def __enter__(self) -> "SQLiteEvidenceStore":
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        self.close()


def _metadata_to_json(metadata) -> str:
    return json.dumps(
        list(metadata), ensure_ascii=False, separators=(",", ":")
    )


def _metadata_from_json(payload: str):
    values = json.loads(payload)
    if not isinstance(values, list) or any(
        not isinstance(item, list) or len(item) != 2 for item in values
    ):
        raise TypeError("metadata persistido é inválido.")
    return tuple((item[0], item[1]) for item in values)


def _required_text(value: object, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} deve ser texto não vazio.")
    return value.strip()


def _evidence_types():
    from platform_sdk.evidence import Document, Evidence, EvidenceState

    return Evidence, Document, EvidenceState


__all__ = [
    "EvidenceNotFoundError",
    "EvidencePersistenceError",
    "SQLiteEvidenceStore",
]
