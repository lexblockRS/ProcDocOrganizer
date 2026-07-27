"""Projeções imutáveis usadas pela apresentação do Dashboard."""

from dataclasses import dataclass, field
from enum import Enum


class DashboardState(str, Enum):
    NO_PROJECT = "no_project"
    LOADING = "loading"
    READY = "ready"
    ERROR = "error"


@dataclass(frozen=True, slots=True)
class ProjectSummaryProjection:
    project_name: str
    project_path: str
    application_id: str
    application_name: str
    created_at: str
    last_opened_at: str


@dataclass(frozen=True, slots=True)
class DocumentSummaryProjection:
    total_documents: int = 0
    processed_documents: int = 0
    pending_documents: int = 0
    ocr_required_documents: int = 0
    failed_documents: int = 0
    processed_pages: int = 0


@dataclass(frozen=True, slots=True)
class EvidenceSummaryProjection:
    total_evidences: int = 0


@dataclass(frozen=True, slots=True)
class DashboardProjection:
    state: DashboardState = DashboardState.NO_PROJECT
    project: ProjectSummaryProjection | None = None
    documents: DocumentSummaryProjection = field(
        default_factory=DocumentSummaryProjection
    )
    evidences: EvidenceSummaryProjection = field(
        default_factory=EvidenceSummaryProjection
    )
    error_message: str | None = None
