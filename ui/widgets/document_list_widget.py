"""Catálogo visual de documentos importados."""

from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtWidgets import QListWidget, QListWidgetItem, QStyle, QVBoxLayout, QWidget


class DocumentListWidget(QWidget):
    document_selected = Signal(object)
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
        self.list_widget = QListWidget()
        self.list_widget.setAlternatingRowColors(True)
        self.list_widget.setIconSize(QSize(24, 24))
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.list_widget)
        self.list_widget.currentItemChanged.connect(self._changed)

    def set_catalog(self, catalog) -> None:
        selected = self.current_identity()
        self.list_widget.blockSignals(True)
        try:
            self.list_widget.clear()
            icon = self.style().standardIcon(QStyle.StandardPixmap.SP_FileIcon)
            for summary in catalog:
                kind = summary.document_type or "Tipo não informado"
                pages = f"{summary.page_count} página{'s' if summary.page_count != 1 else ''}"
                status = self._STATUS_LABELS.get(
                    summary.processing_status, summary.processing_status
                )
                item = QListWidgetItem(
                    icon,
                    f"{summary.name}\n{kind} • {pages} • {status}",
                )
                item.setData(Qt.ItemDataRole.UserRole, summary.identity)
                item.setToolTip(summary.name)
                self.list_widget.addItem(item)
        finally:
            self.list_widget.blockSignals(False)
        self.select_identity(selected)

    def current_identity(self):
        item = self.list_widget.currentItem()
        return item.data(Qt.ItemDataRole.UserRole) if item else None

    def select_identity(self, identity) -> bool:
        self.list_widget.blockSignals(True)
        found = False
        try:
            self.list_widget.setCurrentItem(None)
            for index in range(self.list_widget.count()):
                item = self.list_widget.item(index)
                if item.data(Qt.ItemDataRole.UserRole) == identity:
                    self.list_widget.setCurrentItem(item)
                    found = True
                    break
        finally:
            self.list_widget.blockSignals(False)
        return found

    def clear(self) -> None:
        self.list_widget.clear()

    def _changed(self, current, _previous) -> None:
        self.document_selected.emit(
            current.data(Qt.ItemDataRole.UserRole) if current else None
        )
