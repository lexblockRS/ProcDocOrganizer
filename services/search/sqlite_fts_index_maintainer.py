"""Adaptador de escrita e manutenção da projeção SQLite FTS5."""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime
import hashlib
import json
from pathlib import Path
import sqlite3

from database import DatabaseError, ProjectDatabase

from .exceptions import (
    InvalidIndexDocumentError,
    SearchIndexRebuildError,
    SearchIndexSourceError,
    SearchIndexWriteError,
)
from .maintenance_contracts import (
    IndexMaintenanceIssue,
    IndexRebuildReport,
    IndexReconcileReport,
    SearchIndexDocument,
    SearchIndexStatus,
)
from .search_index_source import SearchIndexSource


class SqliteFtsIndexMaintainer:
    """Mantém a projeção sem participar do fluxo de consulta."""

    REQUIRED_TABLES = {
        "documents", "document_pages", "document_pages_fts",
        "search_index_documents", "search_index_metadata",
    }

    def __init__(
        self,
        database_path: str | Path,
        now_factory: Callable[[], datetime] | None = None,
    ) -> None:
        self._database_path = Path(database_path)
        self._now_factory = now_factory or datetime.now

    def upsert(self, document: SearchIndexDocument) -> None:
        self._require_document(document)
        try:
            with ProjectDatabase(self._database_path) as database:
                with database.transaction() as connection:
                    self._upsert(connection, document)
        except (InvalidIndexDocumentError, SearchIndexWriteError):
            raise
        except (DatabaseError, sqlite3.Error, OSError) as exc:
            raise SearchIndexWriteError(
                "Não foi possível atualizar o documento no índice."
            ) from exc

    def remove(self, document_identity: str) -> bool:
        identity = self._identity(document_identity)
        try:
            with ProjectDatabase(self._database_path) as database:
                with database.transaction() as connection:
                    return self._remove(connection, identity)
        except InvalidIndexDocumentError:
            raise
        except (DatabaseError, sqlite3.Error, OSError) as exc:
            raise SearchIndexWriteError(
                "Não foi possível remover o documento do índice."
            ) from exc

    def rebuild(self, source: SearchIndexSource) -> IndexRebuildReport:
        try:
            documents = self._read_source(source)
        except SearchIndexSourceError as exc:
            raise SearchIndexRebuildError(
                "A fonte canônica não pôde ser lida; o índice foi preservado."
            ) from exc
        identities = [document.document_identity for document in documents]
        if len(identities) != len(set(identities)):
            raise SearchIndexRebuildError(
                "A fonte canônica contém identidades duplicadas."
            )
        try:
            with ProjectDatabase(self._database_path) as database:
                with database.transaction() as connection:
                    self._clear(connection)
                    pages = sum(
                        self._upsert(connection, document)
                        for document in documents
                    )
                    self._set_metadata(
                        connection, "last_rebuild_at", self._timestamp()
                    )
            return IndexRebuildReport(
                scanned_source_documents=len(documents),
                indexed_documents=len(documents),
                indexed_pages=pages,
            )
        except SearchIndexRebuildError:
            raise
        except Exception as exc:
            raise SearchIndexRebuildError(
                "A reconstrução falhou; o índice anterior foi preservado."
            ) from exc

    def reconcile(self, source: SearchIndexSource) -> IndexReconcileReport:
        documents = self._read_source(source)
        source_by_identity = {
            document.document_identity: document for document in documents
        }
        if len(source_by_identity) != len(documents):
            raise SearchIndexSourceError(
                "A fonte canônica contém identidades duplicadas."
            )
        index_fingerprints = self._index_fingerprints()
        inserted = updated = unchanged = failed = removed = 0
        issues: list[IndexMaintenanceIssue] = []

        for identity in sorted(source_by_identity):
            document = source_by_identity[identity]
            fingerprint = self.fingerprint(document)
            previous = index_fingerprints.get(identity)
            if previous == fingerprint:
                unchanged += 1
                continue
            try:
                self.upsert(document)
            except SearchIndexWriteError:
                failed += 1
                issues.append(IndexMaintenanceIssue(
                    code="document_write_failed",
                    message="O documento não pôde ser reconciliado.",
                    document_identity=identity,
                ))
            else:
                if identity in index_fingerprints:
                    updated += 1
                else:
                    inserted += 1

        for identity in sorted(set(index_fingerprints) - set(source_by_identity)):
            try:
                if self.remove(identity):
                    removed += 1
            except SearchIndexWriteError:
                issues.append(IndexMaintenanceIssue(
                    code="orphan_remove_failed",
                    message="O documento órfão não pôde ser removido.",
                    document_identity=identity,
                ))

        try:
            with ProjectDatabase(self._database_path) as database:
                with database.transaction() as connection:
                    self._set_metadata(
                        connection, "last_reconcile_at", self._timestamp()
                    )
        except (DatabaseError, sqlite3.Error) as exc:
            raise SearchIndexWriteError(
                "A reconciliação terminou, mas seus metadados não foram salvos."
            ) from exc

        return IndexReconcileReport(
            scanned_source_documents=len(documents),
            scanned_index_documents=len(index_fingerprints),
            inserted=inserted,
            updated=updated,
            removed=removed,
            unchanged=unchanged,
            failed=failed,
            issues=tuple(issues),
        )

    def inspect(self) -> SearchIndexStatus:
        if not self._database_path.is_file():
            return SearchIndexStatus(
                available=False,
                schema_valid=False,
                issues=(IndexMaintenanceIssue(
                    "index_missing", "O índice de pesquisa não existe."
                ),),
            )
        try:
            connection = sqlite3.connect(
                f"{self._database_path.resolve().as_uri()}?mode=ro",
                uri=True,
                timeout=5.0,
            )
            connection.row_factory = sqlite3.Row
        except sqlite3.Error:
            return SearchIndexStatus(
                available=False,
                schema_valid=False,
                issues=(IndexMaintenanceIssue(
                    "index_unavailable", "O índice de pesquisa está inacessível."
                ),),
            )
        try:
            integrity = connection.execute("PRAGMA integrity_check").fetchone()[0]
            if integrity != "ok":
                return self._invalid_status(
                    "integrity_failed", "A integridade do índice é inválida."
                )
            tables = {
                row[0] for row in connection.execute(
                    "SELECT name FROM sqlite_master "
                    "WHERE type IN ('table', 'view')"
                )
            }
            if not self.REQUIRED_TABLES.issubset(tables):
                return self._invalid_status(
                    "schema_missing", "O schema de pesquisa está ausente."
                )
            document_columns = {
                row[1] for row in connection.execute(
                    "PRAGMA table_info(documents)"
                )
            }
            if not {
                "id", "sha256", "original_filename", "processing_status",
                "page_count",
            }.issubset(document_columns):
                return self._invalid_status(
                    "schema_invalid", "O schema de pesquisa é incompatível."
                )
            document_count = connection.execute(
                "SELECT COUNT(*) FROM documents"
            ).fetchone()[0]
            page_count = connection.execute(
                "SELECT COUNT(*) FROM document_pages"
            ).fetchone()[0]
            fts_count = connection.execute(
                "SELECT COUNT(*) FROM document_pages_fts"
            ).fetchone()[0]
            searchable_count = connection.execute(
                "SELECT COUNT(*) FROM document_pages WHERE trim(text) <> ''"
            ).fetchone()[0]
            declared_mismatches = connection.execute(
                """SELECT COUNT(*) FROM documents AS d
                WHERE d.page_count <> (
                    SELECT COUNT(*) FROM document_pages AS p
                    WHERE p.document_id = d.id
                )"""
            ).fetchone()[0]
            issues: list[IndexMaintenanceIssue] = []
            if fts_count != searchable_count:
                issues.append(IndexMaintenanceIssue(
                    "page_count_mismatch",
                    "A quantidade de páginas textuais é inconsistente.",
                ))
            if declared_mismatches:
                issues.append(IndexMaintenanceIssue(
                    "document_page_count_mismatch",
                    "Há documentos com contagem de páginas inconsistente.",
                ))
            metadata = dict(connection.execute(
                "SELECT key, value FROM search_index_metadata"
            ).fetchall())
            return SearchIndexStatus(
                available=True,
                schema_valid=True,
                document_count=document_count,
                page_count=page_count,
                last_rebuild_at=self._parse_datetime(
                    metadata.get("last_rebuild_at")
                ),
                last_reconcile_at=self._parse_datetime(
                    metadata.get("last_reconcile_at")
                ),
                issues=tuple(issues),
            )
        except sqlite3.DatabaseError:
            return self._invalid_status(
                "schema_invalid", "O banco ou schema de pesquisa é inválido."
            )
        finally:
            connection.close()

    @staticmethod
    def fingerprint(document: SearchIndexDocument) -> str:
        payload = {
            "document_identity": document.document_identity,
            "document_name": document.document_name,
            "document_type": document.document_type,
            "document_date": (
                document.document_date.isoformat()
                if document.document_date is not None else None
            ),
            "pages": [
                {"page_number": page.page_number, "text": page.text}
                for page in document.pages
            ],
        }
        serialized = json.dumps(
            payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")
        )
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()

    def _upsert(
        self, connection: sqlite3.Connection, document: SearchIndexDocument
    ) -> int:
        timestamp = self._timestamp()
        fingerprint = self.fingerprint(document)
        connection.execute(
            """INSERT INTO documents (
                sha256, original_filename, processing_status, page_count,
                document_type, document_date, indexed_at, created_at,
                updated_at
            ) VALUES (?, ?, 'processed', ?, ?, ?, ?, ?, ?)
            ON CONFLICT(sha256) DO UPDATE SET
                original_filename=excluded.original_filename,
                processing_status='processed',
                page_count=excluded.page_count,
                document_type=excluded.document_type,
                document_date=excluded.document_date,
                indexed_at=excluded.indexed_at,
                updated_at=excluded.updated_at""",
            (
                document.document_identity, document.document_name,
                len(document.pages), document.document_type,
                document.document_date.isoformat()
                if document.document_date is not None else None,
                timestamp, timestamp, timestamp,
            ),
        )
        document_id = connection.execute(
            "SELECT id FROM documents WHERE sha256 = ?",
            (document.document_identity,),
        ).fetchone()[0]
        connection.execute(
            "DELETE FROM document_pages_fts WHERE document_id = ?",
            (document_id,),
        )
        connection.execute(
            "DELETE FROM document_pages WHERE document_id = ?", (document_id,)
        )
        searchable_pages = 0
        for page in document.pages:
            text = page.text.replace("\x00", "")
            connection.execute(
                "INSERT INTO document_pages(document_id, page_number, text) "
                "VALUES (?, ?, ?)",
                (document_id, page.page_number, text),
            )
            if text.strip():
                connection.execute(
                    "INSERT INTO document_pages_fts"
                    "(text, document_id, page_number) VALUES (?, ?, ?)",
                    (text, document_id, page.page_number),
                )
                searchable_pages += 1
        connection.execute(
            """INSERT INTO search_index_documents(
                document_identity, fingerprint, page_count, indexed_at
            ) VALUES (?, ?, ?, ?)
            ON CONFLICT(document_identity) DO UPDATE SET
                fingerprint=excluded.fingerprint,
                page_count=excluded.page_count,
                indexed_at=excluded.indexed_at""",
            (
                document.document_identity, fingerprint,
                len(document.pages), timestamp,
            ),
        )
        return searchable_pages

    @staticmethod
    def _remove(connection: sqlite3.Connection, identity: str) -> bool:
        row = connection.execute(
            "SELECT id FROM documents WHERE sha256 = ?", (identity,)
        ).fetchone()
        if row is None:
            return False
        connection.execute(
            "DELETE FROM document_pages_fts WHERE document_id = ?", (row[0],)
        )
        connection.execute(
            "DELETE FROM search_index_documents WHERE document_identity = ?",
            (identity,),
        )
        connection.execute("DELETE FROM documents WHERE id = ?", (row[0],))
        return True

    @staticmethod
    def _clear(connection: sqlite3.Connection) -> None:
        connection.execute("DELETE FROM document_pages_fts")
        connection.execute("DELETE FROM search_index_documents")
        connection.execute("DELETE FROM documents")

    def _index_fingerprints(self) -> dict[str, str | None]:
        try:
            with ProjectDatabase(self._database_path) as database:
                return {
                    str(row["sha256"]): row["fingerprint"]
                    for row in database.connection.execute(
                        """SELECT d.sha256, m.fingerprint
                        FROM documents AS d
                        LEFT JOIN search_index_documents AS m
                            ON m.document_identity = d.sha256"""
                    )
                }
        except (DatabaseError, sqlite3.Error) as exc:
            raise SearchIndexWriteError(
                "Não foi possível ler o estado atual do índice."
            ) from exc

    @staticmethod
    def _read_source(source: SearchIndexSource) -> tuple[SearchIndexDocument, ...]:
        if not isinstance(source, SearchIndexSource):
            raise TypeError("source deve implementar SearchIndexSource.")
        try:
            documents = tuple(source.iter_documents())
        except Exception as exc:
            raise SearchIndexSourceError(
                "Não foi possível percorrer a fonte canônica."
            ) from exc
        if any(not isinstance(item, SearchIndexDocument) for item in documents):
            raise SearchIndexSourceError(
                "A fonte canônica retornou um documento inválido."
            )
        return tuple(sorted(
            documents, key=lambda document: document.document_identity
        ))

    @staticmethod
    def _require_document(document: SearchIndexDocument) -> None:
        if not isinstance(document, SearchIndexDocument):
            raise InvalidIndexDocumentError(
                "document deve ser um SearchIndexDocument."
            )

    @staticmethod
    def _identity(value: str) -> str:
        identity = value.strip() if isinstance(value, str) else ""
        if not identity:
            raise InvalidIndexDocumentError(
                "document_identity deve ser um texto não vazio."
            )
        return identity

    def _timestamp(self) -> str:
        value = self._now_factory()
        if not isinstance(value, datetime):
            raise TypeError("now_factory deve retornar datetime.")
        return value.isoformat(timespec="seconds")

    @staticmethod
    def _set_metadata(
        connection: sqlite3.Connection, key: str, value: str
    ) -> None:
        connection.execute(
            "INSERT INTO search_index_metadata(key, value) VALUES (?, ?) "
            "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
            (key, value),
        )

    @staticmethod
    def _parse_datetime(value: str | None) -> datetime | None:
        if value is None:
            return None
        try:
            return datetime.fromisoformat(value)
        except ValueError:
            return None

    @staticmethod
    def _invalid_status(code: str, message: str) -> SearchIndexStatus:
        return SearchIndexStatus(
            available=True,
            schema_valid=False,
            issues=(IndexMaintenanceIssue(code, message),),
        )
