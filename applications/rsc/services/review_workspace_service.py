"""Composicao passiva do Review Workspace."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from presentation.coverage import CoverageResult
from presentation.insights import Insight, InsightCollection, InsightSeverity
from presentation.navigation_contracts import NavigationIntent
from presentation.navigation_contracts import WorkspaceFilter
from presentation.resources import ResourceIdentity, ResourceType
from presentation.workspace import WorkspaceSnapshot
from applications.rsc.operational_actions import ExecuteEvaluationAction
from presentation.insights import InsightAction


class ReviewCategory(str, Enum):
    DOCUMENTS = "documents"
    EVIDENCES = "evidences"
    EXECUTION_FACTS = "execution_facts"
    REQUIREMENTS = "requirements"
    PROJECT = "project"


class ReviewOrigin(str, Enum):
    COVERAGE = "coverage"
    INSIGHT = "insight"


class ReviewState(str, Enum):
    READY = "ready"
    NO_ITEMS = "no_items"
    NO_PENDING = "no_pending"
    PROJECT_EMPTY = "project_empty"
    PROJECT_NOT_EVALUATED = "project_not_evaluated"


@dataclass(frozen=True, slots=True)
class ReviewProjectSummary:
    project_id: str | None
    project_name: str
    project_status: str


@dataclass(frozen=True, slots=True)
class ReviewItem:
    item_id: str
    category: ReviewCategory
    severity: InsightSeverity
    title: str
    description: str
    primary_resource: ResourceIdentity | None
    related_resources: tuple[ResourceIdentity, ...]
    origin: ReviewOrigin
    navigation_intent: NavigationIntent | None
    operational_action: ExecuteEvaluationAction | None = None


@dataclass(frozen=True, slots=True)
class ReviewCategorySummary:
    category: ReviewCategory
    total: int


@dataclass(frozen=True, slots=True)
class ReviewWorkspaceSnapshot:
    project: ReviewProjectSummary
    items: tuple[ReviewItem, ...]
    category_summary: tuple[ReviewCategorySummary, ...]
    active_filters: tuple[WorkspaceFilter, ...]
    workspace_revision: int
    state: ReviewState


_SEVERITY_ORDER = {InsightSeverity.ERROR: 0, InsightSeverity.WARNING: 1, InsightSeverity.INFO: 2, InsightSeverity.SUCCESS: 3}


class ReviewWorkspaceService:
    """Projeta fontes prontas; nao analisa, diagnostica ou navega."""

    def compose(self, workspace: WorkspaceSnapshot, coverage: CoverageResult,
                insights: InsightCollection) -> ReviewWorkspaceSnapshot:
        if not isinstance(workspace, WorkspaceSnapshot):
            raise TypeError("workspace deve ser WorkspaceSnapshot.")
        if not isinstance(coverage, CoverageResult):
            raise TypeError("coverage deve ser CoverageResult.")
        if not isinstance(insights, InsightCollection):
            raise TypeError("insights deve ser InsightCollection.")
        active = workspace.active_filters
        unfiltered = tuple(self._insight(item) for item in insights.insights)
        items = tuple(sorted((item for item in unfiltered if self._matches(item, active)), key=self._sort_key))
        counts = tuple(ReviewCategorySummary(category, sum(item.category is category for item in items)) for category in ReviewCategory)
        state = self._state(workspace, coverage, insights, unfiltered, items, active)
        return ReviewWorkspaceSnapshot(
            ReviewProjectSummary(workspace.project_id, str(workspace.metadata.get("project_name", workspace.project_id or "")), str(workspace.metadata.get("project_status", ""))),
            items, counts, active, workspace.revision, state,
        )

    @staticmethod
    def _insight(value: Insight) -> ReviewItem:
        primary = value.related_resources[0].identity if value.related_resources else None
        related = tuple(reference.identity for reference in value.related_resources[1:])
        identity = value.identity
        origin = (
            ReviewOrigin.COVERAGE
            if identity.provider_id == "coverage_analysis"
            else ReviewOrigin.INSIGHT
        )
        return ReviewItem(f"insight:{identity.provider_id}:{identity.insight_code}:{identity.discriminator or ''}",
                          _category(primary), value.severity, value.title, value.message, primary, related,
                          origin, _intent(primary, "review_workspace_insight"),
                          ExecuteEvaluationAction(identity.discriminator)
                          if InsightAction.EXECUTE_EVALUATION in value.available_actions and identity.discriminator is not None
                          else None)

    @staticmethod
    def _matches(item: ReviewItem, filters: tuple[WorkspaceFilter, ...]) -> bool:
        values = {value.filter_id: value.parameters.get("value") for value in filters}
        category = values.get("review.category")
        severity = values.get("review.severity")
        origin = values.get("review.origin")
        pending = values.get("review.only_pending") is True
        return (category is None or item.category.value == category) and (severity is None or item.severity.value == severity) and (origin is None or item.origin.value == origin) and (not pending or item.severity in (InsightSeverity.ERROR, InsightSeverity.WARNING))

    @staticmethod
    def _sort_key(item: ReviewItem):
        identity = "" if item.primary_resource is None else f"{item.primary_resource.resource_type.value}:{item.primary_resource.resource_id}"
        return (_SEVERITY_ORDER[item.severity], item.category.value, item.title.casefold(), identity, item.item_id)

    @staticmethod
    def _state(workspace, coverage, insights, unfiltered, items, filters):
        if coverage.overall_coverage.total == 0:
            return ReviewState.PROJECT_EMPTY
        if any(item.identity.insight_code == "project.not_evaluated" for item in insights.insights):
            return ReviewState.PROJECT_NOT_EVALUATED
        if not items:
            only_pending = any(item.filter_id == "review.only_pending" and item.parameters.get("value") is True for item in filters)
            if only_pending and not any(item.severity in (InsightSeverity.ERROR, InsightSeverity.WARNING) for item in unfiltered):
                return ReviewState.NO_PENDING
            return ReviewState.NO_ITEMS
        return ReviewState.READY


def _category(identity: ResourceIdentity | None) -> ReviewCategory:
    if identity is None:
        return ReviewCategory.PROJECT
    return {ResourceType.DOCUMENT: ReviewCategory.DOCUMENTS, ResourceType.EVIDENCE: ReviewCategory.EVIDENCES,
            ResourceType.EXECUTION_FACT: ReviewCategory.EXECUTION_FACTS, ResourceType.REQUIREMENT: ReviewCategory.REQUIREMENTS,
            ResourceType.CRITERION: ReviewCategory.REQUIREMENTS}.get(identity.resource_type, ReviewCategory.PROJECT)


def _intent(identity: ResourceIdentity | None, origin: str) -> NavigationIntent | None:
    if identity is None:
        return None
    factories = {ResourceType.DOCUMENT: NavigationIntent.open_document, ResourceType.EVIDENCE: NavigationIntent.open_evidence,
                 ResourceType.EXECUTION_FACT: NavigationIntent.open_execution_fact, ResourceType.REQUIREMENT: NavigationIntent.open_requirement,
                 ResourceType.CRITERION: NavigationIntent.open_criterion, ResourceType.EVALUATION: NavigationIntent.open_evaluation,
                 ResourceType.REPORT: NavigationIntent.open_report}
    return factories[identity.resource_type](identity.resource_id, origin=origin)


__all__ = ["ReviewCategory", "ReviewCategorySummary", "ReviewItem", "ReviewOrigin", "ReviewProjectSummary", "ReviewState", "ReviewWorkspaceService", "ReviewWorkspaceSnapshot"]
