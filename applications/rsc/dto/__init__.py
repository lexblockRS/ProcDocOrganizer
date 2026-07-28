"""Objetos de transferência da camada Application do ProcDoc RSC."""

from .activity import ActivityDTO
from .functional_assignment_evidence import (
    FunctionalAssignmentEvidenceDTO,
)
from .functional_exercise import FunctionalExerciseDTO
from .project import ProjectDTO
from .document_diagnostic import (
    DocumentDiagnostic,
    DocumentHealthStatus,
    DocumentReferenceMode,
    DocumentStatus,
    ManagedDocumentStatus,
    UpdateDocumentReferenceResult,
    VerifyDocumentsResult,
)

__all__ = [
    "ActivityDTO",
    "DocumentDiagnostic",
    "DocumentHealthStatus",
    "DocumentReferenceMode",
    "DocumentStatus",
    "FunctionalAssignmentEvidenceDTO",
    "FunctionalExerciseDTO",
    "ManagedDocumentStatus",
    "ProjectDTO",
    "UpdateDocumentReferenceResult",
    "VerifyDocumentsResult",
]
