"""Catálogo documental Model/View com pesquisa e filtros nativos do Qt."""

from PySide6.QtCore import QModelIndex, QSortFilterProxyModel, Qt, Signal
from PySide6.QtGui import QStandardItem, QStandardItemModel
from PySide6.QtWidgets import (
    QAbstractItemView,
    QTableView,
    QVBoxLayout,
    QWidget,
)


IDENTITY_ROLE = Qt.ItemDataRole.UserRole
SEARCH_ROLE = Qt.ItemDataRole.UserRole + 1
FILTER_ROLE = Qt.ItemDataRole.UserRole + 2


class DocumentFilterProxyModel(QSortFilterProxyModel):
    """Filtra metadados normalizados sem reconstruir a tabela."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._query = ""
        self._filter_id = "all"
        self.setDynamicSortFilter(True)
        self.setSortCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)

    @property
    def query(self) -> str:
        return self._query

    @property
    def filter_id(self) -> str:
        return self._filter_id

    def set_query(self, query: str) -> None:
        normalized = (query or "").strip().casefold()
        if normalized != self._query:
            self._query = normalized
            self.invalidate()

    def set_filter_id(self, filter_id: str) -> None:
        normalized = filter_id if filter_id in {
            "all", "pdf", "ocr_done", "ocr_pending",
            "processed", "not_processed",
        } else "all"
        if normalized != self._filter_id:
            self._filter_id = normalized
            self.invalidate()

    def filterAcceptsRow(self, source_row, source_parent):
        model = self.sourceModel()
        index = model.index(source_row, 0, source_parent)
        searchable = model.data(index, SEARCH_ROLE) or ""
        flags = model.data(index, FILTER_ROLE) or ()
        return (
            (not self._query or self._query in searchable)
            and (self._filter_id == "all" or self._filter_id in flags)
        )


class _DocumentRow:
    """Adaptador mínimo para a API histórica baseada em itens."""

    def __init__(self, view, row):
        self._view = view
        self._row = row

    def text(self, column=0):
        return self._view.model().index(self._row, column).data() or ""

    def data(self, *args):
        role = args[-1] if args else Qt.ItemDataRole.DisplayRole
        return self._view.model().index(self._row, 0).data(role)


class _DocumentTable(QTableView):
    """QTableView com compatibilidade para consumidores anteriores."""

    def item(self, row):
        return _DocumentRow(self, row) if 0 <= row < self.count() else None

    def count(self):
        return self.model().rowCount() if self.model() is not None else 0

    def setCurrentRow(self, row):
        if self.model() is None or not 0 <= row < self.count():
            self.clearSelection()
            self.setCurrentIndex(QModelIndex())
            return
        self.setCurrentIndex(self.model().index(row, 0))

    def currentItem(self):
        index = self.currentIndex()
        return _DocumentRow(self, index.row()) if index.isValid() else None

    def headerItem(self):
        return _HeaderRow(self)

    def sortItems(self, column, order):
        self.sortByColumn(column, order)

    def keyPressEvent(self, event):
        if event.modifiers() == Qt.KeyboardModifier.NoModifier:
            if event.key() == Qt.Key.Key_Home:
                self.setCurrentRow(0)
                event.accept()
                return
            if event.key() == Qt.Key.Key_End:
                self.setCurrentRow(self.count() - 1)
                event.accept()
                return
        super().keyPressEvent(event)


class _HeaderRow:
    def __init__(self, view):
        self._view = view

    def text(self, column):
        return (
            self._view.model().headerData(
                column,
                Qt.Orientation.Horizontal,
                Qt.ItemDataRole.DisplayRole,
            )
            or ""
        )


class DocumentListWidget(QWidget):
    document_selected = Signal(object)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.source_model = QStandardItemModel(0, 3, self)
        self.source_model.setHorizontalHeaderLabels(
            ("Nome", "Tipo", "Data de inclusão")
        )
        self.proxy_model = DocumentFilterProxyModel(self)
        self.proxy_model.setSourceModel(self.source_model)
        self.list_widget = _DocumentTable()
        self.list_widget.setModel(self.proxy_model)
        self.list_widget.setAlternatingRowColors(True)
        self.list_widget.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )
        self.list_widget.setSelectionMode(
            QAbstractItemView.SelectionMode.SingleSelection
        )
        self.list_widget.setSortingEnabled(True)
        self.list_widget.sortByColumn(0, Qt.SortOrder.AscendingOrder)
        self.list_widget.verticalHeader().hide()
        self.list_widget.horizontalHeader().setStretchLastSection(True)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.list_widget)
        self.list_widget.selectionModel().currentRowChanged.connect(
            self._changed
        )

    def set_catalog(self, catalog) -> None:
        selected = self.current_identity()
        self.source_model.removeRows(0, self.source_model.rowCount())
        for summary in catalog:
            kind = summary.document_type or "Tipo não informado"
            items = tuple(
                QStandardItem(value)
                for value in (
                    summary.name,
                    kind,
                    summary.imported_at,
                )
            )
            for item in items:
                item.setEditable(False)
            searchable = " ".join(
                str(value or "")
                for value in (
                    summary.name,
                    kind,
                    summary.relative_path,
                    summary.sha256,
                    summary.document_date,
                )
            ).casefold()
            processing = str(summary.processing_status or "")
            flags = {
                "pdf" if summary.extension.casefold() == ".pdf" else "",
                "ocr_done" if summary.ocr_used else "",
                "ocr_pending" if processing in (
                    "ocr_required", "not_processed", "pending"
                ) else "",
                "processed" if processing == "processed" else "not_processed",
            }
            items[0].setData(summary.identity, IDENTITY_ROLE)
            items[0].setData(searchable, SEARCH_ROLE)
            items[0].setData(tuple(flags - {""}), FILTER_ROLE)
            items[0].setToolTip(summary.name)
            self.source_model.appendRow(items)
        self.select_identity(selected)

    def set_query(self, query: str) -> None:
        selected = self.current_identity()
        self.proxy_model.set_query(query)
        self._clear_hidden_selection(selected)

    def set_filter_id(self, filter_id: str) -> None:
        selected = self.current_identity()
        self.proxy_model.set_filter_id(filter_id)
        self._clear_hidden_selection(selected)

    def current_identity(self):
        index = self.list_widget.currentIndex()
        return (
            index.siblingAtColumn(0).data(IDENTITY_ROLE)
            if index.isValid()
            else None
        )

    def select_identity(self, identity) -> bool:
        selection_model = self.list_widget.selectionModel()
        selection_model.blockSignals(True)
        try:
            self.list_widget.clearSelection()
            self.list_widget.setCurrentIndex(QModelIndex())
            for row in range(self.proxy_model.rowCount()):
                index = self.proxy_model.index(row, 0)
                if index.data(IDENTITY_ROLE) == identity:
                    self.list_widget.setCurrentIndex(index)
                    self.list_widget.scrollTo(index)
                    return True
            return False
        finally:
            selection_model.blockSignals(False)

    def clear(self) -> None:
        self.source_model.removeRows(0, self.source_model.rowCount())

    def _clear_hidden_selection(self, identity) -> None:
        if identity is not None and not self.select_identity(identity):
            self.document_selected.emit(None)

    def _changed(self, current, _previous) -> None:
        self.document_selected.emit(
            (
                current.siblingAtColumn(0).data(IDENTITY_ROLE)
                if current.isValid()
                else None
            )
        )
