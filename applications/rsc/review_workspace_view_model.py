"""DTOs visuais imutaveis do Review Workspace."""

from __future__ import annotations

from dataclasses import dataclass

from applications.rsc.services.review_workspace_service import ReviewWorkspaceSnapshot
from presentation.navigation_contracts import NavigationIntent
from applications.rsc.operational_actions import ExecuteEvaluationAction


@dataclass(frozen=True, slots=True)
class ReviewItemView:
    item_id: str
    category: str
    severity: str
    title: str
    description: str
    resource_label: str
    origin: str
    navigation_intent: NavigationIntent | None
    operational_action: ExecuteEvaluationAction | None


@dataclass(frozen=True, slots=True)
class ReviewSummaryView:
    project_name: str
    total: int
    categories: tuple[tuple[str, int], ...]
    state: str


@dataclass(frozen=True, slots=True)
class ReviewWorkspaceViewData:
    summary: ReviewSummaryView
    items: tuple[ReviewItemView, ...]
    active_categories: tuple[str, ...]
    active_severities: tuple[str, ...]
    active_origins: tuple[str, ...]
    only_pending: bool
    workspace_revision: int


class ReviewWorkspaceViewModel:
    def __init__(self, snapshot: ReviewWorkspaceSnapshot) -> None:
        if not isinstance(snapshot, ReviewWorkspaceSnapshot):
            raise TypeError("snapshot deve ser ReviewWorkspaceSnapshot.")
        self._data = ReviewWorkspaceViewData(
            ReviewSummaryView(snapshot.project.project_name, len(snapshot.items),
                              tuple((item.category.value, item.total) for item in snapshot.category_summary), snapshot.state.value),
            tuple(ReviewItemView(item.item_id, item.category.value, item.severity.value, item.title, item.description,
                                 "Project" if item.primary_resource is None else f"{item.primary_resource.resource_type.value}: {item.primary_resource.resource_id}",
                                 item.origin.value, item.navigation_intent, item.operational_action) for item in snapshot.items),
            tuple(str(item.parameters["value"]) for item in snapshot.active_filters if item.filter_id == "review.category"),
            tuple(str(item.parameters["value"]) for item in snapshot.active_filters if item.filter_id == "review.severity"),
            tuple(str(item.parameters["value"]) for item in snapshot.active_filters if item.filter_id == "review.origin"),
            any(item.filter_id == "review.only_pending" and item.parameters.get("value") is True for item in snapshot.active_filters),
            snapshot.workspace_revision,
        )

    @property
    def data(self) -> ReviewWorkspaceViewData:
        return self._data


__all__ = ["ReviewItemView", "ReviewSummaryView", "ReviewWorkspaceViewData", "ReviewWorkspaceViewModel"]
