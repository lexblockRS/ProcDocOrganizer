"""Contratos neutros e imutáveis para manutenção do índice de pesquisa."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime

from .exceptions import InvalidIndexDocumentError


def _non_negative(value: int, field_name: str) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"{field_name} deve ser um inteiro não negativo.")


@dataclass(frozen=True)
class SearchIndexPage:
    page_number: int
    text: str

    def __post_init__(self) -> None:
        if (
            isinstance(self.page_number, bool)
            or not isinstance(self.page_number, int)
            or self.page_number < 1
        ):
            raise InvalidIndexDocumentError(
                "page_number deve ser um inteiro a partir de 1."
            )
        if not isinstance(self.text, str):
            raise InvalidIndexDocumentError("text deve ser texto.")


@dataclass(frozen=True)
class SearchIndexDocument:
    document_identity: str
    document_name: str
    pages: tuple[SearchIndexPage, ...]
    document_type: str | None = None
    document_date: date | None = None

    def __post_init__(self) -> None:
        identity = (
            self.document_identity.strip()
            if isinstance(self.document_identity, str)
            else ""
        )
        name = self.document_name.strip() if isinstance(self.document_name, str) else ""
        if not identity:
            raise InvalidIndexDocumentError(
                "document_identity deve ser um texto não vazio."
            )
        if not name:
            raise InvalidIndexDocumentError(
                "document_name deve ser um texto não vazio."
            )
        try:
            pages = tuple(self.pages)
        except TypeError as exc:
            raise InvalidIndexDocumentError(
                "pages deve ser uma sequência de SearchIndexPage."
            ) from exc
        if any(not isinstance(page, SearchIndexPage) for page in pages):
            raise InvalidIndexDocumentError(
                "pages deve conter apenas SearchIndexPage."
            )
        numbers = [page.page_number for page in pages]
        if len(numbers) != len(set(numbers)):
            raise InvalidIndexDocumentError("Páginas duplicadas não são permitidas.")
        if self.document_type is not None and not isinstance(
            self.document_type, str
        ):
            raise InvalidIndexDocumentError("document_type deve ser texto ou None.")
        if self.document_date is not None and (
            not isinstance(self.document_date, date)
            or isinstance(self.document_date, datetime)
        ):
            raise InvalidIndexDocumentError("document_date deve ser date ou None.")
        object.__setattr__(self, "document_identity", identity)
        object.__setattr__(self, "document_name", name)
        object.__setattr__(self, "pages", tuple(sorted(
            pages, key=lambda page: page.page_number
        )))
        if self.document_type is not None:
            normalized_type = self.document_type.strip()
            object.__setattr__(
                self, "document_type", normalized_type or None
            )


@dataclass(frozen=True)
class IndexMaintenanceIssue:
    code: str
    message: str
    document_identity: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.code, str) or not self.code.strip():
            raise ValueError("code deve ser um texto não vazio.")
        if not isinstance(self.message, str) or not self.message.strip():
            raise ValueError("message deve ser um texto não vazio.")
        object.__setattr__(self, "code", self.code.strip())
        object.__setattr__(self, "message", self.message.strip())
        if self.document_identity is not None:
            if not isinstance(self.document_identity, str):
                raise ValueError("document_identity deve ser texto ou None.")
            identity = self.document_identity.strip()
            object.__setattr__(self, "document_identity", identity or None)


@dataclass(frozen=True)
class IndexRebuildReport:
    scanned_source_documents: int
    indexed_documents: int
    indexed_pages: int
    issues: tuple[IndexMaintenanceIssue, ...] = ()

    def __post_init__(self) -> None:
        for field_name in (
            "scanned_source_documents", "indexed_documents", "indexed_pages"
        ):
            _non_negative(getattr(self, field_name), field_name)
        issues = tuple(self.issues)
        if any(not isinstance(issue, IndexMaintenanceIssue) for issue in issues):
            raise TypeError("issues deve conter apenas IndexMaintenanceIssue.")
        if self.indexed_documents > self.scanned_source_documents:
            raise ValueError("indexed_documents não pode exceder documentos lidos.")
        object.__setattr__(self, "issues", issues)


@dataclass(frozen=True)
class IndexReconcileReport:
    scanned_source_documents: int
    scanned_index_documents: int
    inserted: int = 0
    updated: int = 0
    removed: int = 0
    unchanged: int = 0
    failed: int = 0
    issues: tuple[IndexMaintenanceIssue, ...] = ()

    def __post_init__(self) -> None:
        for field_name in (
            "scanned_source_documents", "scanned_index_documents", "inserted",
            "updated", "removed", "unchanged", "failed",
        ):
            _non_negative(getattr(self, field_name), field_name)
        issues = tuple(self.issues)
        if any(not isinstance(issue, IndexMaintenanceIssue) for issue in issues):
            raise TypeError("issues deve conter apenas IndexMaintenanceIssue.")
        if self.inserted + self.updated + self.unchanged + self.failed != (
            self.scanned_source_documents
        ):
            raise ValueError("Contadores da fonte são incoerentes.")
        if self.removed > self.scanned_index_documents:
            raise ValueError("removed não pode exceder documentos do índice.")
        object.__setattr__(self, "issues", issues)


@dataclass(frozen=True)
class SearchIndexStatus:
    available: bool
    schema_valid: bool
    document_count: int | None = None
    page_count: int | None = None
    last_rebuild_at: datetime | None = None
    last_reconcile_at: datetime | None = None
    issues: tuple[IndexMaintenanceIssue, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.available, bool) or not isinstance(
            self.schema_valid, bool
        ):
            raise TypeError("available e schema_valid devem ser booleanos.")
        for field_name in ("document_count", "page_count"):
            value = getattr(self, field_name)
            if value is not None:
                _non_negative(value, field_name)
        for field_name in ("last_rebuild_at", "last_reconcile_at"):
            value = getattr(self, field_name)
            if value is not None and not isinstance(value, datetime):
                raise TypeError(f"{field_name} deve ser datetime ou None.")
        issues = tuple(self.issues)
        if any(not isinstance(issue, IndexMaintenanceIssue) for issue in issues):
            raise TypeError("issues deve conter apenas IndexMaintenanceIssue.")
        object.__setattr__(self, "issues", issues)
