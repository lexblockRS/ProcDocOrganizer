"""Coordena o Documents Workspace sem infraestrutura ou navegação."""

import logging

from contracts import DocumentNavigationRequest
from models import EvidenceSourceCandidate
from presentation import (
    SelectionContext,
    SelectionIdentity,
    SelectionKind,
)
from services.document_service import (
    DocumentNotFoundError,
    DocumentPageNotFoundError,
)

logger = logging.getLogger(__name__)


class DocumentsController:
    NAVIGATION_DOCUMENT_OPENED = "document_opened"
    NAVIGATION_PAGE_MISSING = "page_missing"
    NAVIGATION_FAILED = "failed"
    NAVIGATION_ERROR_MESSAGE = (
        "Não foi possível localizar o documento solicitado."
    )
    PAGE_NAVIGATION_ERROR_MESSAGE = (
        "Não foi possível localizar a página solicitada."
    )
    def __init__(
        self, workspace, document_service=None, evidence_source_requested=None,
        document_remove_requested=None, document_open_requested=None,
        document_ocr_requested=None, selection_store=None,
        document_metadata_update_requested=None,
        confirm_unsaved_metadata=None, notify=None,
    ):
        self.workspace = workspace
        self.service = document_service
        self.evidence_source_requested = evidence_source_requested
        self.document_remove_requested = document_remove_requested
        self.document_open_requested = document_open_requested
        self.document_ocr_requested = document_ocr_requested
        self.selection_store = selection_store
        self.document_metadata_update_requested = (
            document_metadata_update_requested
        )
        self.confirm_unsaved_metadata = (
            confirm_unsaved_metadata or (lambda: "cancel")
        )
        self.notify = notify or (lambda _kind, _message: None)
        self.catalog = ()
        self.selected_identity = None
        self.selected_page_number = None
        self.last_navigation_outcome = None
        workspace.document_selected.connect(self.select_document)
        workspace.page_selected.connect(self.select_page)
        if hasattr(workspace, "create_evidence_requested"):
            workspace.create_evidence_requested.connect(
                self.request_create_evidence
            )
        if hasattr(workspace, "remove_requested"):
            workspace.remove_requested.connect(self.request_remove_document)
        if hasattr(workspace, "open_requested"):
            workspace.open_requested.connect(self.request_open_document)
        if hasattr(workspace, "ocr_requested"):
            workspace.ocr_requested.connect(self.request_document_ocr)
        if hasattr(workspace, "refresh_requested"):
            workspace.refresh_requested.connect(self.refresh)
        if hasattr(workspace, "metadata_save_requested"):
            workspace.metadata_save_requested.connect(self.save_metadata)
        if hasattr(workspace, "metadata_cancel_requested"):
            workspace.metadata_cancel_requested.connect(
                self.cancel_metadata_edit
            )
        if hasattr(workspace, "set_unsaved_guard"):
            workspace.set_unsaved_guard(self.can_leave_metadata)
        if self.selection_store is not None:
            self._unsubscribe_selection = self.selection_store.subscribe(
                self._on_selection_changed
            )

    def request_open_document(self) -> bool:
        return self._request_selected(self.document_open_requested)

    def request_document_ocr(self) -> bool:
        return self._request_selected(self.document_ocr_requested)

    def _request_selected(self, callback) -> bool:
        if callback is None or self.selected_identity is None:
            return False
        return bool(callback(self.selected_identity))

    def request_remove_document(self) -> bool:
        if not self.can_leave_metadata():
            return False
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
        if (
            previous_identity in identities
            and self.workspace.select_document(previous_identity)
        ):
            self._apply_document_selection(previous_identity)
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
            if self.selection_store is not None:
                selection = self.selection_store.snapshot.selection.identity
                if selection.kind is SelectionKind.DOCUMENT:
                    self.selection_store.clear()
        return True

    def refresh(self, force=False) -> bool:
        if not force and not self.can_leave_metadata():
            return False
        return self.load()

    def navigate(self, request: DocumentNavigationRequest) -> bool:
        """Resolve e seleciona um documento por contrato neutro."""
        self.last_navigation_outcome = self.NAVIGATION_FAILED
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
            self.last_navigation_outcome = self.NAVIGATION_DOCUMENT_OPENED
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
            self.last_navigation_outcome = self.NAVIGATION_PAGE_MISSING
            return True
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
        self.last_navigation_outcome = self.NAVIGATION_DOCUMENT_OPENED
        return True

    def select_document(self, identity) -> bool:
        if (
            identity != self.selected_identity
            and not self.can_leave_metadata()
        ):
            self.workspace.select_document(self.selected_identity)
            return False
        if self.selection_store is not None:
            if not identity:
                self.selection_store.clear()
                return False
            summary = next(
                (item for item in self.catalog if item.identity == identity),
                None,
            )
            if summary is None:
                return False
            self.selection_store.select(
                SelectionContext(
                    SelectionIdentity(SelectionKind.DOCUMENT, identity),
                    display_name=summary.name,
                )
            )
            return self.selected_identity == identity
        return self._apply_document_selection(identity)

    def _apply_document_selection(self, identity) -> bool:
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

    def _on_selection_changed(self, snapshot) -> None:
        identity = snapshot.selection.identity
        if identity.kind is SelectionKind.DOCUMENT:
            if identity.identifier == self.selected_identity:
                return
            if not self.workspace.select_document(identity.identifier):
                return
            self._apply_document_selection(identity.identifier)
            return
        if self.selected_identity is not None:
            self.selected_identity = None
            self.selected_page_number = None
            self.workspace.select_document(None)
            self.workspace.clear_document()

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

    def save_metadata(self, document_type: str) -> bool:
        if (
            self.selected_identity is None
            or self.document_metadata_update_requested is None
        ):
            return False
        try:
            self.document_metadata_update_requested(
                self.selected_identity,
                document_type,
            )
        except (TypeError, ValueError, RuntimeError) as exc:
            message = str(exc) or "Valor inválido."
            self.workspace.show_metadata_error(message)
            self.notify(
                "error",
                f"Não foi possível salvar as alterações: {message}",
            )
            return False
        identity = self.selected_identity
        self.workspace.finish_metadata_edit()
        if not self.refresh(force=True):
            return False
        self.workspace.select_document(identity)
        self.notify("success", "Metadados atualizados.")
        return True

    def cancel_metadata_edit(self) -> bool:
        if not self.workspace.metadata_widget.is_editing:
            return False
        self.workspace.cancel_metadata_edit()
        self.notify("info", "Alterações canceladas.")
        return True

    def can_leave_metadata(self) -> bool:
        if not self.workspace.has_unsaved_metadata:
            return True
        decision = self.confirm_unsaved_metadata()
        if decision == "save":
            return self.save_metadata(
                self.workspace.metadata_widget.type_editor.currentData()
            )
        if decision == "discard":
            self.cancel_metadata_edit()
            return True
        return False
