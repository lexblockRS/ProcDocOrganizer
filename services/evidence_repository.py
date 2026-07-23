"""Facade de compatibilidade do antigo repository concreto."""

from .evidence_repository_errors import (
    DuplicateEvidenceError,
    EvidenceDocumentNotFoundError,
    EvidenceNotFoundError,
    EvidenceRepositoryError,
)
from .sqlite_evidence_repository import SQLiteEvidenceRepository

# Compatibilidade temporária para consumidores históricos deste módulo.
EvidenceRepository = SQLiteEvidenceRepository

__all__ = [
    "DuplicateEvidenceError",
    "EvidenceDocumentNotFoundError",
    "EvidenceNotFoundError",
    "EvidenceRepository",
    "EvidenceRepositoryError",
    "SQLiteEvidenceRepository",
]
