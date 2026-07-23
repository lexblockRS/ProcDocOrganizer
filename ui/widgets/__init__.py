"""
Widgets da interface.
"""

from .project_tree_widget import ProjectTreeWidget
from .search_panel import SearchPanel
from .search_preview_widget import SearchPreviewWidget
from .search_results_widget import SearchResultsWidget
from .evidence_editor_widget import EvidenceEditorWidget
from .evidence_list_widget import EvidenceListWidget
from .evidence_source_status_widget import EvidenceSourceStatusWidget
from .document_list_widget import DocumentListWidget
from .document_metadata_widget import DocumentMetadataWidget
from .document_page_list_widget import DocumentPageListWidget
from .document_text_widget import DocumentTextWidget

__all__ = [
    "ProjectTreeWidget",
    "SearchPanel",
    "SearchPreviewWidget",
    "SearchResultsWidget",
    "EvidenceEditorWidget",
    "EvidenceListWidget",
    "EvidenceSourceStatusWidget",
    "DocumentListWidget",
    "DocumentMetadataWidget",
    "DocumentPageListWidget",
    "DocumentTextWidget",
]
