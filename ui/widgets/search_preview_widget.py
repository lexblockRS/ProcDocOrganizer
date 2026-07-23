"""Apresentação de um SearchHit selecionado."""

from PySide6.QtWidgets import QFormLayout, QLabel, QWidget

from services.search import SearchHit


class SearchPreviewWidget(QWidget):
    EMPTY_VALUE = "—"

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QFormLayout(self)
        self.title_value = QLabel()
        self.type_value = QLabel()
        self.date_value = QLabel()
        self.page_value = QLabel()
        self.file_value = QLabel()
        self.file_value.setWordWrap(True)
        layout.addRow("Título", self.title_value)
        layout.addRow("Tipo", self.type_value)
        layout.addRow("Data", self.date_value)
        layout.addRow("Página", self.page_value)
        layout.addRow("Arquivo", self.file_value)
        self.clear()

    def set_result(self, result: SearchHit) -> None:
        self.title_value.setText(result.document_name or self.EMPTY_VALUE)
        self.type_value.setText(self.EMPTY_VALUE)
        self.date_value.setText(self.EMPTY_VALUE)
        self.page_value.setText(str(result.page_number))
        self.file_value.setText(self.EMPTY_VALUE)

    def clear(self) -> None:
        for label in (
            self.title_value, self.type_value, self.date_value,
            self.page_value, self.file_value,
        ):
            label.setText(self.EMPTY_VALUE)
