"""Lista visual de páginas com numeração canônica."""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QLabel, QListWidget, QListWidgetItem, QVBoxLayout, QWidget


class DocumentPageListWidget(QWidget):
    page_selected = Signal(object)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.empty_label = QLabel("Nenhuma página disponível.")
        self.empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.list_widget = QListWidget()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.list_widget, 1)
        layout.addWidget(self.empty_label)
        self.list_widget.currentItemChanged.connect(self._changed)
        self.set_pages(())

    def set_pages(self, pages) -> None:
        selected = self.current_page_number()
        self.list_widget.blockSignals(True)
        try:
            self.list_widget.clear()
            for page in pages:
                item = QListWidgetItem(f"Página {page.page_number}")
                item.setData(Qt.ItemDataRole.UserRole, page.page_number)
                self.list_widget.addItem(item)
        finally:
            self.list_widget.blockSignals(False)
        self.select_page(selected)
        self.empty_label.setVisible(self.list_widget.count() == 0)

    def current_page_number(self):
        item = self.list_widget.currentItem()
        return item.data(Qt.ItemDataRole.UserRole) if item else None

    def select_page(self, page_number) -> bool:
        self.list_widget.blockSignals(True)
        found = False
        try:
            self.list_widget.setCurrentItem(None)
            for index in range(self.list_widget.count()):
                item = self.list_widget.item(index)
                if item.data(Qt.ItemDataRole.UserRole) == page_number:
                    self.list_widget.setCurrentItem(item)
                    found = True
                    break
        finally:
            self.list_widget.blockSignals(False)
        return found

    def clear(self) -> None:
        self.set_pages(())

    def _changed(self, current, _previous) -> None:
        self.page_selected.emit(
            current.data(Qt.ItemDataRole.UserRole) if current else None
        )

