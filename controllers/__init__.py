"""Controladores da aplicação."""

from .search_controller import SearchController
from .evidence_controller import EvidenceController, EvidenceEditorMode
from .documents_controller import DocumentsController

__all__ = [
    "SearchController", "EvidenceController", "EvidenceEditorMode",
    "DocumentsController",
]
