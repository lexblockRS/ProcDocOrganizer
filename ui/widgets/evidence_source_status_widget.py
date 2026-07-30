"""Apresenta a disponibilidade da fonte de uma evidência."""

from PySide6.QtWidgets import QLabel, QWidget, QFormLayout, QVBoxLayout


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
        self.document_label = QLabel("—")
        self.document_label.setTextInteractionFlags(
            self.document_label.textInteractionFlags()
        )
        self.page_label = QLabel("Não informada")
        self.snippet_label = QLabel("Não informado")
        self.snippet_label.setWordWrap(True)
        self.checked_at_label = QLabel("Não registrada")
        details = QFormLayout()
        details.addRow("Documento:", self.document_label)
        details.addRow("Página:", self.page_label)
        details.addRow("Trecho:", self.snippet_label)
        details.addRow("Última verificação:", self.checked_at_label)
        layout = QVBoxLayout(self)
        layout.addWidget(self.label)
        layout.addLayout(details)
        self.set_status(None)

    def set_status(self, status) -> None:
        value = getattr(status, "value", status)
        self.label.setText(self.MESSAGES.get(value, self.MESSAGES[None]))

    def set_origin(self, draft, status, checked_at=None) -> None:
        self.set_status(status)
        self.document_label.setText(
            draft.document_identity or "Não informado"
        )
        self.page_label.setText(
            str(draft.page_number)
            if draft.page_number is not None
            else "Não informada"
        )
        self.snippet_label.setText(
            draft.source_snippet or "Não informado"
        )
        self.checked_at_label.setText(
            str(checked_at) if checked_at else "Não registrada"
        )

