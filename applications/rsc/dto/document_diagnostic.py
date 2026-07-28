"""DTOs imutáveis do gerenciamento documental RSC."""

from dataclasses import dataclass
from enum import Enum


class ManagedDocumentStatus(str, Enum):
    UNKNOWN = "unknown"
    AVAILABLE = "available"
    MISSING = "missing"
    MODIFIED = "modified"
    DUPLICATED = "duplicated"
    INVALID_REFERENCE = "invalid_reference"


# Public descriptive aliases avoid ambiguity with the domain's normative
# DocumentStatus while preserving a conventional contract name for clients.
DocumentHealthStatus = ManagedDocumentStatus
DocumentStatus = ManagedDocumentStatus


class DocumentReferenceMode(str, Enum):
    """Contrato preparado para referências e conteúdo incorporado futuro."""

    REFERENCED = "referenced"
    EMBEDDED = "embedded"


@dataclass(frozen=True, slots=True)
class DocumentDiagnostic:
    document_id: str
    status: ManagedDocumentStatus
    path: str | None
    exists: bool
    hash_changed: bool
    modified_date_changed: bool
    size_changed: bool
    message: str


@dataclass(frozen=True, slots=True)
class VerifyDocumentsResult:
    diagnostics: tuple[DocumentDiagnostic, ...]

    @property
    def total(self) -> int:
        return len(self.diagnostics)

    @property
    def healthy_count(self) -> int:
        return sum(
            item.status is ManagedDocumentStatus.AVAILABLE
            for item in self.diagnostics
        )


@dataclass(frozen=True, slots=True)
class UpdateDocumentReferenceResult:
    document_id: str
    path: str
    checksum: str
    size: int
    last_modified_at: str
    document: object
