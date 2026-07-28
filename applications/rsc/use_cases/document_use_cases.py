"""Casos de uso documentais em memória do processo RSC."""

from datetime import datetime, timezone

from applications.rsc.services import (
    RscDocumentService,
    RscProcessService,
)

from ._support import require_command, require_text, require_uuid
from .commands import (
    GetDocumentCommand,
    ListDocumentsCommand,
    RegisterDocumentCommand,
    RemoveDocumentCommand,
)
from .errors import (
    DocumentNotFoundError,
    DuplicateEntityError,
    InvalidCommandError,
    ProcessNotFoundError,
)
from .results import (
    GetDocumentResult,
    ListDocumentsResult,
    RegisterDocumentResult,
    RemoveDocumentResult,
)


class _DocumentUseCase:
    def __init__(
        self,
        processes: RscProcessService,
        documents: RscDocumentService,
    ) -> None:
        self._processes = processes
        self._documents = documents

    def _get_process(self, process_id: str):
        normalized = require_uuid(process_id, "process_id")
        try:
            return self._processes.get_process(normalized)
        except KeyError as exc:
            raise ProcessNotFoundError(
                f"processo não encontrado: {normalized}"
            ) from exc

    def _get_document(self, document_id: str):
        normalized = require_uuid(document_id, "document_id")
        try:
            return self._documents.get_document(normalized)
        except KeyError as exc:
            raise DocumentNotFoundError(
                f"documento não encontrado: {normalized}"
            ) from exc


class RegisterDocumentUseCase(_DocumentUseCase):
    def execute(
        self, command: RegisterDocumentCommand
    ) -> RegisterDocumentResult:
        require_command(command, RegisterDocumentCommand)
        process = self._get_process(command.process_id)
        document_id = (
            require_uuid(command.document_id, "document_id")
            if command.document_id is not None
            else None
        )
        if (
            document_id is not None
            and document_id in {
                item.id for item in self._documents.list_documents()
            }
        ):
            raise DuplicateEntityError(
                f"documento duplicado: {document_id}"
            )
        file_name = require_text(command.file_name, "file_name")
        document = None
        try:
            document = self._documents.create_document(
                id=document_id,
                file_name=file_name,
                original_path=command.original_path,
                stored_path=command.stored_path,
                mime_type=command.mime_type,
                checksum=command.checksum,
                description=command.description,
            )
            process.attach_document(document.id)
        except (TypeError, ValueError) as exc:
            if document is not None:
                try:
                    self._documents.remove_document(document.id)
                except KeyError:
                    pass
            raise InvalidCommandError(str(exc)) from exc
        return RegisterDocumentResult(
            process_id=process.id,
            document_id=document.id,
            registered_at=document.created_at,
            document=document,
        )


class GetDocumentUseCase(_DocumentUseCase):
    def execute(self, command: GetDocumentCommand) -> GetDocumentResult:
        require_command(command, GetDocumentCommand)
        document = self._get_document(command.document_id)
        return GetDocumentResult(document.id, document)


class ListDocumentsUseCase(_DocumentUseCase):
    def execute(
        self, command: ListDocumentsCommand
    ) -> ListDocumentsResult:
        require_command(command, ListDocumentsCommand)
        process = self._get_process(command.process_id)
        documents = []
        for document_id in process.document_ids:
            documents.append(self._get_document(document_id))
        return ListDocumentsResult(process.id, tuple(documents))


class RemoveDocumentUseCase(_DocumentUseCase):
    def execute(
        self, command: RemoveDocumentCommand
    ) -> RemoveDocumentResult:
        require_command(command, RemoveDocumentCommand)
        process = self._get_process(command.process_id)
        document = self._get_document(command.document_id)
        if document.id not in process.document_ids:
            raise DocumentNotFoundError(
                "documento não está associado ao processo informado."
            )
        process.detach_document(document.id)
        self._documents.remove_document(document.id)
        return RemoveDocumentResult(
            process_id=process.id,
            document_id=document.id,
            removed_at=datetime.now(timezone.utc),
        )
