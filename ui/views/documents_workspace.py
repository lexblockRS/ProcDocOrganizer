"""Workspace visual, somente leitura, para navegação documental."""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QGroupBox, QHBoxLayout, QLabel, QPushButton, QSplitter, QVBoxLayout,
    QWidget,
)

from ui.widgets.document_list_widget import DocumentListWidget
from ui.widgets.document_metadata_widget import DocumentMetadataWidget
from ui.widgets.document_page_list_widget import DocumentPageListWidget
from ui.widgets.document_text_widget import DocumentTextWidget


class DocumentsWorkspace(QWidget):
    document_selected = Signal(object)
    page_selected = Signal(object)
    create_evidence_requested = Signal()
    import_requested = Signal()
    remove_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.state = "no_project"
        self.catalog = ()
        self.details = None
        self.pages = ()
        self.current_page = None

        title = QLabel("Documentos")
        title.setStyleSheet("font-size: 18px; font-weight: bold;")
        self.status_label = QLabel()
        self.message_label = QLabel()
        self.message_label.setWordWrap(True)
        self.import_button = QPushButton("Importar Documento")
        self.import_button.setAccessibleName("Importar documento")
        self.import_button.setToolTip(
            "Copiar um documento para o acervo do projeto"
        )
        self.remove_button = QPushButton("Remover Documento")
        self.remove_button.setAccessibleName("Remover documento")
        self.remove_button.setToolTip(
            "Remover o documento selecionado do acervo"
        )
        self.remove_button.setEnabled(False)
        self.import_button.clicked.connect(self.import_requested)
        self.remove_button.clicked.connect(self.remove_requested)
        actions = QHBoxLayout()
        actions.addWidget(self.import_button)
        actions.addWidget(self.remove_button)
        actions.addStretch(1)

        self.document_list_widget = DocumentListWidget()
        self.metadata_widget = DocumentMetadataWidget()
        self.page_list_widget = DocumentPageListWidget()
        self.text_widget = DocumentTextWidget()

        documents_group = self._group("Documentos", self.document_list_widget)
        metadata_group = self._group("Informações", self.metadata_widget)
        pages_group = self._group("Páginas", self.page_list_widget)
        text_group = self._group("Texto", self.text_widget)

        middle = QSplitter(Qt.Orientation.Vertical)
        middle.addWidget(metadata_group)
        middle.addWidget(pages_group)
        middle.setStretchFactor(0, 1)
        middle.setStretchFactor(1, 2)
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setChildrenCollapsible(False)
        splitter.addWidget(documents_group)
        splitter.addWidget(middle)
        splitter.addWidget(text_group)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 1)
        splitter.setStretchFactor(2, 2)
        splitter.setSizes([300, 360, 600])
        self.splitter = splitter

        layout = QVBoxLayout(self)
        layout.addWidget(title)
        layout.addWidget(self.status_label)
        layout.addWidget(self.message_label)
        layout.addLayout(actions)
        layout.addWidget(splitter, 1)

        self.document_list_widget.document_selected.connect(
            self.document_selected
        )
        self.page_list_widget.page_selected.connect(self.page_selected)
        self.setTabOrder(
            self.document_list_widget.list_widget, self.metadata_widget
        )
        self.setTabOrder(
            self.metadata_widget, self.page_list_widget.list_widget
        )
        self.setTabOrder(
            self.page_list_widget.list_widget, self.text_widget.text_edit
        )
        self.clear()

    @staticmethod
    def _group(title, widget):
        group = QGroupBox(title)
        layout = QVBoxLayout(group)
        layout.addWidget(widget)
        return group

    def set_state(self, state: str) -> None:
        self.state = state
        messages = {
            "no_project": "Nenhum projeto aberto.",
            "loading": "Carregando documentos...",
            "empty": "Nenhum documento importado.",
            "error": "Não foi possível carregar os documentos do projeto.",
            "ready": "",
        }
        self.status_label.setText(messages.get(state, state))

    def set_catalog(self, catalog) -> None:
        self.catalog = tuple(catalog)
        self.document_list_widget.set_catalog(self.catalog)

    def set_details(self, details) -> None:
        self.details = details
        self.metadata_widget.set_details(details)
        self.remove_button.setEnabled(details is not None)
        if details is not None and not details.summary.has_processing_result:
            self.metadata_widget.show_unprocessed()

    def set_pages(self, pages) -> None:
        self.pages = tuple(pages)
        self.page_list_widget.set_pages(self.pages)

    def set_page(self, page) -> None:
        self.current_page = page
        self.text_widget.set_page(page)

    def select_document(self, identity) -> bool:
        return self.document_list_widget.select_identity(identity)

    def select_page(self, page_number) -> bool:
        return self.page_list_widget.select_page(page_number)

    def clear_document(self) -> None:
        self.details = None
        self.pages = ()
        self.current_page = None
        self.metadata_widget.clear()
        self.page_list_widget.clear()
        self.text_widget.clear()
        self.remove_button.setEnabled(False)

    def show_message(self, message: str) -> None:
        self.message_label.setText(message)

    def clear(self) -> None:
        self.catalog = ()
        self.document_list_widget.clear()
        self.clear_document()
        self.message_label.clear()
        self.set_state("no_project")

    def on_project_opened(self, _project) -> None:
        self.set_state("loading")

    def on_project_closed(self) -> None:
        self.clear()
