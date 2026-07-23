"""Controles visuais de entrada da pesquisa."""

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QHBoxLayout, QLabel, QLineEdit, QPushButton, QVBoxLayout, QWidget


class SearchPanel(QWidget):
    search_requested = Signal(str)
    clear_requested = Signal()
    create_evidence_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        controls = QHBoxLayout()

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Pesquisar no conteúdo dos documentos")
        self.search_button = QPushButton("Pesquisar")
        self.clear_button = QPushButton("Limpar")
        self.create_evidence_button = QPushButton("Criar evidência")
        self.create_evidence_button.setEnabled(False)
        self.create_evidence_button.setToolTip(
            "Preparar uma evidência a partir do resultado selecionado"
        )
        self.result_count_label = QLabel("Resultados: 0")
        self.message_label = QLabel()
        self.message_label.setWordWrap(True)

        controls.addWidget(self.search_input, 1)
        controls.addWidget(self.search_button)
        controls.addWidget(self.clear_button)
        controls.addWidget(self.create_evidence_button)
        layout.addLayout(controls)
        layout.addWidget(self.result_count_label)
        layout.addWidget(self.message_label)

        self.search_input.returnPressed.connect(self._request_search)
        self.search_button.clicked.connect(self._request_search)
        self.clear_button.clicked.connect(self.clear_requested)
        self.create_evidence_button.clicked.connect(self.create_evidence_requested)

    def _request_search(self) -> None:
        self.search_requested.emit(self.search_input.text())

    def clear(self) -> None:
        self.search_input.clear()
        self.set_result_count(0)
        self.show_message("")

    def focus_search(self) -> None:
        self.search_input.setFocus()

    def set_result_count(self, count: int) -> None:
        self.result_count_label.setText(f"Resultados: {count}")

    def show_message(self, message: str) -> None:
        self.message_label.setText(message)

    def set_create_evidence_enabled(self, enabled: bool) -> None:
        self.create_evidence_button.setEnabled(enabled)
