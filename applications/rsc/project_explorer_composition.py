"""Composição concreta do Application Service do Project Explorer."""

from __future__ import annotations

from applications.rsc.services.project_explorer_service import (
    ProjectExplorerApplicationService,
)
from database import (
    SQLiteEvidenceStore,
    SQLiteExecutionBindingStore,
    SQLiteExecutionFactStore,
)
from core.operational_project_state import OperationalProjectStateStore
from platform_sdk import Project


def create_project_explorer_service(
    session,
) -> ProjectExplorerApplicationService:
    project = session.project
    return create_project_explorer_service_for_project(
        project, session.document_repository
    )


def create_project_explorer_service_for_project(
    project, document_repository
) -> ProjectExplorerApplicationService:
    database_path = project.project_path / project.database
    operational_state = OperationalProjectStateStore(database_path)
    projected_project = Project(
        project_id=operational_state.project_id,
        name=project.project_name,
        application_id=project.application,
        revision=operational_state.current(),
    )
    return ProjectExplorerApplicationService(
        projected_project,
        SQLiteEvidenceStore(database_path),
        SQLiteExecutionFactStore(database_path),
        SQLiteExecutionBindingStore(database_path),
        document_repository,
        operational_state,
        project.project_path,
    )


__all__ = [
    "create_project_explorer_service",
    "create_project_explorer_service_for_project",
]
