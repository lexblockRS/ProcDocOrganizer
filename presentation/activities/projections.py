"""Projeções imutáveis da tela de atividades."""

from dataclasses import dataclass
from enum import Enum


class ActivitiesViewState(str, Enum):
    NO_PROJECT = "no_project"
    LOADING = "loading"
    EMPTY = "empty"
    READY = "ready"
    ERROR = "error"


@dataclass(frozen=True, slots=True)
class ActivityListItemProjection:
    activity_id: str
    description: str
    state: str
    state_label: str
    evidence_count: int
    exercise_count: int
    is_selected: bool = False


@dataclass(frozen=True, slots=True)
class ActivityDetailsProjection:
    activity_id: str
    description: str
    state: str
    state_label: str
    evidence_ids: tuple[str, ...]
    exercise_ids: tuple[str, ...]
    evidence_count: int
    exercise_count: int
    state_options: tuple[tuple[str, str], ...] = ()
    related_interpretations: tuple["RelatedInterpretationProjection", ...] = ()
    related_exercises: tuple["RelatedExerciseProjection", ...] = ()


@dataclass(frozen=True, slots=True)
class RelatedExerciseProjection:
    exercise_id: str
    available: bool
    person_id: str | None = None
    role: str | None = None
    organization: str | None = None
    unit: str | None = None
    period: str | None = None
    status: str | None = None
    assignment_count: int = 0
    unavailable_reason: str | None = None


@dataclass(frozen=True, slots=True)
class RelatedInterpretationProjection:
    assignment_id: str
    exercise_id: str | None
    person_id: str
    role: str
    evidence_id: str
    document_identity: str | None
    page_number: int | None
    snippet: str | None
    source_available: bool
    assignment_available: bool = True
    evidence_available: bool = True
    document_available: bool = True
    unavailable_reason: str | None = None


@dataclass(frozen=True, slots=True)
class ActivitiesProjection:
    state: ActivitiesViewState = ActivitiesViewState.NO_PROJECT
    project_name: str | None = None
    items: tuple[ActivityListItemProjection, ...] = ()
    selected_activity_id: str | None = None
    selected_activity: ActivityDetailsProjection | None = None
    total: int = 0
    remembered_count: int = 0
    investigating_count: int = 0
    partially_proven_count: int = 0
    proven_count: int = 0
    error_message: str | None = None
