"""Resultados estruturados reservados aos futuros casos de uso RSC."""

from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass(frozen=True, slots=True)
class CreateProcessResult:
    process_id: str
    created_at: datetime
    process: Any = None


@dataclass(frozen=True, slots=True)
class CreateActivityResult:
    process_id: str
    activity_id: str
    created_at: datetime
    activity: Any = None


@dataclass(frozen=True, slots=True)
class RegisterDocumentResult:
    process_id: str
    document_id: str
    registered_at: datetime
    document: Any = None


@dataclass(frozen=True, slots=True)
class CreateEvidenceResult:
    process_id: str
    activity_id: str
    evidence_id: str
    created_at: datetime
    evidence: Any = None


@dataclass(frozen=True, slots=True)
class ValidationUseCaseResult:
    process_id: str
    validated_at: datetime
    executed: bool = False
    is_valid: bool = False
    issues: tuple[Any, ...] = ()
    errors: tuple[Any, ...] = ()
    warnings: tuple[Any, ...] = ()
    error_count: int = 0
    warning_count: int = 0
    validation: Any = None


@dataclass(frozen=True, slots=True)
class ScoreUseCaseResult:
    process_id: str
    calculated_at: datetime
    total_score: Any = None
    requirement_scores: tuple[Any, ...] = ()
    warnings: tuple[str, ...] = ()
    score: Any = None


@dataclass(frozen=True, slots=True)
class SummaryUseCaseResult:
    process_id: str
    generated_at: datetime
    summary: Any = None


@dataclass(frozen=True, slots=True)
class GetProcessResult:
    process_id: str
    process: Any


@dataclass(frozen=True, slots=True)
class ListProcessesResult:
    processes: tuple[Any, ...]


@dataclass(frozen=True, slots=True)
class GetDocumentResult:
    document_id: str
    document: Any


@dataclass(frozen=True, slots=True)
class ListDocumentsResult:
    process_id: str
    documents: tuple[Any, ...]


@dataclass(frozen=True, slots=True)
class RemoveDocumentResult:
    process_id: str
    document_id: str
    removed_at: datetime


@dataclass(frozen=True, slots=True)
class GetActivityResult:
    process_id: str
    activity_id: str
    activity: Any


@dataclass(frozen=True, slots=True)
class ListActivitiesResult:
    process_id: str
    activities: tuple[Any, ...]


@dataclass(frozen=True, slots=True)
class GetEvidenceResult:
    evidence_id: str
    evidence: Any


@dataclass(frozen=True, slots=True)
class ListEvidenceResult:
    evidence: tuple[Any, ...]
