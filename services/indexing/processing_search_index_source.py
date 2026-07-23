"""Adaptador entre ProcessingRepository e os contratos neutros de indexação."""

from __future__ import annotations

from collections.abc import Callable, Iterable
from datetime import date

from services.processing import ProcessingRepository, ProcessingResult
from services.search import (
    SearchIndexDocument,
    SearchIndexPage,
    SearchIndexSourceError,
)


class ProcessingSearchIndexSource:
    """Converte resultados canônicos sem expor JSON ao maintainer."""

    def __init__(
        self,
        repository: ProcessingRepository,
        name_resolver: Callable[[str], str | None] | None = None,
    ) -> None:
        if not isinstance(repository, ProcessingRepository):
            raise TypeError("repository deve ser um ProcessingRepository.")
        self._repository = repository
        self._name_resolver = name_resolver

    def iter_documents(self) -> Iterable[SearchIndexDocument]:
        try:
            results = sorted(
                self._repository.list_results(),
                key=lambda result: result.document_sha256,
            )
            return tuple(
                self._convert(result)
                for result in results
                if result.status == "processed"
            )
        except SearchIndexSourceError:
            raise
        except Exception as exc:
            raise SearchIndexSourceError(
                "Não foi possível ler a fonte canônica de processamento."
            ) from exc

    def get_document(self, identity: str) -> SearchIndexDocument | None:
        normalized = identity.strip() if isinstance(identity, str) else ""
        if not normalized:
            return None
        try:
            result = self._repository.load(normalized)
        except Exception as exc:
            raise SearchIndexSourceError(
                "Não foi possível ler o documento na fonte canônica."
            ) from exc
        if result is None or result.status != "processed":
            return None
        return self._convert(result)

    def _convert(self, result: ProcessingResult) -> SearchIndexDocument:
        metadata = result.metadata if isinstance(result.metadata, dict) else {}
        resolved_name = (
            self._name_resolver(result.document_sha256)
            if self._name_resolver is not None
            else None
        )
        name = (
            resolved_name
            or self._text(metadata.get("title"))
            or result.document_sha256
        )
        pages = tuple(
            SearchIndexPage(
                page_number=page.get("page"),
                text=page.get("text"),
            )
            for page in result.pages
        )
        return SearchIndexDocument(
            document_identity=result.document_sha256,
            document_name=name,
            document_type=self._text(metadata.get("document_type")),
            document_date=self._date(metadata.get("document_date")),
            pages=pages,
        )

    @staticmethod
    def _text(value: object) -> str | None:
        if not isinstance(value, str):
            return None
        return value.strip() or None

    @staticmethod
    def _date(value: object) -> date | None:
        if not isinstance(value, str) or not value.strip():
            return None
        try:
            return date.fromisoformat(value.strip())
        except ValueError:
            return None
