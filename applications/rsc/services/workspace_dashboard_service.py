"""Composicao passiva das fontes oficiais do Workspace Dashboard 2.0."""

from __future__ import annotations

from dataclasses import dataclass

from presentation.coverage import CoverageResult
from presentation.insights import InsightCollection
from presentation.workspace import WorkspaceSnapshot


@dataclass(frozen=True, slots=True)
class WorkspaceDashboardSnapshot:
    """Fontes imutaveis consumidas pela projecao do Dashboard."""

    workspace: WorkspaceSnapshot
    coverage: CoverageResult
    insights: InsightCollection


class WorkspaceDashboardService:
    """Coordena Coverage e Insights; nao interpreta seus resultados."""

    def summarize(
        self, workspace: WorkspaceSnapshot, coverage: CoverageResult,
        insights: InsightCollection,
    ) -> WorkspaceDashboardSnapshot:
        if not isinstance(workspace, WorkspaceSnapshot):
            raise TypeError("workspace deve ser WorkspaceSnapshot.")
        if not isinstance(coverage, CoverageResult):
            raise TypeError("coverage deve ser CoverageResult.")
        if not isinstance(insights, InsightCollection):
            raise TypeError("insights deve ser InsightCollection.")
        return WorkspaceDashboardSnapshot(workspace, coverage, insights)


__all__ = [
    "WorkspaceDashboardService",
    "WorkspaceDashboardSnapshot",
]
