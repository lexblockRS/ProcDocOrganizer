"""Coordena o Evidence Workspace sem depender de Qt ou persistência."""

from enum import Enum

from contracts import DocumentNavigationRequest
from models import EvidenceDraft, EvidenceSourceCandidate
from services.evidence_service import (
    EvidenceClockError, EvidenceDocumentUnavailableError,
    EvidenceNotFoundError, EvidenceServiceError, EvidenceSourceStatus,
    EvidenceValidationError,
)


class EvidenceEditorMode(str, Enum):
    EMPTY = "empty"
    VIEWING = "viewing"
    CREATING = "creating"
    EDITING = "editing"


class EvidenceController:
    """Fonte de verdade para seleção, draft, baseline e dirty state."""

    def __init__(
        self, workspace, evidence_service=None, *,
        confirm_unsaved=None, confirm_delete=None, confirm_duplicates=None,
        notify=None, document_navigation_requested=None,
    ):
        self.workspace = workspace
        self.service = evidence_service
        self.confirm_unsaved = confirm_unsaved or (lambda: "cancel")
        self.confirm_delete = confirm_delete or (lambda _evidence: False)
        self.confirm_duplicates = confirm_duplicates or (lambda _items: False)
        self.notify = notify or (lambda _kind, message: workspace.show_message(message))
        self.document_navigation_requested = document_navigation_requested
        self.evidences = ()
        self.selected_evidence = None
        self.current_draft = EvidenceDraft.empty()
        self.baseline_draft = EvidenceDraft.empty()
        self.mode = EvidenceEditorMode.EMPTY
        self._connect()
        self._render_state()

    @property
    def dirty(self) -> bool:
        return self.current_draft != self.baseline_draft

    def set_service(self, service) -> None:
        self.service = service
        self.clear()
        if service is not None:
            self.load()

    def load(self, preserve_selection=True) -> bool:
        if self.service is None:
            self.clear()
            return False
        if self.dirty and not self._resolve_unsaved():
            return False
        selected_id = (
            self.selected_evidence.id
            if preserve_selection and self.selected_evidence else None
        )
        try:
            self.evidences = tuple(self.service.list_all())
            statuses = {
                evidence.id: self._source_status(evidence)
                for evidence in self.evidences
            }
        except EvidenceServiceError as exc:
            self._show_error(exc)
            return False
        self.workspace.set_evidences(self.evidences, statuses)
        if selected_id and self._find(selected_id):
            self._select(selected_id)
        elif self.selected_evidence and not self._find(self.selected_evidence.id):
            self._set_empty()
        self._render_state()
        return True

    def select(self, evidence_id) -> bool:
        if evidence_id is None:
            return False
        if self.selected_evidence and evidence_id == self.selected_evidence.id:
            return True
        previous_id = self.selected_evidence.id if self.selected_evidence else None
        if self.dirty and not self._resolve_unsaved():
            self.workspace.select_evidence(previous_id)
            return False
        return self._select(evidence_id)

    def start_create(self) -> bool:
        if self.dirty and not self._resolve_unsaved():
            return False
        self._start_creation(EvidenceDraft.empty())
        return True

    def start_create_from_source(
        self, candidate: EvidenceSourceCandidate
    ) -> bool:
        if self.service is None:
            return False
        if self.dirty and not self._resolve_unsaved():
            return False
        try:
            draft = EvidenceDraft.from_source_candidate(candidate)
            available = self.service.is_document_available(
                candidate.document_identity
            )
        except (TypeError, ValueError, EvidenceServiceError) as exc:
            self._show_error(exc)
            return False
        self._start_creation(
            draft,
            source_locked=True,
            source_status=(
                EvidenceSourceStatus.AVAILABLE
                if available else EvidenceSourceStatus.UNAVAILABLE
            ),
            message="" if available else (
                "O documento deste resultado não está mais disponível no projeto."
            ),
        )
        return True

    def update_draft(self, draft: EvidenceDraft) -> None:
        if self.mode == EvidenceEditorMode.EMPTY:
            return
        self.current_draft = draft
        if self.mode != EvidenceEditorMode.CREATING:
            self.mode = (
                EvidenceEditorMode.EDITING if self.dirty
                else EvidenceEditorMode.VIEWING
            )
        self._render_state()

    def save(self) -> bool:
        if self.service is None or not self.dirty:
            return False
        try:
            if self.mode == EvidenceEditorMode.CREATING:
                request = self.current_draft.to_create_request()
                duplicates = self.service.find_potential_duplicates(
                    request.document_identity, request.page_number, request.title
                )
                if duplicates and not self.confirm_duplicates(duplicates):
                    return False
                saved = self.service.create(request)
                message = "Evidência criada com sucesso."
            else:
                saved = self.service.update(self.current_draft.to_update_request())
                message = "Evidência atualizada com sucesso."
        except (ValueError, EvidenceServiceError) as exc:
            self._show_error(exc)
            return False
        self._reload_after_save(saved.id)
        self.notify("success", message)
        return True

    def cancel(self) -> None:
        if self.mode == EvidenceEditorMode.CREATING:
            self._set_empty()
        elif self.selected_evidence is not None:
            self._restore_baseline(render=True)

    def delete(self) -> bool:
        evidence = self.selected_evidence
        if evidence is None or not self.confirm_delete(evidence):
            return False
        try:
            deleted = self.service.delete(evidence.id)
        except EvidenceServiceError as exc:
            self._show_error(exc)
            return False
        self.load(preserve_selection=False)
        self._set_empty()
        self.notify(
            "success" if deleted else "info",
            "Evidência excluída com sucesso." if deleted
            else "A evidência não foi encontrada. A lista foi atualizada.",
        )
        return deleted

    def can_leave(self) -> bool:
        return not self.dirty or self._resolve_unsaved()

    def clear(self) -> None:
        self.evidences = ()
        self._reset_editor_state()
        self.workspace.clear()
        self._render_state()

    def _connect(self) -> None:
        self.workspace.new_requested.connect(self.start_create)
        self.workspace.save_requested.connect(self.save)
        self.workspace.cancel_requested.connect(self.cancel)
        self.workspace.delete_requested.connect(self.delete)
        self.workspace.refresh_requested.connect(self.load)
        self.workspace.evidence_selected.connect(self.select)
        self.workspace.draft_changed.connect(self.update_draft)
        if hasattr(self.workspace, "open_document_requested"):
            self.workspace.open_document_requested.connect(
                self.request_document_navigation
            )

    def set_document_navigation_requested(self, callback) -> None:
        self.document_navigation_requested = callback

    def request_document_navigation(self) -> bool:
        """Entrega uma solicitação neutra de navegação ao composition root."""
        if (
            self.selected_evidence is None
            or self.document_navigation_requested is None
        ):
            return False
        try:
            request = DocumentNavigationRequest(
                document_identity=self.selected_evidence.document_identity,
                page_number=self.selected_evidence.page_number,
            )
            return bool(self.document_navigation_requested(request))
        except (AttributeError, TypeError, ValueError):
            return False

    def _select(self, evidence_id) -> bool:
        evidence = self._find(evidence_id)
        if evidence is None:
            self.workspace.select_evidence(None)
            return False
        self.selected_evidence = evidence
        draft = EvidenceDraft.from_evidence(evidence)
        self.current_draft = draft
        self.baseline_draft = draft
        self.mode = EvidenceEditorMode.VIEWING
        self.workspace.select_evidence(evidence.id)
        self.workspace.set_draft(draft)
        self.workspace.set_source_status(self._source_status(evidence))
        self.workspace.show_message("")
        self._render_state()
        return True

    def _resolve_unsaved(self) -> bool:
        decision = self.confirm_unsaved()
        if decision == "save":
            return self.save()
        if decision == "discard":
            if self.mode == EvidenceEditorMode.CREATING:
                self._set_empty()
            else:
                self._restore_baseline(render=False)
            return True
        return False

    def _reload_after_save(self, evidence_id) -> None:
        self.current_draft = self.baseline_draft
        self.evidences = tuple(self.service.list_all())
        statuses = {item.id: self._source_status(item) for item in self.evidences}
        self.workspace.set_evidences(self.evidences, statuses)
        self._select(evidence_id)

    def _set_empty(self) -> None:
        self._reset_editor_state()
        self.workspace.select_evidence(None)
        self.workspace.set_draft(self.current_draft, creating=True)
        self.workspace.set_source_status(None)
        self._render_state()

    def _start_creation(
        self, draft: EvidenceDraft, *, source_locked=False,
        source_status=None, message="",
    ) -> None:
        self.selected_evidence = None
        self.current_draft = draft
        self.baseline_draft = EvidenceDraft.empty()
        self.mode = EvidenceEditorMode.CREATING
        self.workspace.select_evidence(None)
        self.workspace.set_draft(draft, creating=True, source_locked=source_locked)
        self.workspace.set_source_status(source_status)
        self.workspace.show_message(message)
        self._render_state()
        self.workspace.focus_title()

    def _restore_baseline(self, *, render: bool) -> None:
        self.current_draft = self.baseline_draft
        self.mode = EvidenceEditorMode.VIEWING
        if render:
            self.workspace.set_draft(self.current_draft)
            self._render_state()

    def _reset_editor_state(self) -> None:
        self.selected_evidence = None
        self.current_draft = EvidenceDraft.empty()
        self.baseline_draft = EvidenceDraft.empty()
        self.mode = EvidenceEditorMode.EMPTY

    def _find(self, evidence_id):
        return next((item for item in self.evidences if item.id == evidence_id), None)

    def _source_status(self, evidence):
        try:
            return (
                EvidenceSourceStatus.AVAILABLE
                if self.service.is_source_available(evidence)
                else EvidenceSourceStatus.UNAVAILABLE
            )
        except EvidenceServiceError:
            return EvidenceSourceStatus.UNAVAILABLE

    def _render_state(self) -> None:
        self.workspace.set_editor_state(
            self.mode, self.dirty, self.current_draft.is_minimally_valid()
        )

    def _show_error(self, error) -> None:
        if isinstance(error, EvidenceDocumentUnavailableError):
            message = "O documento informado não está disponível no projeto."
        elif isinstance(error, EvidenceNotFoundError):
            message = "A evidência não foi encontrada. A lista será atualizada."
        elif isinstance(error, EvidenceClockError):
            message = "Não foi possível salvar devido a uma inconsistência de data e hora."
        elif isinstance(error, (EvidenceValidationError, ValueError)):
            message = "Revise os dados da evidência."
        else:
            message = "Não foi possível concluir a operação."
        self.notify("error", message)
