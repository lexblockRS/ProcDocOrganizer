"""Contratos compartilhados entre módulos da aplicação."""

from .application import Application
from .application_contribution import ActionContribution
from .application_descriptor import (
    ApplicationDescriptor,
    Version,
    create_transitional_application_descriptor,
)
from .application_module import ApplicationModule
from .capabilities import (
    CLOCK_CAPABILITY,
    DOCUMENT_ENGINE_CAPABILITY,
    ID_GENERATOR_CAPABILITY,
    KNOWLEDGE_ENGINE_CAPABILITY,
    LOGGING_CAPABILITY,
    NAVIGATION_CAPABILITY,
    Capability,
    CapabilityProvider,
    ClockCapability,
    DocumentEngineCapability,
    IdGeneratorCapability,
    KnowledgeEngineCapability,
    LoggingCapability,
    NavigationCapability,
)
from .contribution import (
    ContributionCategory,
    ContributionRegistration,
)
from .dashboard_contribution import (
    DashboardContribution,
    DashboardRefreshPolicy,
)
from .lifecycle import (
    VALID_APPLICATION_LIFECYCLE_TRANSITIONS,
    ApplicationLifecycleState,
    ApplicationLifecycleTransition,
)
from .navigation import DocumentNavigationRequest

__all__ = [
    "ActionContribution",
    "Application",
    "ApplicationDescriptor",
    "ApplicationLifecycleState",
    "ApplicationLifecycleTransition",
    "ApplicationModule",
    "CLOCK_CAPABILITY",
    "Capability",
    "CapabilityProvider",
    "ClockCapability",
    "ContributionCategory",
    "ContributionRegistration",
    "DOCUMENT_ENGINE_CAPABILITY",
    "DashboardContribution",
    "DashboardRefreshPolicy",
    "DocumentNavigationRequest",
    "DocumentEngineCapability",
    "ID_GENERATOR_CAPABILITY",
    "IdGeneratorCapability",
    "KNOWLEDGE_ENGINE_CAPABILITY",
    "KnowledgeEngineCapability",
    "LOGGING_CAPABILITY",
    "LoggingCapability",
    "NAVIGATION_CAPABILITY",
    "NavigationCapability",
    "VALID_APPLICATION_LIFECYCLE_TRANSITIONS",
    "Version",
    "create_transitional_application_descriptor",
]
