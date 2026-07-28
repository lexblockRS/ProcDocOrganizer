"""Comandos imutáveis reservados aos futuros casos de uso RSC."""

from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True, slots=True)
class CreateProcessCommand:
    applicant_name: str
    institution: str
    applicant_identifier: str | None = None


@dataclass(frozen=True, slots=True)
class CreateActivityCommand:
    process_id: str
    criterion_id: str
    title: str
    quantity: str
    description: str | None = None
    score_variant_id: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    notes: str | None = None


@dataclass(frozen=True, slots=True)
class RegisterDocumentCommand:
    process_id: str
    file_name: str
    document_id: str | None = None
    original_path: str | None = None
    stored_path: str | None = None
    mime_type: str | None = None
    checksum: str | None = None
    description: str | None = None


@dataclass(frozen=True, slots=True)
class CreateEvidenceCommand:
    process_id: str
    activity_id: str
    document_ids: tuple[str, ...]
    description: str


@dataclass(frozen=True, slots=True)
class ValidateProcessCommand:
    process_id: str


@dataclass(frozen=True, slots=True)
class CalculateScoreCommand:
    process_id: str


@dataclass(frozen=True, slots=True)
class GenerateSummaryCommand:
    process_id: str


@dataclass(frozen=True, slots=True)
class GetProcessCommand:
    process_id: str


@dataclass(frozen=True, slots=True)
class ListProcessesCommand:
    pass


@dataclass(frozen=True, slots=True)
class GetDocumentCommand:
    document_id: str


@dataclass(frozen=True, slots=True)
class ListDocumentsCommand:
    process_id: str


@dataclass(frozen=True, slots=True)
class RemoveDocumentCommand:
    process_id: str
    document_id: str


@dataclass(frozen=True, slots=True)
class GetActivityCommand:
    process_id: str
    activity_id: str


@dataclass(frozen=True, slots=True)
class ListActivitiesCommand:
    process_id: str


@dataclass(frozen=True, slots=True)
class ListActivitiesByCriterionCommand:
    process_id: str
    criterion_id: str


@dataclass(frozen=True, slots=True)
class ListActivitiesByRequirementCommand:
    process_id: str
    requirement_id: str


@dataclass(frozen=True, slots=True)
class GetEvidenceCommand:
    evidence_id: str


@dataclass(frozen=True, slots=True)
class ListEvidenceCommand:
    pass


@dataclass(frozen=True, slots=True)
class ListEvidenceByActivityCommand:
    process_id: str
    activity_id: str
