"""Apresenta a disponibilidade da fonte de uma evidência."""

from PySide6.QtWidgets import QLabel, QWidget, QVBoxLayout


class EvidenceSourceStatusWidget(QWidget):
    MESSAGES = {
        "available": "Documento de origem disponível",
        "unavailable": "Documento de origem temporariamente indisponível",
        None: "Nenhuma evidência selecionada",
    }

    def __init__(self, parent=None):
        super().__init__(parent)
        self.label = QLabel()
        self.label.setWordWrap(True)
        layout = QVBoxLayout(self)
        layout.addWidget(self.label)
        self.set_status(None)

    def set_status(self, status) -> None:
        value = getattr(status, "value", status)
        self.label.setText(self.MESSAGES.get(value, self.MESSAGES[None]))

