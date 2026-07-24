"""Contratos compartilhados entre módulos da aplicação."""

from .application import Application
from .navigation import DocumentNavigationRequest

__all__ = ["Application", "DocumentNavigationRequest"]
