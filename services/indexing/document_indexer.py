"""Indexa resultados JSON de processamento no SQLite do projeto."""

from __future__ import annotations

from datetime import datetime
import json
from pathlib import Path
import sqlite3
from typing import Callable

from database import DatabaseError, ProjectDatabase
from services.search import (
    SearchIndexDocument,
    SearchIndexPage,
    SearchIndexWriteError,
    SqliteFtsIndexMaintainer,
)

from .indexing_result import IndexingResult, RebuildReport


class IndexingValidationError(ValueError):
    """O JSON não atende ao contrato mínimo de indexação."""


class DocumentIndexer:
    """Mantém o índice de páginas sem depender do processamento ou da UI."""

    SUPPORTED_STATUSES = {"processed", "ocr_required", "failed"}
    METADATA_FIELDS = (
        "title", "document_type", "document_number", "document_date",
        "issuing_organization", "sei_process_number", "sei_code",
    )

    def __init__(
        self,
        database_path: str | Path,
        now_factory: Callable[[], str] | None = None,
    ):
        self.database_path = Path(database_path)
        self._now_factory = now_factory or self._now
        self._maintainer = SqliteFtsIndexMaintainer(
            self.database_path,
            now_factory=lambda: datetime.fromisoformat(self._now_factory()),
        )

    @staticmethod
    def _now() -> str:
        return datetime.now().isoformat(timespec="seconds")

    def index_processing_result(
        self,
        processing_json_path: str | Path,
        original_filename: str | None = None,
        stored_path: str | None = None,
    ) -> IndexingResult:
        json_path = Path(processing_json_path)
        data = self._load_json(json_path)
        validated = self._validate(data, json_path)
        sha256 = validated["document_sha256"]

        if validated["status"] == "processed":
            return self._index_processed_with_maintainer(
                validated, original_filename, stored_path
            )

        try:
            with ProjectDatabase(self.database_path) as database:
                with database.transaction() as connection:
                    existing = connection.execute(
                        "SELECT id FROM documents WHERE sha256 = ?", (sha256,)
                    ).fetchone()
                    document_id = self._upsert_document(
                        connection,
                        validated,
                        original_filename,
                        stored_path,
                    )
                    previous_pages = connection.execute(
                        "SELECT COUNT(*) FROM document_pages "
                        "WHERE document_id = ?",
                        (document_id,),
                    ).fetchone()[0]
                    self._delete_pages(connection, document_id)

                    if validated["status"] == "ocr_required":
                        return IndexingResult(
                            sha256, "skipped", document_id, 0,
                            "Documento requer OCR; índice textual removido.",
                        )
                    return IndexingResult(
                        sha256,
                        "removed" if previous_pages else "skipped",
                        document_id,
                        0,
                        "Processamento falhou; índice textual removido.",
                    )
        except DatabaseError:
            raise
        except sqlite3.Error as exc:
            raise DatabaseError(
                f"Falha transacional ao indexar '{json_path}': {exc}"
            ) from exc

    def remove_document(self, document_sha256: str) -> IndexingResult:
        sha256 = self._validate_sha256(document_sha256, "remoção")
        try:
            with ProjectDatabase(self.database_path) as database:
                row = database.connection.execute(
                    "SELECT id FROM documents WHERE sha256 = ?", (sha256,)
                ).fetchone()
            removed = self._maintainer.remove(sha256)
            if not removed:
                return IndexingResult(
                    sha256, "skipped", None, 0,
                    "Documento não encontrado no índice.",
                )
            return IndexingResult(sha256, "removed", row["id"])
        except (DatabaseError, SearchIndexWriteError, sqlite3.Error) as exc:
            raise DatabaseError(
                f"Falha transacional ao remover '{sha256}'."
            ) from exc

    def _index_processed_with_maintainer(
        self, data: dict, original_filename: str | None, stored_path: str | None
    ) -> IndexingResult:
        sha256 = data["document_sha256"]
        metadata = data["metadata"]
        name = (
            metadata.get("title")
            or self._nullable_string(original_filename)
            or sha256
        )
        document_date = None
        if metadata.get("document_date"):
            try:
                document_date = datetime.strptime(
                    metadata["document_date"], "%Y-%m-%d"
                ).date()
            except ValueError:
                document_date = None
        document = SearchIndexDocument(
            document_identity=sha256,
            document_name=name,
            document_type=metadata.get("document_type"),
            document_date=document_date,
            pages=tuple(
                SearchIndexPage(page["page"], page["text"])
                for page in data["pages"]
            ),
        )
        try:
            with ProjectDatabase(self.database_path) as database:
                existing = database.connection.execute(
                    "SELECT id FROM documents WHERE sha256 = ?", (sha256,)
                ).fetchone()
            self._maintainer.upsert(document)
            with ProjectDatabase(self.database_path) as database:
                with database.transaction() as connection:
                    connection.execute(
                        """UPDATE documents SET
                            original_filename=COALESCE(?, original_filename),
                            stored_path=COALESCE(?, stored_path),
                            title=?, document_number=?,
                            issuing_organization=?, sei_process_number=?,
                            sei_code=?
                        WHERE sha256=?""",
                        (
                            self._nullable_string(original_filename),
                            self._nullable_string(stored_path),
                            metadata.get("title"),
                            metadata.get("document_number"),
                            metadata.get("issuing_organization"),
                            metadata.get("sei_process_number"),
                            metadata.get("sei_code"),
                            sha256,
                        ),
                    )
                    row = connection.execute(
                        "SELECT id FROM documents WHERE sha256 = ?", (sha256,)
                    ).fetchone()
            pages_indexed = sum(
                1 for page in data["pages"] if page["text"].strip()
            )
            return IndexingResult(
                sha256, "updated" if existing else "indexed",
                row["id"], pages_indexed,
            )
        except (DatabaseError, SearchIndexWriteError, sqlite3.Error) as exc:
            raise DatabaseError(
                f"Falha transacional ao indexar '{sha256}'."
            ) from exc

    def is_indexed(self, document_sha256: str) -> bool:
        sha256 = self._validate_sha256(document_sha256, "consulta")
        with ProjectDatabase(self.database_path) as database:
            row = database.connection.execute(
                "SELECT 1 FROM documents "
                "WHERE sha256 = ? AND indexed_at IS NOT NULL",
                (sha256,),
            ).fetchone()
            return row is not None

    def rebuild_incremental(
        self, processing_directory: str | Path
    ) -> RebuildReport:
        return self._rebuild(processing_directory, mode="incremental")

    def rebuild_full(
        self, processing_directory: str | Path
    ) -> RebuildReport:
        """Limpa explicitamente o índice e o recompõe a partir dos JSONs."""

        try:
            with ProjectDatabase(self.database_path) as database:
                with database.transaction() as connection:
                    removed = self._clear_index(connection)
        except DatabaseError:
            raise
        except sqlite3.Error as exc:
            raise DatabaseError(
                f"Falha ao preparar reconstrução completa: {exc}"
            ) from exc

        report = self._rebuild(processing_directory, mode="full")
        report.documents_removed_before_rebuild = removed
        return report

    def _rebuild(
        self, processing_directory: str | Path, mode: str
    ) -> RebuildReport:
        directory = Path(processing_directory)
        files = sorted(directory.glob("*.json"), key=lambda item: item.name)
        report = RebuildReport(mode=mode, total=len(files))
        for json_path in files:
            try:
                report.add_result(self.index_processing_result(json_path))
            except Exception as exc:
                report.add_error(str(json_path), str(exc))
        return report

    @staticmethod
    def _load_json(json_path: Path) -> dict:
        try:
            data = json.loads(json_path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            raise IndexingValidationError(
                f"JSON de processamento inválido '{json_path}': {exc}"
            ) from exc
        if not isinstance(data, dict):
            raise IndexingValidationError(
                f"JSON de processamento inválido '{json_path}': "
                "a raiz deve ser um objeto."
            )
        return data

    def _validate(self, data: dict, json_path: Path) -> dict:
        result = dict(data)
        result["document_sha256"] = self._validate_sha256(
            data.get("document_sha256"), str(json_path)
        )
        status = self._technical_string(data.get("status"))
        if status not in self.SUPPORTED_STATUSES:
            raise IndexingValidationError(
                f"Status desconhecido em '{json_path}': {status!r}."
            )
        result["status"] = status

        page_count = data.get("page_count", 0)
        if (
            isinstance(page_count, bool)
            or not isinstance(page_count, int)
            or page_count < 0
        ):
            raise IndexingValidationError(
                f"page_count inválido em '{json_path}'."
            )
        result["page_count"] = page_count
        result["metadata"] = self._validate_metadata(data.get("metadata", {}))
        result["pages"] = self._validate_pages(
            data.get("pages", []), json_path, status
        )
        if status == "processed" and page_count != len(result["pages"]):
            raise IndexingValidationError(
                f"page_count divergente em '{json_path}': informado "
                f"{page_count}, mas existem {len(result['pages'])} páginas."
            )
        return result

    @staticmethod
    def _validate_sha256(value, operation: str) -> str:
        sha256 = value.strip().lower() if isinstance(value, str) else ""
        if len(sha256) != 64 or any(c not in "0123456789abcdef" for c in sha256):
            raise IndexingValidationError(
                f"SHA-256 inválido durante {operation}."
            )
        return sha256

    @classmethod
    def _validate_metadata(cls, metadata) -> dict:
        if metadata is None:
            metadata = {}
        if not isinstance(metadata, dict):
            raise IndexingValidationError("O campo metadata deve ser um objeto.")
        return {
            field: cls._nullable_string(metadata.get(field))
            for field in cls.METADATA_FIELDS
        }

    @staticmethod
    def _validate_pages(pages, json_path: Path, status: str) -> list[dict]:
        if not isinstance(pages, list):
            raise IndexingValidationError(
                f"O campo pages deve ser uma lista em '{json_path}'."
            )
        validated = []
        seen = set()
        for page in pages:
            if not isinstance(page, dict):
                raise IndexingValidationError(f"Página inválida em '{json_path}'.")
            number = page.get("page")
            text = page.get("text")
            if isinstance(number, bool) or not isinstance(number, int) or number < 1:
                raise IndexingValidationError(
                    f"Número de página inválido em '{json_path}'."
                )
            if number in seen:
                raise IndexingValidationError(
                    f"Página {number} duplicada em '{json_path}'."
                )
            if not isinstance(text, str):
                raise IndexingValidationError(
                    f"Texto da página {number} inválido em '{json_path}'."
                )
            seen.add(number)
            validated.append({"page": number, "text": text})
        if status != "processed":
            return []
        return validated

    @staticmethod
    def _technical_string(value) -> str:
        return value.strip() if isinstance(value, str) else ""

    @staticmethod
    def _nullable_string(value) -> str | None:
        if not isinstance(value, str):
            return None
        normalized = value.strip()
        return normalized or None

    def _upsert_document(
        self, connection, data, original_filename, stored_path
    ) -> int:
        timestamp = self._now_factory()
        indexed_at = timestamp if data["status"] == "processed" else None
        metadata = data["metadata"]
        values = (
            data["document_sha256"], self._nullable_string(original_filename),
            self._nullable_string(stored_path), data["status"],
            data["page_count"], *(metadata[field] for field in self.METADATA_FIELDS),
            indexed_at, timestamp, timestamp,
        )
        connection.execute(
            """INSERT INTO documents (
                sha256, original_filename, stored_path, processing_status,
                page_count, title, document_type, document_number,
                document_date, issuing_organization, sei_process_number,
                sei_code, indexed_at, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(sha256) DO UPDATE SET
                original_filename=COALESCE(
                    excluded.original_filename, documents.original_filename
                ),
                stored_path=COALESCE(excluded.stored_path, documents.stored_path),
                processing_status=excluded.processing_status,
                page_count=excluded.page_count, title=excluded.title,
                document_type=excluded.document_type,
                document_number=excluded.document_number,
                document_date=excluded.document_date,
                issuing_organization=excluded.issuing_organization,
                sei_process_number=excluded.sei_process_number,
                sei_code=excluded.sei_code, indexed_at=excluded.indexed_at,
                updated_at=excluded.updated_at""",
            values,
        )
        # created_at representa a primeira inclusão e não é alterado
        # pelo ON CONFLICT. indexed_at é a última indexação textual
        # bem-sucedida, não o instante em que o documento foi processado.
        row = connection.execute(
            "SELECT id FROM documents WHERE sha256 = ?",
            (data["document_sha256"],),
        ).fetchone()
        return row["id"]

    @staticmethod
    def _delete_pages(connection, document_id: int) -> None:
        connection.execute(
            "DELETE FROM document_pages_fts WHERE document_id = ?",
            (document_id,),
        )
        connection.execute(
            "DELETE FROM document_pages WHERE document_id = ?", (document_id,)
        )

    @staticmethod
    def _clear_index(connection) -> int:
        removed = connection.execute(
            "SELECT COUNT(*) FROM documents"
        ).fetchone()[0]
        connection.execute("DELETE FROM document_pages_fts")
        connection.execute("DELETE FROM documents")
        return removed
