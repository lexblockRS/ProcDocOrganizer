"""
Visualizador integrado de arquivos PDF.
"""

from pathlib import Path

from PySide6.QtCore import QPointF
from PySide6.QtPdf import QPdfDocument, QPdfSearchModel
from PySide6.QtPdfWidgets import QPdfView
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QLayout,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)


class PdfView(QWidget):
    """
    Exibe um documento PDF com navegação, zoom e busca.
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        self.document = QPdfDocument(self)
        self.search_model = QPdfSearchModel(self)

        self._build_ui()
        self._connect_signals()
        self.clear_document()

    # ------------------------------------------------------------------

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSizeConstraint(
            QLayout.SizeConstraint.SetNoConstraint
        )

        controls = QHBoxLayout()

        self.previous_button = QPushButton("Página anterior")
        self.next_button = QPushButton("Próxima página")

        self.page_input = QSpinBox()
        self.page_input.setPrefix("Página ")

        self.page_count_label = QLabel("de 0")

        self.zoom_out_button = QPushButton("-")
        self.zoom_in_button = QPushButton("+")
        self.fit_width_button = QPushButton("Ajustar largura")
        self.fit_page_button = QPushButton("Ajustar página")
        self.zoom_label = QLabel("100%")

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Buscar no documento")
        self.previous_result_button = QPushButton("Resultado anterior")
        self.next_result_button = QPushButton("Próximo resultado")
        self.search_count_label = QLabel("0 resultados")

        for widget in (
            self.previous_button,
            self.next_button,
            self.page_input,
            self.zoom_out_button,
            self.zoom_in_button,
            self.fit_width_button,
            self.fit_page_button,
            self.search_input,
            self.previous_result_button,
            self.next_result_button,
        ):
            controls.addWidget(widget)

        controls.addWidget(self.page_count_label)
        controls.addWidget(self.zoom_label)
        controls.addWidget(self.search_count_label)

        self.message_label = QLabel()

        self.pdf_view = QPdfView(self)
        self.pdf_view.setDocument(self.document)
        self.search_model.setDocument(self.document)
        self.pdf_view.setSearchModel(self.search_model)
        self.pdf_view.setZoomMode(QPdfView.ZoomMode.FitInView)

        layout.addLayout(controls)
        layout.addWidget(self.message_label)
        layout.addWidget(self.pdf_view)

    # ------------------------------------------------------------------

    def _connect_signals(self):
        self.previous_button.clicked.connect(self._show_previous_page)
        self.next_button.clicked.connect(self._show_next_page)
        self.page_input.valueChanged.connect(self._show_page)
        self.zoom_out_button.clicked.connect(self._zoom_out)
        self.zoom_in_button.clicked.connect(self._zoom_in)
        self.fit_width_button.clicked.connect(self._fit_to_width)
        self.fit_page_button.clicked.connect(self._fit_in_view)
        self.search_input.textChanged.connect(self._search)
        self.previous_result_button.clicked.connect(self._show_previous_result)
        self.next_result_button.clicked.connect(self._show_next_result)

        self.document.pageCountChanged.connect(self._update_page_count)
        self.pdf_view.pageNavigator().currentPageChanged.connect(
            self._update_current_page
        )
        self.pdf_view.zoomFactorChanged.connect(self._update_zoom_label)
        self.search_model.countChanged.connect(self._update_search_count)

    # ------------------------------------------------------------------

    def open_document(self, file_path: Path) -> None:
        """
        Carrega um arquivo PDF para visualização.
        """

        self.clear_document()

        if file_path.suffix.lower() != ".pdf":
            self._show_error("O documento selecionado não é um arquivo PDF.")
            return

        if not file_path.exists():
            self._show_error("O arquivo do documento não foi encontrado.")
            return

        error = self.document.load(str(file_path))

        if error != QPdfDocument.Error.None_:
            self._show_error("Não foi possível abrir o arquivo PDF.")
            return

        self.message_label.clear()
        self._set_controls_enabled(True)
        self._update_page_count(self.document.pageCount())
        self._show_page(1)

    # ------------------------------------------------------------------

    def clear_document(self) -> None:
        """
        Limpa o documento atualmente exibido.
        """

        self.document.close()
        self.search_model.setSearchString("")
        self.search_input.clear()
        self.page_input.setRange(0, 0)
        self.page_count_label.setText("de 0")
        self.search_count_label.setText("0 resultados")
        self.message_label.clear()
        self._set_controls_enabled(False)

    # ------------------------------------------------------------------

    def show_page(self, page: int) -> None:
        """
        Navega para uma página já carregada no visualizador.
        """

        self._show_page(page)

    # ------------------------------------------------------------------

    def current_page(self) -> int:
        """
        Retorna a página atualmente exibida, iniciada em 1.
        """

        return self.page_input.value()

    # ------------------------------------------------------------------

    def _show_error(self, message: str) -> None:
        self.message_label.setText(message)
        self._set_controls_enabled(False)

    # ------------------------------------------------------------------

    def _set_controls_enabled(self, enabled: bool) -> None:
        for widget in (
            self.previous_button,
            self.next_button,
            self.page_input,
            self.zoom_out_button,
            self.zoom_in_button,
            self.fit_width_button,
            self.fit_page_button,
            self.search_input,
            self.previous_result_button,
            self.next_result_button,
        ):
            widget.setEnabled(enabled)

    # ------------------------------------------------------------------

    def _update_page_count(self, page_count: int) -> None:
        self.page_input.setRange(1, max(page_count, 1))
        self.page_count_label.setText(f"de {page_count}")

    # ------------------------------------------------------------------

    def _update_current_page(self, page: int) -> None:
        self.page_input.blockSignals(True)
        self.page_input.setValue(page + 1)
        self.page_input.blockSignals(False)

    # ------------------------------------------------------------------

    def _show_page(self, page: int) -> None:
        if self.document.pageCount() == 0:
            return

        page_index = page - 1

        self.pdf_view.pageNavigator().jump(
            page_index,
            QPointF(),
            self.pdf_view.zoomFactor(),
        )

    # ------------------------------------------------------------------

    def _show_previous_page(self) -> None:
        self._show_page(max(1, self.page_input.value() - 1))

    # ------------------------------------------------------------------

    def _show_next_page(self) -> None:
        self._show_page(
            min(self.document.pageCount(), self.page_input.value() + 1)
        )

    # ------------------------------------------------------------------

    def _zoom_out(self) -> None:
        self._set_zoom_factor(self.pdf_view.zoomFactor() - 0.1)

    # ------------------------------------------------------------------

    def _zoom_in(self) -> None:
        self._set_zoom_factor(self.pdf_view.zoomFactor() + 0.1)

    # ------------------------------------------------------------------

    def _fit_to_width(self) -> None:
        self.pdf_view.setZoomMode(QPdfView.ZoomMode.FitToWidth)

    # ------------------------------------------------------------------

    def _fit_in_view(self) -> None:
        self.pdf_view.setZoomMode(QPdfView.ZoomMode.FitInView)

    # ------------------------------------------------------------------

    def _set_zoom_factor(self, factor: float) -> None:
        self.pdf_view.setZoomMode(QPdfView.ZoomMode.Custom)
        self.pdf_view.setZoomFactor(max(0.1, factor))

    # ------------------------------------------------------------------

    def _update_zoom_label(self, factor: float) -> None:
        self.zoom_label.setText(f"{round(factor * 100)}%")

    # ------------------------------------------------------------------

    def _search(self, search_text: str) -> None:
        self.search_model.setSearchString(search_text)
        self.pdf_view.setCurrentSearchResultIndex(-1)

    # ------------------------------------------------------------------

    def _update_search_count(self) -> None:
        count = self.search_model.count()
        self.search_count_label.setText(f"{count} resultados")

    # ------------------------------------------------------------------

    def _show_previous_result(self) -> None:
        self._show_search_result(-1)

    # ------------------------------------------------------------------

    def _show_next_result(self) -> None:
        self._show_search_result(1)

    # ------------------------------------------------------------------

    def _show_search_result(self, step: int) -> None:
        count = self.search_model.count()

        if count == 0:
            return

        current = self.pdf_view.currentSearchResultIndex()
        result_index = (current + step) % count

        self.pdf_view.setCurrentSearchResultIndex(result_index)
        self.pdf_view.pageNavigator().jump(
            self.search_model.resultAtIndex(result_index)
        )
