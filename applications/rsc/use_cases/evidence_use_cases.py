"""Casos de uso de evidências vinculadas a atividades e documentos."""

from applications.rsc.services import (
    RscActivityService,
    RscDocumentService,
    RscEvidenceService,
    RscProcessService,
)

from ._support import require_command, require_text, require_uuid
from .commands import (
    CreateEvidenceCommand,
    GetEvidenceCommand,
    ListEvidenceByActivityCommand,
    ListEvidenceCommand,
)
from .errors import (
    ActivityNotFoundError,
    DocumentNotFoundError,
    DomainValidationError,
    EvidenceNotFoundError,
    ProcessNotFoundError,
)
from .results import (
    CreateEvidenceResult,
    GetEvidenceResult,
    ListEvidenceResult,
)


class _EvidenceUseCase:
    def __init__(
        self,
        processes: RscProcessService,
        activities: RscActivityService,
        documents: RscDocumentService,
        evidence: RscEvidenceService,
    ) -> None:
        self._processes = processes
        self._activities = activities
        self._documents = documents
        self._evidence = evidence

    def _get_process(self, process_id: str):
        normalized = require_uuid(process_id, "process_id")
        try:
            return self._processes.get_process(normalized)
        except KeyError as exc:
            raise ProcessNotFoundError(
                f"processo não encontrado: {normalized}"
            ) from exc

    def _get_activity(self, process, activity_id: str):
        normalized = require_uuid(activity_id, "activity_id")
        try:
            return self._activities.get_activity(process, normalized)
        except KeyError as exc:
            raise ActivityNotFoundError(
                f"atividade não encontrada: {normalized}"
            ) from exc

    def _require_document(self, document_id: str):
        normalized = require_uuid(document_id, "document_id")
        try:
            return self._documents.get_document(normalized)
        except KeyError as exc:
            raise DocumentNotFoundError(
                f"documento não encontrado: {normalized}"
            ) from exc


class CreateEvidenceUseCase(_EvidenceUseCase):
    def execute(
        self, command: CreateEvidenceCommand
    ) -> CreateEvidenceResult:
        require_command(command, CreateEvidenceCommand)
        process = self._get_process(command.process_id)
        activity = self._get_activity(process, command.activity_id)
        description = require_text(command.description, "description")
        document_ids = tuple(command.document_ids)
        if not document_ids:
            raise DomainValidationError(
                "evidência exige ao menos um documento."
            )
        if len(set(document_ids)) != len(document_ids):
            raise DomainValidationError(
                "documentos não podem duplicar."
            )
        normalized_document_ids = tuple(
            self._require_document(value).id for value in document_ids
        )
        unrelated = set(normalized_document_ids) - set(process.document_ids)
        if unrelated:
            raise DocumentNotFoundError(
                "documento não está associado ao processo informado."
            )
        try:
            evidence = self._evidence.create_evidence(
                activity_id=activity.id,
                document_ids=normalized_document_ids,
                description=description,
            )
            updated_activity = self._evidence.add_evidence(
                activity, evidence
            )
            self._activities.update_activity(process, updated_activity)
        except (KeyError, TypeError, ValueError) as exc:
            raise DomainValidationError(str(exc)) from exc
        return CreateEvidenceResult(
            process_id=process.id,
            activity_id=updated_activity.id,
            evidence_id=evidence.id,
            created_at=evidence.created_at,
            evidence=evidence,
        )


class GetEvidenceUseCase(_EvidenceUseCase):
    def execute(self, command: GetEvidenceCommand) -> GetEvidenceResult:
        require_command(command, GetEvidenceCommand)
        evidence_id = require_uuid(command.evidence_id, "evidence_id")
        try:
            evidence = self._evidence.get_evidence(evidence_id)
        except KeyError as exc:
            raise EvidenceNotFoundError(
                f"evidência não encontrada: {evidence_id}"
            ) from exc
        return GetEvidenceResult(evidence.id, evidence)


class ListEvidenceUseCase(_EvidenceUseCase):
    def execute(
        self, command: ListEvidenceCommand
    ) -> ListEvidenceResult:
        require_command(command, ListEvidenceCommand)
        return ListEvidenceResult(self._evidence.list_all())


class ListEvidenceByActivityUseCase(_EvidenceUseCase):
    def execute(
        self, command: ListEvidenceByActivityCommand
    ) -> ListEvidenceResult:
        require_command(command, ListEvidenceByActivityCommand)
        process = self._get_process(command.process_id)
        activity = self._get_activity(process, command.activity_id)
        return ListEvidenceResult(
            self._evidence.list_by_activity(activity)
        )
