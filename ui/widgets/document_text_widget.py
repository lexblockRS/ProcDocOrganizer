"""Visualiza o texto integral de uma página sem transformação."""

from PySide6.QtWidgets import QLabel, QPlainTextEdit, QVBoxLayout, QWidget


class DocumentTextWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.message_label = QLabel("Selecione uma página.")
        self.text_edit = QPlainTextEdit()
        self.text_edit.setReadOnly(True)
        self.text_edit.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.message_label)
        layout.addWidget(self.text_edit, 1)

    def set_page(self, page) -> None:
        previous_number = getattr(getattr(self, "_page", None), "page_number", None)
        scroll = self.text_edit.verticalScrollBar().value()
        self._page = page
        if page is None:
            self.clear()
            return
        self.text_edit.setPlainText(page.text)
        self.message_label.setText(
            "" if page.text else "Nenhum texto disponível para esta página."
        )
        if previous_number == page.page_number:
            self.text_edit.verticalScrollBar().setValue(scroll)

    def clear(self) -> None:
        self._page = None
        self.text_edit.clear()
        self.message_label.setText("Selecione uma página.")

