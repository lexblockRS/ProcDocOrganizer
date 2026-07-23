"""Adaptador temporário de disponibilidade baseado na projeção de Search."""

from __future__ import annotations

from pathlib import Path

from database import ProjectDatabase
from models import Project


class SearchDocumentSourceResolver:
    """Consulta a infraestrutura atual sem expô-la aos casos de uso."""

    def __init__(self, project_or_database: Project | str | Path) -> None:
        self.database_path = (
            project_or_database.project_path / project_or_database.database
            if isinstance(project_or_database, Project)
            else Path(project_or_database)
        )

    def is_document_available(self, document_identity: str) -> bool:
        sha256 = self._sha256(document_identity)
        with ProjectDatabase(self.database_path) as database:
            return database.connection.execute(
                "SELECT 1 FROM documents WHERE sha256 = ?", (sha256,)
            ).fetchone() is not None

    @staticmethod
    def _sha256(value: object) -> str:
        normalized = value.strip().lower() if isinstance(value, str) else ""
        if len(normalized) != 64 or any(
            character not in "0123456789abcdef" for character in normalized
        ):
            raise ValueError("A infraestrutura requer um SHA-256 válido.")
        return normalized
