"""View passiva do Resource Inspector."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from presentation.resource_inspector_view_model import (
    ResourceInspectorState,
    ResourceInspectorViewData,
)


class ResourceInspectorView(QWidget):
    """Renderiza DTOs do Inspector e emite somente Navigation Intents."""

    navigation_requested = Signal(object)

    def __init__(self, data: ResourceInspectorViewData, parent=None) -> None:
        if not isinstance(data, ResourceInspectorViewData):
            raise TypeError("data deve ser ResourceInspectorViewData.")
        super().__init__(parent)
        layout = QVBoxLayout(self)
        self.message_value = QLabel(self)
        self.message_value.setWordWrap(True)
        layout.addWidget(self.message_value)

        identity_group = QGroupBox("Resource", self)
        identity_form = QFormLayout(identity_group)
        self.type_value = QLabel(self)
        self.identifier_value = QLabel(self)
        self.name_value = QLabel(self)
        self.status_value = QLabel(self)
        identity_form.addRow("Tipo:", self.type_value)
        identity_form.addRow("Identificador:", self.identifier_value)
        identity_form.addRow("Nome:", self.name_value)
        identity_form.addRow("Status:", self.status_value)
        layout.addWidget(identity_group)

        self.metadata_table = QTableWidget(0, 2, self)
        self.metadata_table.setHorizontalHeaderLabels(("Campo", "Valor"))
        layout.addWidget(self.metadata_table)

        self.relationships_tree = QTreeWidget(self)
        self.relationships_tree.setHeaderLabels((
            "Relação", "Tipo", "Destino", "Rótulo"
        ))
        self.relationships_tree.itemDoubleClicked.connect(
            self._request_relationship
        )
        self.relationships_tree.currentItemChanged.connect(
            self._update_relationship_action
        )
        layout.addWidget(self.relationships_tree)
        self.relationship_button = QPushButton("Navegar", self)
        self.relationship_button.clicked.connect(
            self._request_selected_relationship
        )
        layout.addWidget(self.relationship_button)

        self.actions_group = QGroupBox("Ações", self)
        self.actions_layout = QHBoxLayout(self.actions_group)
        layout.addWidget(self.actions_group)
        layout.addStretch()
        self._action_buttons: list[QWidget] = []
        self.set_data(data)

    def set_data(self, data: ResourceInspectorViewData) -> None:
        if not isinstance(data, ResourceInspectorViewData):
            raise TypeError("data deve ser ResourceInspectorViewData.")
        self._data = data
        self.message_value.setText(data.message)
        self.message_value.setVisible(bool(data.message))
        self.type_value.setText(data.resource_type)
        self.identifier_value.setText(data.resource_id)
        self.name_value.setText(data.display_name)
        self.status_value.setText(data.status)
        self._render_metadata(data)
        self._render_relationships(data)
        self._render_actions(data)
        ready = data.state is ResourceInspectorState.READY
        self.metadata_table.setEnabled(ready)
        self.relationships_tree.setEnabled(ready)

    @property
    def data(self) -> ResourceInspectorViewData:
        return self._data

    def _render_metadata(self, data: ResourceInspectorViewData) -> None:
        self.metadata_table.setRowCount(max(1, len(data.metadata)))
        if not data.metadata:
            self.metadata_table.setItem(
                0, 0, QTableWidgetItem("Nenhuma metadata disponível.")
            )
            self.metadata_table.setItem(0, 1, QTableWidgetItem("—"))
            return
        for row, item in enumerate(data.metadata):
            self.metadata_table.setItem(row, 0, QTableWidgetItem(item.label))
            self.metadata_table.setItem(row, 1, QTableWidgetItem(item.value))

    def _render_relationships(self, data: ResourceInspectorViewData) -> None:
        self.relationships_tree.clear()
        for relationship in data.relationships:
            item = QTreeWidgetItem((
                relationship.relationship_type,
                relationship.target_type,
                relationship.target_id,
                relationship.label,
            ))
            item.setData(0, Qt.ItemDataRole.UserRole, relationship.intent)
            self.relationships_tree.addTopLevelItem(item)
        if not data.relationships:
            item = QTreeWidgetItem(("Nenhum relacionamento.", "—", "—", "—"))
            item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsSelectable)
            self.relationships_tree.addTopLevelItem(item)
        self.relationship_button.setEnabled(False)

    def _render_actions(self, data: ResourceInspectorViewData) -> None:
        for button in self._action_buttons:
            self.actions_layout.removeWidget(button)
            button.deleteLater()
        self._action_buttons = []
        if not data.actions:
            label = QLabel("Nenhuma ação disponível.", self.actions_group)
            self.actions_layout.addWidget(label)
            self._action_buttons.append(label)
            return
        for action in data.actions:
            button = QPushButton(action.label, self.actions_group)
            button.clicked.connect(
                lambda _checked=False, intent=action.intent: (
                    self.navigation_requested.emit(intent)
                )
            )
            self.actions_layout.addWidget(button)
            self._action_buttons.append(button)

    def _update_relationship_action(self, current, _previous) -> None:
        intent = (
            None
            if current is None
            else current.data(0, Qt.ItemDataRole.UserRole)
        )
        self.relationship_button.setEnabled(intent is not None)

    def _request_selected_relationship(self) -> None:
        current = self.relationships_tree.currentItem()
        if current is not None:
            self._request_relationship(current)

    def _request_relationship(self, item, _column=0) -> None:
        intent = item.data(0, Qt.ItemDataRole.UserRole)
        if intent is not None:
            self.navigation_requested.emit(intent)


__all__ = ["ResourceInspectorView"]
