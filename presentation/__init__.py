"""Componentes da camada de apresentação."""

from .application_state import (
    ApplicationState,
    ApplicationStateSnapshot,
    ApplicationStateStore,
    InvalidApplicationStateTransition,
)
from .selection import (
    InvalidSelectionContext,
    InvalidSelectionIdentity,
    SelectionContext,
    SelectionContractError,
    SelectionIdentity,
    SelectionKind,
    SelectionSnapshot,
    SelectionStore,
)
from .perspectives import (
    DuplicatePerspective,
    InvalidPerspectiveDefinition,
    PerspectiveContractError,
    PerspectiveDefinition,
    PerspectiveId,
    PerspectiveNotRegistered,
    PerspectiveSnapshot,
    PerspectiveStore,
)
from .presentation_context import (
    PresentationContextStore,
    PresentationSnapshot,
)
from .workspace import (
    InvalidWorkspacePerspective,
    WorkspaceContractError,
    WorkspaceSnapshot,
    WorkspaceState,
    WorkspaceStore,
)
from .navigation import NavigationController
from .operations import (
    CancellationToken,
    OperationCancelled,
    OperationContext,
    OperationExecutor,
    OperationId,
    OperationWork,
)
from .notifications import (
    Notification,
    NotificationCenter,
    NotificationLevel,
)

__all__ = [
    "ApplicationState",
    "ApplicationStateSnapshot",
    "ApplicationStateStore",
    "InvalidApplicationStateTransition",
    "DuplicatePerspective",
    "InvalidPerspectiveDefinition",
    "PerspectiveContractError",
    "PerspectiveDefinition",
    "PerspectiveId",
    "PerspectiveNotRegistered",
    "PerspectiveSnapshot",
    "PerspectiveStore",
    "PresentationContextStore",
    "PresentationSnapshot",
    "InvalidWorkspacePerspective",
    "WorkspaceContractError",
    "WorkspaceSnapshot",
    "WorkspaceState",
    "WorkspaceStore",
    "NavigationController",
    "CancellationToken",
    "OperationCancelled",
    "OperationContext",
    "OperationExecutor",
    "OperationId",
    "OperationWork",
    "Notification",
    "NotificationCenter",
    "NotificationLevel",
    "InvalidSelectionContext",
    "InvalidSelectionIdentity",
    "SelectionContext",
    "SelectionContractError",
    "SelectionIdentity",
    "SelectionKind",
    "SelectionSnapshot",
    "SelectionStore",
]
