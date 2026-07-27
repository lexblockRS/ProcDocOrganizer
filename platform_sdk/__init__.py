"""Superfície pública para desenvolvimento de Applications."""

from contracts import (
    ApplicationDescriptor,
    ApplicationLifecycleState,
    ApplicationLifecycleTransition,
    ApplicationModule,
    ContributionCategory,
    ContributionRegistration,
    DashboardContribution,
    DashboardRefreshPolicy,
    VALID_APPLICATION_LIFECYCLE_TRANSITIONS,
    Version,
)
from core.application_registry import ApplicationRegistry
from core.application_runtime import ApplicationRuntime
from core.contribution_manager import ContributionManager
from core.platform_session import PlatformSession
from core.project_context import ProjectContext
from core.project_session_factory import ProjectSessionFactory
from core.session_context import SessionContext

from .application_catalog import ApplicationCatalog, ApplicationProvider
from .contributions import (
    ActionContribution,
    MenuContribution,
    ToolbarContribution,
    ViewContribution,
)
from .presentation import (
    ApplicationController,
    ApplicationView,
    DashboardCard,
    DashboardPanel,
)

__all__ = [
    "ActionContribution",
    "ApplicationCatalog",
    "ApplicationController",
    "ApplicationDescriptor",
    "ApplicationLifecycleState",
    "ApplicationLifecycleTransition",
    "ApplicationModule",
    "ApplicationProvider",
    "ApplicationRegistry",
    "ApplicationRuntime",
    "ApplicationView",
    "ContributionCategory",
    "ContributionManager",
    "ContributionRegistration",
    "DashboardContribution",
    "DashboardCard",
    "DashboardPanel",
    "DashboardRefreshPolicy",
    "MenuContribution",
    "PlatformSession",
    "ProjectContext",
    "ProjectSessionFactory",
    "SessionContext",
    "ToolbarContribution",
    "VALID_APPLICATION_LIFECYCLE_TRANSITIONS",
    "Version",
    "ViewContribution",
]
