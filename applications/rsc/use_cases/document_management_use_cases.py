"""Casos de uso de integridade e atualização de referências documentais."""

from dataclasses import dataclass, replace
from pathlib import Path

from applications.rsc.dto.document_diagnostic import (
    DocumentReferenceMode,
    ManagedDocumentStatus,
    UpdateDocumentReferenceResult,
    VerifyDocumentsResult,
)
from applications.rsc.infrastructure.document_files import (
    FILE_EXTENSION_KEY,
    FILE_SIZE_KEY,
    LAST_MODIFIED_AT_KEY,
    MANAGED_STATUS_KEY,
    REFERENCE_MODE_KEY,
    DocumentHashService,
)
from applications.rsc.services import RscDocumentService
from applications.rsc.services.document_health_service import (
    DocumentHealthService,
)

from ._support import require_command, require_text, require_uuid
from .errors import DocumentNotFoundError, InvalidCommandError


@dataclass(frozen=True, slots=True)
class VerifyDocumentsCommand:
    pass


@dataclass(frozen=True, slots=True)
class UpdateDocumentReferenceCommand:
    document_id: str
    path: str | Path


class VerifyDocumentsUseCase:
    def __init__(
        self, documents: RscDocumentService, health: DocumentHealthService
    ) -> None:
        self._documents = documents
        self._health = health

    def execute(
        self, command: VerifyDocumentsCommand
    ) -> VerifyDocumentsResult:
        require_command(command, VerifyDocumentsCommand)
        return VerifyDocumentsResult(
            self._health.verify(self._documents.list_documents())
        )


class UpdateDocumentReferenceUseCase:
    def __init__(
        self, documents: RscDocumentService, hashes: DocumentHashService
    ) -> None:
        self._documents = documents
        self._hashes = hashes

    def execute(
        self, command: UpdateDocumentReferenceCommand
    ) -> UpdateDocumentReferenceResult:
        require_command(command, UpdateDocumentReferenceCommand)
        document_id = require_uuid(command.document_id, "document_id")
        path = require_text(str(command.path), "path")
        try:
            document = self._documents.get_document(document_id)
        except KeyError as exc:
            raise DocumentNotFoundError(
                f"documento não encontrado: {document_id}"
            ) from exc
        identity = self._hashes.inspect(path)
        if not identity.exists:
            raise InvalidCommandError("o arquivo informado não existe.")
        if not identity.is_file:
            raise InvalidCommandError(
                "a referência informada não aponta para um arquivo."
            )
        metadata = dict(document.metadata)
        metadata.update(
            {
                FILE_EXTENSION_KEY: identity.extension,
                FILE_SIZE_KEY: identity.size,
                LAST_MODIFIED_AT_KEY: identity.last_modified_at,
                MANAGED_STATUS_KEY: ManagedDocumentStatus.AVAILABLE.value,
                REFERENCE_MODE_KEY: DocumentReferenceMode.REFERENCED.value,
            }
        )
        updated = replace(
            document,
            file_name=Path(path).name,
            original_path=path,
            checksum=identity.sha256,
            metadata=metadata,
        )
        self._documents.replace_document(updated)
        return UpdateDocumentReferenceResult(
            updated.id,
            path,
            identity.sha256,
            identity.size,
            identity.last_modified_at,
            updated,
        )
