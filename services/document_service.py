"""Serviço somente leitura para o catálogo e conteúdo processado."""

from __future__ import annotations

import logging
from collections.abc import Callable

from models import (
    DocumentAvailability, DocumentDetails, DocumentPageSummary, DocumentSummary,
)


logger = logging.getLogger(__name__)


class DocumentServiceError(RuntimeError):
    pass


class DocumentNotFoundError(DocumentServiceError):
    pass


class DocumentPageNotFoundError(DocumentServiceError):
    pass


class DocumentService:
    """Compõe Document e ProcessingResult sem consultar o índice SQLite."""

    def __init__(
        self, document_repository, processing_repository,
        availability_resolver: Callable[[object], DocumentAvailability] | None = None,
    ):
        self.document_repository = document_repository
        self.processing_repository = processing_repository
        self._availability_resolver = (
            availability_resolver or self._default_availability
        )

    def list_documents(self) -> tuple[DocumentSummary, ...]:
        summaries = [
            self._summary(document, self._safe_result(document))
            for document in self.document_repository.list_documents()
        ]
        return tuple(sorted(
            summaries,
            key=lambda item: (
                item.name.casefold(), item.relative_path.casefold(), item.identity
            ),
        ))

    def get_document(self, identity: str) -> DocumentDetails:
        document = self._find_document(identity)
        result = self._safe_result(document)
        summary = self._summary(document, result)
        return DocumentDetails(
            summary=summary,
            imported_at=document.imported_at,
            processed_at=(result.processed_at if result else document.processed_at),
            text_source=result.text_source if result else None,
            ocr_used=result.ocr_used if result else False,
            processing_error=result.error if result else None,
            metadata=result.metadata if result else {},
            page_count=summary.page_count,
            has_pages=bool(result and result.pages),
        )

    def list_pages(self, identity: str) -> tuple[DocumentPageSummary, ...]:
        document = self._find_document(identity)
        result = self._safe_result(document)
        if result is None or not isinstance(result.pages, list):
            return ()
        pages = [self._page(document, result, page) for page in result.pages]
        return tuple(sorted(pages, key=lambda item: item.page_number))

    def get_page(self, identity: str, page_number: int) -> DocumentPageSummary:
        if isinstance(page_number, bool) or not isinstance(page_number, int):
            raise DocumentPageNotFoundError("Página não encontrada.")
        for page in self.list_pages(identity):
            if page.page_number == page_number:
                return page
        raise DocumentPageNotFoundError("Página não encontrada.")

    def _find_document(self, identity: str):
        for document in self.document_repository.list_documents():
            if self.identity_for(document) == identity:
                return document
        raise DocumentNotFoundError("Documento não encontrado.")

    def _safe_result(self, document):
        if not self._valid_sha(document.sha256):
            return None
        try:
            result = self.processing_repository.load(document.sha256)
        except Exception:
            logger.warning(
                "Resultado de processamento ilegível para documento %s.",
                self.identity_for(document), exc_info=True,
            )
            return None
        if result is None or result.document_sha256 != document.sha256:
            return None
        return result

    def _summary(self, document, result) -> DocumentSummary:
        metadata = result.metadata if result and isinstance(result.metadata, dict) else {}
        return DocumentSummary(
            identity=self.identity_for(document),
            sha256=document.sha256,
            name=document.name,
            relative_path=document.relative_path,
            document_type=(
                metadata.get("document_type") or document.document_type
            ),
            document_date=metadata.get("document_date"),
            page_count=result.page_count if result else document.pages,
            processing_status=(
                result.status
                if result else (document.processing_status or document.status)
            ),
            availability=self._availability(document),
            has_processing_result=result is not None,
        )

    def _page(self, document, result, page) -> DocumentPageSummary:
        try:
            number = page["page"]
            text = page["text"]
            if isinstance(number, bool) or not isinstance(number, int) or number < 1:
                raise ValueError
            if not isinstance(text, str):
                raise ValueError
        except (KeyError, TypeError, ValueError) as exc:
            raise DocumentServiceError("Página processada inválida.") from exc
        return DocumentPageSummary(
            document_identity=self.identity_for(document),
            document_sha256=document.sha256,
            page_number=number,
            text=text,
            text_source=result.text_source,
            character_count=len(text),
        )

    def _availability(self, document) -> DocumentAvailability:
        try:
            value = self._availability_resolver(document)
            return value if isinstance(value, DocumentAvailability) else DocumentAvailability(value)
        except Exception:
            logger.warning("Falha ao consultar disponibilidade documental.", exc_info=True)
            return DocumentAvailability.UNKNOWN

    def _default_availability(self, document) -> DocumentAvailability:
        relative_path = document.relative_path
        if not isinstance(relative_path, str) or not relative_path:
            return DocumentAvailability.UNKNOWN
        path = self.document_repository.project.project_path / relative_path
        return (
            DocumentAvailability.AVAILABLE
            if path.is_file() else DocumentAvailability.MISSING
        )

    @classmethod
    def identity_for(cls, document) -> str:
        return document.sha256 if cls._valid_sha(document.sha256) else document.relative_path

    @staticmethod
    def _valid_sha(value) -> bool:
        return (
            isinstance(value, str) and len(value) == 64
            and all(character in "0123456789abcdef" for character in value.lower())
        )
