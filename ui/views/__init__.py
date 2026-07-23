"""
Views da aplicação.
"""

from .base_view import BaseView
from .home_view import HomeView
from .pdf_view import PdfView
from .search_workspace import SearchWorkspace
from .evidence_workspace import EvidenceWorkspace
from .documents_workspace import DocumentsWorkspace

__all__ = [
    "BaseView",
    "HomeView",
    "PdfView",
    "SearchWorkspace",
    "EvidenceWorkspace",
    "DocumentsWorkspace",
]
