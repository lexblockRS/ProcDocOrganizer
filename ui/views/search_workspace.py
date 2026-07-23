"""Composição visual do workspace de pesquisa."""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QGroupBox, QHBoxLayout, QSplitter, QVBoxLayout, QWidget

from services.search import SearchResultPage
from ui.widgets.search_panel import SearchPanel
from ui.widgets.search_preview_widget import SearchPreviewWidget
from ui.widgets.search_results_widget import SearchResultsWidget


class SearchWorkspace(QWidget):
    search_requested = Signal(str)
    clear_requested = Signal()
    result_selected = Signal(object)
    create_evidence_requested = Signal(object)
    open_result_requested = Signal(object)

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        self.search_panel = SearchPanel()
        self.results_widget = SearchResultsWidget()
        self.preview_widget = SearchPreviewWidget()
        self.result_page = None

        results_group = QGroupBox("Lista de resultados")
        results_layout = QVBoxLayout(results_group)
        results_layout.addWidget(self.results_widget)
        preview_group = QGroupBox("Painel de detalhes")
        preview_layout = QHBoxLayout(preview_group)
        preview_layout.addWidget(self.preview_widget)
        splitter = QSplitter(Qt.Orientation.Vertical)
        splitter.addWidget(results_group)
        splitter.addWidget(preview_group)
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 1)

        layout.addWidget(self.search_panel)
        layout.addWidget(splitter, 1)
        self.search_panel.search_requested.connect(self.search_requested)
        self.search_panel.clear_requested.connect(self.clear_requested)
        self.results_widget.result_selected.connect(self.result_selected)
        self.results_widget.result_selected.connect(self._selection_changed)
        self.results_widget.result_activated.connect(
            self.open_result_requested
        )
        self.search_panel.create_evidence_requested.connect(
            self._request_create_evidence
        )

    def set_results(self, results) -> None:
        if isinstance(results, SearchResultPage):
            self.result_page = results
            hits = results.hits
        else:
            self.result_page = None
            hits = tuple(results)
        self.results_widget.set_results(hits)
        self.search_panel.set_result_count(len(hits))
        self.search_panel.set_create_evidence_enabled(False)
        self.preview_widget.clear()

    def show_result(self, result) -> None:
        self.preview_widget.set_result(result)

    def show_message(self, message: str) -> None:
        self.search_panel.show_message(message)

    def clear(self) -> None:
        self.result_page = None
        self.search_panel.clear()
        self.results_widget.clear()
        self.preview_widget.clear()
        self.search_panel.set_create_evidence_enabled(False)

    def selected_result(self):
        return self.results_widget.current_result()

    def _selection_changed(self, result) -> None:
        self.search_panel.set_create_evidence_enabled(result is not None)

    def _request_create_evidence(self) -> None:
        self.create_evidence_requested.emit(self.selected_result())

    def focus_search(self) -> None:
        self.search_panel.focus_search()

    def on_project_opened(self, project) -> None:
        self.clear()

    def on_project_closed(self) -> None:
        self.clear()
