"""Exceções públicas da persistência de evidências."""

from database import DatabaseError


class EvidenceRepositoryError(DatabaseError):
    pass


class DuplicateEvidenceError(EvidenceRepositoryError):
    pass


class EvidenceNotFoundError(EvidenceRepositoryError):
    pass


class EvidenceDocumentNotFoundError(EvidenceRepositoryError):
    pass
