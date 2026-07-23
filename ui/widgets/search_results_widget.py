"""Lista visual de SearchHit, sem acesso a infraestrutura ou documentos."""

from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtWidgets import QListWidget, QListWidgetItem, QStyle, QVBoxLayout, QWidget

from services.search import SearchHit


class SearchResultsWidget(QWidget):
    result_selected = Signal(object)
    result_activated = Signal(object)

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        self.results_list = QListWidget()
        self.results_list.setIconSize(QSize(24, 24))
        self.results_list.setAlternatingRowColors(True)
        layout.addWidget(self.results_list)
        self.results_list.currentItemChanged.connect(self._select_result)
        self.results_list.itemActivated.connect(self._activate_result)

    def set_results(
        self, results: tuple[SearchHit, ...] | list[SearchHit]
    ) -> None:
        self.results_list.clear()
        icon = self.style().standardIcon(QStyle.StandardPixmap.SP_FileIcon)
        for result in results:
            title = result.document_name or "Documento sem título"
            item = QListWidgetItem(
                icon,
                f"{title}\nPágina {result.page_number}\n{result.snippet}",
            )
            item.setData(Qt.ItemDataRole.UserRole, result)
            self.results_list.addItem(item)

    def clear(self) -> None:
        self.results_list.clear()

    def result_count(self) -> int:
        return self.results_list.count()

    def current_result(self) -> SearchHit | None:
        item = self.results_list.currentItem()
        return item.data(Qt.ItemDataRole.UserRole) if item else None

    def _select_result(self, current: QListWidgetItem | None, previous=None) -> None:
        self.result_selected.emit(
            current.data(Qt.ItemDataRole.UserRole) if current else None
        )

    def _activate_result(self, item: QListWidgetItem | None) -> None:
        if item is not None:
            self.result_activated.emit(
                item.data(Qt.ItemDataRole.UserRole)
            )
