"""Fronteira de apresentação do Dashboard."""

from .controller import DashboardController
from .projections import (
    DashboardProjection,
    DashboardState,
    DocumentSummaryProjection,
    EvidenceSummaryProjection,
    ProjectSummaryProjection,
)
from .service import DashboardService

__all__ = [
    "DashboardController",
    "DashboardProjection",
    "DashboardService",
    "DashboardState",
    "DocumentSummaryProjection",
    "EvidenceSummaryProjection",
    "ProjectSummaryProjection",
]
