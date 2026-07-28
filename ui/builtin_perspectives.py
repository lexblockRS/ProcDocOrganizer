"""Composição das perspectivas visuais nativas da aplicação."""

from collections.abc import Callable, Mapping

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

from core.contribution_manager import ContributionManager
from ui.views.documents_view import DocumentsView
from ui.views.evidence_workspace import EvidenceWorkspace
from ui.views.home_view import HomeView
from ui.views.pdf_view import PdfView
from ui.views.search_workspace import SearchWorkspace


def create_builtin_perspective_views(
    contribution_manager: ContributionManager,
    actions: Mapping[str, Callable[[], None]],
) -> dict[str, QWidget]:
    """Materializa Views nativas sem expor tipos concretos à MainWindow."""
    home = HomeView(contribution_manager)
    documents = DocumentsView()
    views = {
        "home": home,
        "documents": documents,
        "timeline": _placeholder(
            "Timeline",
            "A perspectiva de linha do tempo será disponibilizada "
            "em uma etapa futura.",
        ),
        "evidence": EvidenceWorkspace(),
        "reports": _placeholder(
            "Relatórios",
            "A perspectiva de relatórios será disponibilizada "
            "em uma etapa futura.",
        ),
        "pdf": PdfView(),
        "search": SearchWorkspace(),
    }

    home.new_project_requested.connect(actions["new_project"])
    home.open_project_requested.connect(actions["open_project"])
    home.documents_requested.connect(actions["documents"])
    home.search_requested.connect(actions["search"])
    home.evidences_requested.connect(actions["evidence"])
    home.import_documents_requested.connect(actions["import_documents"])
    home.process_documents_requested.connect(actions["process_documents"])
    documents.import_requested.connect(actions["import_documents"])
    return views


def _placeholder(title: str, description: str) -> QWidget:
    widget = QWidget()
    widget.setObjectName(f"{title.casefold()}Perspective")
    layout = QVBoxLayout(widget)
    heading = QLabel(title)
    heading.setObjectName("perspectiveTitle")
    description_label = QLabel(description)
    description_label.setWordWrap(True)
    layout.addStretch()
    layout.addWidget(
        heading,
        alignment=Qt.AlignmentFlag.AlignCenter,
    )
    layout.addWidget(
        description_label,
        alignment=Qt.AlignmentFlag.AlignCenter,
    )
    layout.addStretch()
    return widget
