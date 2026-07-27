"""Coordena o Documents Workspace sem infraestrutura ou navegação."""

import logging

from contracts import DocumentNavigationRequest
from models import EvidenceSourceCandidate
from services.document_service import (
    DocumentNotFoundError,
    DocumentPageNotFoundError,
)

logger = logging.getLogger(__name__)


class DocumentsController:
    NAVIGATION_ERROR_MESSAGE = (
        "Não foi possível localizar o documento solicitado."
    )
    PAGE_NAVIGATION_ERROR_MESSAGE = (
        "Não foi possível localizar a página solicitada."
    )
    def __init__(
        self, workspace, document_service=None, evidence_source_requested=None,
        document_remove_requested=None,
    ):
        self.workspace = workspace
        self.service = document_service
        self.evidence_source_requested = evidence_source_requested
        self.document_remove_requested = document_remove_requested
        self.catalog = ()
        self.selected_identity = None
        self.selected_page_number = None
        workspace.document_selected.connect(self.select_document)
        workspace.page_selected.connect(self.select_page)
        if hasattr(workspace, "create_evidence_requested"):
            workspace.create_evidence_requested.connect(
                self.request_create_evidence
            )
        if hasattr(workspace, "remove_requested"):
            workspace.remove_requested.connect(self.request_remove_document)

    def request_remove_document(self) -> bool:
        if (
            self.document_remove_requested is None
            or self.selected_identity is None
        ):
            return False
        return bool(
            self.document_remove_requested(self.selected_identity)
        )

    def set_evidence_source_requested(self, callback) -> None:
        self.evidence_source_requested = callback

    def request_create_evidence(self) -> bool:
        """Produz um candidato neutro a partir da seleção documental."""
        if (
            self.evidence_source_requested is None
            or self.selected_identity is None
            or self.workspace.details is None
        ):
            return False
        page = self.workspace.current_page
        try:
            candidate = EvidenceSourceCandidate(
                document_identity=self.selected_identity,
                document_name=self.workspace.details.summary.name,
                page_number=getattr(page, "page_number", None),
                source_snippet=getattr(page, "text", ""),
            )
            return bool(self.evidence_source_requested(candidate))
        except (AttributeError, TypeError, ValueError):
            return False

    def set_service(self, service) -> None:
        self.service = service
        self.clear()

    def load(self) -> bool:
        if self.service is None:
            self.workspace.set_state("no_project")
            return False
        previous_identity = self.selected_identity
        previous_page = self.selected_page_number
        self.workspace.set_state("loading")
        try:
            catalog = tuple(self.service.list_documents())
        except Exception:
            logger.exception("Falha ao carregar catálogo documental.")
            self.workspace.show_message(
                "Não foi possível carregar os documentos do projeto."
            )
            self.workspace.set_state("error")
            return False
        self.catalog = catalog
        self.workspace.set_catalog(catalog)
        self.workspace.set_state("ready" if catalog else "empty")
        identities = {item.identity for item in catalog}
        if previous_identity in identities:
            self.workspace.select_document(previous_identity)
            self.select_document(previous_identity)
            if previous_page is not None:
                page_numbers = {item.page_number for item in self.workspace.pages}
                if previous_page in page_numbers:
                    self.workspace.select_page(previous_page)
                    self.select_page(previous_page)
                else:
                    self.workspace.set_page(None)
        else:
            self.selected_identity = None
            self.selected_page_number = None
            self.workspace.clear_document()
        return True

    def refresh(self) -> bool:
        return self.load()

    def navigate(self, request: DocumentNavigationRequest) -> bool:
        """Resolve e seleciona um documento por contrato neutro."""
        if not isinstance(request, DocumentNavigationRequest):
            self.workspace.show_message(self.NAVIGATION_ERROR_MESSAGE)
            return False
        if self.service is None:
            self.workspace.show_message(self.NAVIGATION_ERROR_MESSAGE)
            return False
        try:
            details = self.service.get_document(request.document_identity)
            pages = self.service.list_pages(request.document_identity)
        except DocumentNotFoundError:
            logger.info(
                "Documento solicitado para navegação não foi encontrado: %s",
                request.document_identity,
            )
            self.workspace.show_message(self.NAVIGATION_ERROR_MESSAGE)
            return False
        except Exception:
            logger.exception("Falha ao resolver navegação documental.")
            self.workspace.show_message(self.NAVIGATION_ERROR_MESSAGE)
            return False

        if not self.workspace.select_document(request.document_identity):
            self.workspace.show_message(self.NAVIGATION_ERROR_MESSAGE)
            return False
        self.selected_identity = request.document_identity
        self.selected_page_number = None
        self.workspace.set_page(None)
        self.workspace.set_details(details)
        self.workspace.set_pages(pages)
        if request.page_number is None:
            self.workspace.show_message("")
            return True

        try:
            page = self.service.get_page(
                request.document_identity, request.page_number
            )
        except DocumentPageNotFoundError:
            logger.info(
                "Página %s não encontrada durante navegação documental.",
                request.page_number,
            )
            self.workspace.show_message(self.PAGE_NAVIGATION_ERROR_MESSAGE)
            return False
        except Exception:
            logger.exception("Falha ao resolver página para navegação.")
            self.workspace.show_message(self.PAGE_NAVIGATION_ERROR_MESSAGE)
            return False

        if not self.workspace.select_page(page.page_number):
            self.workspace.show_message(self.PAGE_NAVIGATION_ERROR_MESSAGE)
            return False
        self.selected_page_number = page.page_number
        self.workspace.set_page(page)
        self.workspace.show_message("")
        return True

    def select_document(self, identity) -> bool:
        if self.service is None or not identity:
            return False
        self.workspace.set_page(None)
        try:
            details = self.service.get_document(identity)
            pages = self.service.list_pages(identity)
        except Exception:
            logger.exception("Falha ao carregar detalhes do documento.")
            self.workspace.show_message(
                "Não foi possível carregar os detalhes deste documento."
            )
            return False
        self.selected_identity = identity
        self.selected_page_number = None
        self.workspace.set_details(details)
        self.workspace.set_pages(pages)
        return True

    def select_page(self, page_number) -> bool:
        if self.service is None or self.selected_identity is None:
            return False
        try:
            page = self.service.get_page(self.selected_identity, page_number)
        except Exception:
            logger.exception("Falha ao carregar página documental.")
            self.workspace.show_message(
                "Não foi possível carregar a página selecionada."
            )
            return False
        self.selected_page_number = page.page_number
        self.workspace.set_page(page)
        return True

    def clear(self) -> None:
        self.catalog = ()
        self.selected_identity = None
        self.selected_page_number = None
        self.workspace.clear()
