"""Repository SQLite do acervo documental de um projeto."""

from __future__ import annotations

from pathlib import Path
import sqlite3

from database import ProjectDatabase
from models import (
    Document, DocumentProcessingStatus, DocumentStatus, Project,
)


class DocumentRepository:
    """Persiste o catálogo documental sem executar análise."""

    def __init__(self, project: Project, revision_store=None):
        self.project = project
        self.database_path = project.project_path / project.database
        self._revision_store = revision_store

    def load(self) -> None:
        """Inicializa/migra o banco; mantido para compatibilidade."""
        with ProjectDatabase(self.database_path):
            pass

    def save(self) -> None:
        """Compatibilidade: operações individuais já são transacionais."""

    def create(self, document: Document) -> Document:
        if not isinstance(document, Document):
            raise TypeError("document deve ser Document.")
        try:
            with ProjectDatabase(self.database_path) as database:
                with database.transaction() as connection:
                    connection.execute(
                        """INSERT INTO documents (
                            document_id, sha256, original_filename,
                            stored_path, stored_filename, relative_path,
                            file_size, extension, mime_type, imported_at,
                            status, processing_status, page_count,
                            document_type, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                        self._to_row(document),
                    )
            self._increment_revision("document.created")
            return document
        except sqlite3.IntegrityError as exc:
            raise ValueError(
                "O documento já existe no projeto."
            ) from exc

    def update(self, document: Document) -> None:
        if not isinstance(document, Document):
            raise TypeError("document deve ser Document.")
        with ProjectDatabase(self.database_path) as database:
            with database.transaction() as connection:
                result = connection.execute(
                    """UPDATE documents SET
                        sha256=?, original_filename=?, stored_path=?,
                        stored_filename=?, relative_path=?, file_size=?,
                        extension=?, mime_type=?, imported_at=?, status=?,
                        processing_status=?, page_count=?, document_type=?,
                        updated_at=?
                    WHERE document_id=?""",
                    (
                        document.sha256,
                        document.original_filename,
                        document.relative_path,
                        document.stored_filename,
                        document.relative_path,
                        document.file_size,
                        document.extension,
                        document.mime_type,
                        document.imported_at,
                        (
                            document.status.value
                            if isinstance(document.status, DocumentStatus)
                            else document.status
                        ),
                        (
                            document.processing_status.value
                            if isinstance(
                                document.processing_status,
                                DocumentProcessingStatus,
                            )
                            else document.processing_status
                        ),
                        document.pages,
                        document.document_type,
                        Document.now(),
                        document.id,
                    ),
                )
                if result.rowcount != 1:
                    raise ValueError(
                        f"O documento '{document.name}' não existe no projeto."
                    )
        self._increment_revision("document.updated")

    def delete(self, document_id: str) -> Document | None:
        document = self.find_by_id(document_id)
        if document is None:
            return None
        with ProjectDatabase(self.database_path) as database:
            with database.transaction() as connection:
                row = connection.execute(
                    "SELECT id FROM documents WHERE document_id = ?",
                    (document_id,),
                ).fetchone()
                if row is None:
                    return None
                internal_id = row["id"]
                connection.execute(
                    "DELETE FROM document_pages_fts WHERE document_id = ?",
                    (internal_id,),
                )
                connection.execute(
                    "DELETE FROM document_pages WHERE document_id = ?",
                    (internal_id,),
                )
                connection.execute(
                    "DELETE FROM search_index_documents "
                    "WHERE document_identity = ?",
                    (document.sha256,),
                )
                connection.execute(
                    "DELETE FROM documents WHERE document_id = ?",
                    (document_id,),
                )
        self._increment_revision("document.deleted")
        return document

    def find_by_id(self, document_id: str) -> Document | None:
        return self._find("document_id", document_id)

    def find_by_hash(self, sha256: str) -> Document | None:
        return self._find("sha256", sha256)

    def list_all(self) -> tuple[Document, ...]:
        with ProjectDatabase(self.database_path) as database:
            rows = database.connection.execute(
                "SELECT * FROM documents WHERE document_id IS NOT NULL "
                "ORDER BY imported_at, id"
            ).fetchall()
        return tuple(self._from_row(row) for row in rows)

    def list_documents(self) -> list[Document]:
        return sorted(
            self.list_all(),
            key=lambda document: document.name.lower(),
        )

    def add(self, document: Document) -> None:
        self.create(document)

    def remove(self, document: Document) -> None:
        removed = self.delete(document.id)
        if removed is None:
            raise ValueError(
                f"O documento '{document.name}' não existe no projeto."
            )

    def clear(self) -> None:
        with ProjectDatabase(self.database_path) as database:
            with database.transaction() as connection:
                connection.execute(
                    "DELETE FROM documents WHERE document_id IS NOT NULL"
                )

    def __len__(self) -> int:
        return len(self.list_all())

    def __iter__(self):
        return iter(self.list_all())

    def _find(self, column: str, value: str):
        if not isinstance(value, str) or not value.strip():
            return None
        with ProjectDatabase(self.database_path) as database:
            row = database.connection.execute(
                f"SELECT * FROM documents WHERE {column} = ?",
                (value.strip(),),
            ).fetchone()
        return self._from_row(row) if row is not None else None

    def _increment_revision(self, reason: str) -> None:
        if self._revision_store is not None:
            self._revision_store.increment(reason)

    @staticmethod
    def _to_row(document):
        return (
            document.id,
            document.sha256,
            document.original_filename,
            document.relative_path,
            document.stored_filename,
            document.relative_path,
            document.file_size,
            document.extension,
            document.mime_type,
            document.imported_at,
            (
                document.status.value
                if isinstance(document.status, DocumentStatus)
                else document.status
            ),
            (
                document.processing_status.value
                if isinstance(
                    document.processing_status,
                    DocumentProcessingStatus,
                )
                else document.processing_status
            ),
            document.pages,
            document.document_type,
            document.created_at,
            document.updated_at,
        )

    @staticmethod
    def _from_row(row):
        return Document(
            name=row["original_filename"],
            relative_path=row["relative_path"] or row["stored_path"],
            imported_at=row["imported_at"] or row["created_at"],
            pages=row["page_count"],
            sha256=row["sha256"],
            status=DocumentStatus(row["status"] or "imported"),
            document_type=row["document_type"] or "unknown",
            processing_status=DocumentRepository._processing_status(
                row["processing_status"]
            ),
            id=row["document_id"],
            original_filename=row["original_filename"],
            stored_filename=row["stored_filename"],
            file_size=row["file_size"] or 0,
            extension=row["extension"] or "",
            mime_type=row["mime_type"] or "application/octet-stream",
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    @staticmethod
    def _processing_status(value):
        try:
            return DocumentProcessingStatus(
                value or DocumentProcessingStatus.NOT_PROCESSED
            )
        except ValueError:
            return value
