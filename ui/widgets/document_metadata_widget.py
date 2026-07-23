"""Apresenta metadados documentais de interesse do usuário."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFormLayout, QLabel, QWidget


class DocumentMetadataWidget(QWidget):
    _STATUS_LABELS = {
        "processed": "Processado",
        "not_processed": "Não processado",
        "processing": "Em processamento",
        "pending": "Pendente",
        "failed": "Falha no processamento",
        "cancelled": "Cancelado",
        "ocr_required": "OCR necessário",
    }

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.values = {}
        layout = QFormLayout(self)
        fields = (
            ("name", "Nome"), ("type", "Tipo"), ("date", "Data"),
            ("status", "Situação"), ("pages", "Quantidade de páginas"),
            ("ocr", "OCR utilizado"), ("source", "Origem do texto"),
            ("processed", "Data de processamento"),
        )
        for key, label in fields:
            value = QLabel("Não informado")
            value.setWordWrap(True)
            value.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            layout.addRow(f"{label}:", value)
            self.values[key] = value

    def set_details(self, details) -> None:
        if details is None:
            self.clear()
            return
        summary = details.summary
        values = {
            "name": summary.name,
            "type": summary.document_type,
            "date": summary.document_date,
            "status": self._STATUS_LABELS.get(
                summary.processing_status, summary.processing_status
            ),
            "pages": str(details.page_count),
            "ocr": "Sim" if details.ocr_used else "Não",
            "source": details.text_source,
            "processed": details.processed_at,
        }
        for key, value in values.items():
            self.values[key].setText(str(value) if value not in (None, "") else "Não informado")

    def show_unprocessed(self) -> None:
        self.values["status"].setText("Este documento ainda não foi processado.")

    def clear(self) -> None:
        for value in self.values.values():
            value.setText("Não informado")
