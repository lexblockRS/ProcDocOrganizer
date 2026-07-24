"""Contratos compartilhados entre módulos da aplicação."""

from .application import Application
from .application_contribution import ActionContribution
from .navigation import DocumentNavigationRequest

__all__ = [
    "ActionContribution",
    "Application",
    "DocumentNavigationRequest",
]
