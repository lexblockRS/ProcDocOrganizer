"""View passiva do Review Workspace."""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QCheckBox, QComboBox, QFormLayout, QGroupBox, QLabel, QListWidget, QListWidgetItem, QPushButton, QVBoxLayout, QWidget

from applications.rsc.review_workspace_view_model import ReviewItemView, ReviewWorkspaceViewData
from applications.rsc.services.review_workspace_service import ReviewCategory, ReviewOrigin
from presentation.insights import InsightSeverity
from presentation.navigation_contracts import (
    NavigationIntent,
    NavigationIntentType,
    WorkspaceFilter,
)


class ReviewWorkspaceView(QWidget):
    navigation_requested = Signal(object)
    operational_requested = Signal(object)

    def __init__(self, data: ReviewWorkspaceViewData, parent=None) -> None:
        if not isinstance(data, ReviewWorkspaceViewData):
            raise TypeError("data deve ser ReviewWorkspaceViewData.")
        super().__init__(parent)
        self._data = data
        layout = QVBoxLayout(self)
        summary = QGroupBox("Resumo da revisao", self)
        form = QFormLayout(summary)
        form.addRow("Projeto:", QLabel(data.summary.project_name))
        form.addRow("Itens:", QLabel(str(data.summary.total)))
        form.addRow("Estado:", QLabel(data.summary.state))
        form.addRow("Filtros:", QLabel(self._filter_text(data)))
        layout.addWidget(summary)
        filters_group = QGroupBox("Filtros", self)
        filters_form = QFormLayout(filters_group)
        self.category_filter = self._combo(("Todas", None), *((item.value, item) for item in ReviewCategory))
        self.severity_filter = self._combo(("Todas", None), *((item.value, item) for item in InsightSeverity))
        self.origin_filter = self._combo(("Todas", None), *((item.value, item) for item in ReviewOrigin))
        self.pending_filter = QCheckBox("Somente pendencias", filters_group)
        self._restore_combo(
            self.category_filter, data.active_categories
        )
        self._restore_combo(
            self.severity_filter, data.active_severities
        )
        self._restore_combo(self.origin_filter, data.active_origins)
        self.pending_filter.setChecked(data.only_pending)
        self.apply_filters_button = QPushButton("Aplicar filtros", filters_group)
        self.apply_filters_button.clicked.connect(self._request_filters)
        filters_form.addRow("Categoria:", self.category_filter)
        filters_form.addRow("Severidade:", self.severity_filter)
        filters_form.addRow("Origem:", self.origin_filter)
        filters_form.addRow(self.pending_filter)
        filters_form.addRow(self.apply_filters_button)
        layout.addWidget(filters_group)
        self.items_list = QListWidget(self)
        for value in data.items:
            item = QListWidgetItem(f"[{value.severity.upper()}] {value.title} — {value.description}")
            item.setData(Qt.ItemDataRole.UserRole, value)
            self.items_list.addItem(item)
        if not data.items:
            item = QListWidgetItem(data.summary.state.replace("_", " ").title())
            item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsSelectable)
            self.items_list.addItem(item)
        self.items_list.currentItemChanged.connect(self._selection_changed)
        self.items_list.itemDoubleClicked.connect(lambda _item: self._emit_selected())
        layout.addWidget(self.items_list)
        self.open_button = QPushButton("Abrir Resource", self)
        self.open_button.setEnabled(False)
        self.open_button.clicked.connect(self._emit_selected)
        layout.addWidget(self.open_button)

    @property
    def data(self) -> ReviewWorkspaceViewData:
        return self._data

    @staticmethod
    def _filter_text(data):
        parts = list(data.active_categories + data.active_severities + data.active_origins)
        if data.only_pending:
            parts.append("somente pendencias")
        return ", ".join(parts) if parts else "Nenhum"

    def _combo(self, *options):
        combo = QComboBox(self)
        for label, value in options:
            combo.addItem(label, value)
        return combo

    @staticmethod
    def _restore_combo(combo: QComboBox, values: tuple[str, ...]) -> None:
        if not values:
            return
        expected = values[0]
        for index in range(combo.count()):
            value = combo.itemData(index)
            actual = (
                value.value if hasattr(value, "value") else str(value)
            )
            if value is not None and actual == expected:
                combo.setCurrentIndex(index)
                return

    def _request_filters(self) -> None:
        category = self.category_filter.currentData()
        severity = self.severity_filter.currentData()
        origin = self.origin_filter.currentData()
        filters = []
        for filter_id, value in (("review.category", category), ("review.severity", severity), ("review.origin", origin)):
            if value is not None:
                filters.append(WorkspaceFilter(
                    filter_id,
                    {"value": value.value if hasattr(value, "value") else str(value)},
                ))
        if self.pending_filter.isChecked():
            filters.append(WorkspaceFilter("review.only_pending", {"value": True}))
        self.navigation_requested.emit(NavigationIntent(
            NavigationIntentType.OPEN_PERSPECTIVE,
            "review_workspace",
            origin="review_workspace_filters",
            filters=tuple(filters),
        ))

    def _selection_changed(self, current, _previous) -> None:
        value = None if current is None else current.data(Qt.ItemDataRole.UserRole)
        self.open_button.setEnabled(isinstance(value, ReviewItemView) and (value.navigation_intent is not None or value.operational_action is not None))

    def _emit_selected(self) -> None:
        current = self.items_list.currentItem()
        value = None if current is None else current.data(Qt.ItemDataRole.UserRole)
        if isinstance(value, ReviewItemView) and value.navigation_intent is not None:
            self.navigation_requested.emit(value.navigation_intent)
        elif isinstance(value, ReviewItemView) and value.operational_action is not None:
            self.operational_requested.emit(value.operational_action)


__all__ = ["ReviewWorkspaceView"]
