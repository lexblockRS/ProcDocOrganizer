"""Composição concreta do Application Service do Project Explorer."""

from __future__ import annotations

from pathlib import Path

from applications.rsc.services.project_explorer_service import (
    ProjectExplorerApplicationService,
)
from database import (
    SQLiteEvidenceStore,
    SQLiteExecutionBindingStore,
    SQLiteExecutionFactStore,
    SQLiteProjectStore,
)
from platform_infrastructure import WorkspaceFactory, WorkspaceLocator


def create_project_explorer_service(
    *, database_path: str | Path, workspace_base: str | Path,
    application_registry,
) -> ProjectExplorerApplicationService:
    return ProjectExplorerApplicationService(
        SQLiteProjectStore(database_path),
        SQLiteEvidenceStore(database_path),
        SQLiteExecutionFactStore(database_path),
        SQLiteExecutionBindingStore(database_path),
        WorkspaceFactory(workspace_base),
        WorkspaceLocator(workspace_base),
        application_registry,
    )


__all__ = ["create_project_explorer_service"]
