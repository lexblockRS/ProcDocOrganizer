"""
Serviços do ProcDocOrganizer.
"""

from .document_importer import DocumentImporter
from .document_import_service import (
    DocumentImportResult,
    DocumentImportService,
)
from .document_repository import DocumentRepository
from .evidence_repository_errors import (
    DuplicateEvidenceError,
    EvidenceDocumentNotFoundError,
    EvidenceNotFoundError as RepositoryEvidenceNotFoundError,
    EvidenceRepositoryError,
)
from .evidence_repository_port import EvidenceRepository
from .document_source_resolver import DocumentSourceResolver
from .search_document_source_resolver import SearchDocumentSourceResolver
from .sqlite_evidence_repository import SQLiteEvidenceRepository
from .search_service import SearchService
from .evidence_service import (
    EvidenceClockError,
    EvidenceDocumentUnavailableError,
    EvidenceNotFoundError,
    EvidenceService,
    EvidenceServiceError,
    EvidenceSourceStatus,
    EvidenceValidationError,
)
from .document_service import (
    DocumentNotFoundError,
    DocumentPageNotFoundError,
    DocumentService,
    DocumentServiceError,
)

__all__ = [
    "DocumentImporter",
    "DocumentImportResult",
    "DocumentImportService",
    "DocumentRepository",
    "EvidenceRepository",
    "DocumentSourceResolver",
    "SearchDocumentSourceResolver",
    "SQLiteEvidenceRepository",
    "EvidenceRepositoryError",
    "DuplicateEvidenceError",
    "EvidenceDocumentNotFoundError",
    "RepositoryEvidenceNotFoundError",
    "SearchService",
    "EvidenceService",
    "EvidenceServiceError",
    "EvidenceValidationError",
    "EvidenceNotFoundError",
    "EvidenceDocumentUnavailableError",
    "EvidenceClockError",
    "EvidenceSourceStatus",
    "DocumentService",
    "DocumentServiceError",
    "DocumentNotFoundError",
    "DocumentPageNotFoundError",
]
