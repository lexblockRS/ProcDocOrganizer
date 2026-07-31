"""Adapters físicos neutros da plataforma."""

from .workspace import (
    Workspace,
    WorkspaceDirectory,
    WorkspaceError,
    WorkspaceFactory,
    WorkspaceLocator,
)

__all__ = [
    "Workspace",
    "WorkspaceDirectory",
    "WorkspaceError",
    "WorkspaceFactory",
    "WorkspaceLocator",
]
