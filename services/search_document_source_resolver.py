"""Adaptador temporário de disponibilidade baseado na projeção de Search."""

from __future__ import annotations

from pathlib import Path

from database import ProjectDatabase
from models import Project


class SearchDocumentSourceResolver:
    """Consulta a infraestrutura atual sem expô-la aos casos de uso."""

    def __init__(self, project_or_database: Project | str | Path) -> None:
        self.project_path = (
            project_or_database.project_path
            if isinstance(project_or_database, Project)
            else None
        )
        self.database_path = (
            project_or_database.project_path / project_or_database.database
            if isinstance(project_or_database, Project)
            else Path(project_or_database)
        )

    def is_document_available(self, document_identity: str) -> bool:
        stored_identity = self._stored_identity(document_identity)
        if stored_identity is None:
            return False
        with ProjectDatabase(self.database_path) as database:
            row = database.connection.execute(
                "SELECT stored_path FROM documents WHERE sha256 = ?",
                (stored_identity,),
            ).fetchone()
        if row is None:
            return False
        stored_path = row["stored_path"]
        if self.project_path is not None and stored_path:
            return (self.project_path / stored_path).is_file()
        return True

    @staticmethod
    def _stored_identity(value: object) -> str | None:
        normalized = value.strip().lower() if isinstance(value, str) else ""
        if len(normalized) != 64 or any(
            character not in "0123456789abcdef" for character in normalized
        ):
            return None
        return normalized
