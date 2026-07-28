"""Diagnóstico documental sem alterações automáticas."""

from collections import Counter

from applications.rsc.domain import RscDocument
from applications.rsc.dto.document_diagnostic import (
    DocumentDiagnostic,
    ManagedDocumentStatus,
)
from applications.rsc.infrastructure.document_files import (
    FILE_SIZE_KEY,
    LAST_MODIFIED_AT_KEY,
    DocumentHashService,
)


class DocumentHealthService:
    def __init__(self, hashes: DocumentHashService) -> None:
        if not isinstance(hashes, DocumentHashService):
            raise TypeError("hashes deve ser DocumentHashService.")
        self._hashes = hashes

    def verify(
        self, documents: tuple[RscDocument, ...]
    ) -> tuple[DocumentDiagnostic, ...]:
        checksum_counts = Counter(
            item.checksum for item in documents if item.checksum
        )
        return tuple(
            self._diagnose(item, checksum_counts) for item in documents
        )

    def _diagnose(
        self, document: RscDocument, checksum_counts: Counter
    ) -> DocumentDiagnostic:
        path = document.original_path
        if not path:
            return self._result(
                document,
                ManagedDocumentStatus.INVALID_REFERENCE,
                None,
                False,
                False,
                False,
                False,
                "Documento sem caminho original.",
            )
        identity = self._hashes.inspect(path)
        if not identity.exists:
            return self._result(
                document,
                ManagedDocumentStatus.MISSING,
                path,
                False,
                False,
                False,
                False,
                "Arquivo não encontrado.",
            )
        if not identity.is_file:
            return self._result(
                document,
                ManagedDocumentStatus.INVALID_REFERENCE,
                path,
                True,
                False,
                False,
                False,
                "A referência não aponta para um arquivo.",
            )
        hash_changed = (
            document.checksum is not None
            and document.checksum != identity.sha256
        )
        stored_size = document.metadata.get(FILE_SIZE_KEY)
        size_changed = (
            isinstance(stored_size, int) and stored_size != identity.size
        )
        stored_modified = document.metadata.get(LAST_MODIFIED_AT_KEY)
        modified_changed = (
            isinstance(stored_modified, str)
            and stored_modified != identity.last_modified_at
        )
        if hash_changed or size_changed or modified_changed:
            status = ManagedDocumentStatus.MODIFIED
            message = "O arquivo difere dos metadados registrados."
        elif document.checksum and checksum_counts[document.checksum] > 1:
            status = ManagedDocumentStatus.DUPLICATED
            message = "Outro documento possui o mesmo conteúdo SHA-256."
        elif (
            document.checksum is None
            or not isinstance(stored_size, int)
            or not isinstance(stored_modified, str)
        ):
            status = ManagedDocumentStatus.UNKNOWN
            message = "A referência existe, mas não possui identidade completa."
        else:
            status = ManagedDocumentStatus.AVAILABLE
            message = "Documento disponível e íntegro."
        return self._result(
            document,
            status,
            path,
            True,
            hash_changed,
            modified_changed,
            size_changed,
            message,
        )

    @staticmethod
    def _result(
        document,
        status,
        path,
        exists,
        hash_changed,
        modified_date_changed,
        size_changed,
        message,
    ):
        return DocumentDiagnostic(
            document.id,
            status,
            path,
            exists,
            hash_changed,
            modified_date_changed,
            size_changed,
            message,
        )
