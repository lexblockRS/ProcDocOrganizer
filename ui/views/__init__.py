"""
Views da aplicação.
"""

from .base_view import BaseView
from .home_view import HomeView
from .pdf_view import PdfView
from .search_workspace import SearchWorkspace
from .evidence_workspace import EvidenceWorkspace
from .documents_workspace import DocumentsWorkspace
from .documents_view import DocumentsView
from .activities_view import ActivitiesView
from .functional_assignments_view import FunctionalAssignmentsView
from .functional_exercises_view import FunctionalExercisesView

__all__ = [
    "BaseView",
    "HomeView",
    "PdfView",
    "SearchWorkspace",
    "EvidenceWorkspace",
    "DocumentsWorkspace",
    "DocumentsView",
    "ActivitiesView",
    "FunctionalAssignmentsView",
    "FunctionalExercisesView",
]
