"""View passiva do Workspace Dashboard."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from applications.rsc.workspace_dashboard_view_model import (
    PendingItemView,
    WorkspaceDashboardViewData,
)
from presentation import NavigationIntent


class WorkspaceDashboardView(QWidget):
    """Renderiza somente DTOs e emite intenções de navegação."""

    navigation_requested = Signal(object)
    operational_requested = Signal(object)

    def __init__(
        self, dashboard: WorkspaceDashboardViewData, parent=None
    ) -> None:
        if not isinstance(dashboard, WorkspaceDashboardViewData):
            raise TypeError(
                "dashboard deve ser WorkspaceDashboardViewData."
            )
        super().__init__(parent)
        self._dashboard = dashboard
        layout = QVBoxLayout(self)
        layout.addWidget(self._summary_group())
        layout.addWidget(self._actions_group())

        middle = QHBoxLayout()
        middle.addWidget(self._statistics_group())
        middle.addWidget(self._coverage_group())
        layout.addLayout(middle)

        layout.addWidget(self._insight_summary_group())
        layout.addStretch()

    @property
    def dashboard(self) -> WorkspaceDashboardViewData:
        return self._dashboard

    def _summary_group(self) -> QGroupBox:
        group = QGroupBox("Situação geral", self)
        form = QFormLayout(group)
        summary = self._dashboard.summary
        self.project_value = QLabel(summary.project_name)
        self.status_value = QLabel(summary.status)
        self.score_value = QLabel(str(summary.score))
        self.maturity_value = QLabel(summary.maturity)
        self.last_evaluation_value = QLabel(summary.last_evaluation)
        for label, value in (
            ("Projeto:", self.project_value),
            ("Status:", self.status_value),
            ("Pontuação atual:", self.score_value),
            ("Maturidade:", self.maturity_value),
            ("Última avaliação:", self.last_evaluation_value),
        ):
            form.addRow(label, value)
        return group

    def _actions_group(self) -> QGroupBox:
        group = QGroupBox("Ações prioritárias", self)
        layout = QVBoxLayout(group)
        self.priority_list = QListWidget(group)
        for action in self._dashboard.priority_actions:
            prefix = "🔴 " if action.critical else ""
            item = QListWidgetItem(
                f"{prefix}{action.category}: {action.description}"
            )
            item.setData(256, action)
            self.priority_list.addItem(item)
        if not self._dashboard.priority_actions:
            item = QListWidgetItem("Nenhuma ação prioritária.")
            item.setFlags(
                item.flags() & ~Qt.ItemFlag.ItemIsSelectable
            )
            self.priority_list.addItem(item)
        self.priority_list.currentItemChanged.connect(
            self._update_action_button
        )
        self.priority_list.itemDoubleClicked.connect(
            lambda _item: self._request_selected_action()
        )
        layout.addWidget(self.priority_list)
        self.action_button = QPushButton("Abrir", group)
        self.action_button.setEnabled(False)
        self.action_button.clicked.connect(self._request_selected_action)
        layout.addWidget(self.action_button)
        return group

    def _statistics_group(self) -> QGroupBox:
        group = QGroupBox("Estatísticas", self)
        form = QFormLayout(group)
        for statistic in self._dashboard.statistics:
            form.addRow(f"{statistic.label}:", QLabel(statistic.value))
        return group

    def _coverage_group(self) -> QGroupBox:
        group = QGroupBox("Cobertura documental", self)
        form = QFormLayout(group)
        status = self._dashboard.document_status
        for label, value in (
            ("Documents utilizados:", status.used_documents),
            ("Documents sem utilização:", status.unused_documents),
            ("Evidence com Documents:", status.evidences_with_documents),
            ("Evidence sem Documents:", status.evidences_without_documents),
            ("Evidence com ExecutionFacts:", status.evidences_with_facts),
            ("Evidence sem ExecutionFacts:", status.evidences_without_facts),
            ("ExecutionFacts pendentes:", status.pending_execution_facts),
            ("Estado normativo:", status.normative_state),
        ):
            form.addRow(label, QLabel(str(value)))
        return group

    def _insight_summary_group(self) -> QGroupBox:
        group = QGroupBox("Resumo de Insights", self)
        form = QFormLayout(group)
        summary = self._dashboard.insights
        for label, value in (("Total", summary.total), ("Erros", summary.errors),
                             ("Avisos", summary.warnings), ("Informacoes", summary.information),
                             ("Sucessos", summary.success)):
            form.addRow(f"{label}:", QLabel(str(value)))
        return group

    def _update_action_button(self, current, _previous) -> None:
        action = None if current is None else current.data(256)
        self.action_button.setEnabled(isinstance(action, PendingItemView))
        self.action_button.setText(
            "Abrir" if action is None else action.action_label
        )

    def _request_selected_action(self) -> None:
        item = self.priority_list.currentItem()
        action = None if item is None else item.data(256)
        if isinstance(action, PendingItemView):
            if action.intent is not None:
                self.navigation_requested.emit(action.intent)
            elif action.operational_action is not None:
                self.operational_requested.emit(action.operational_action)


__all__ = ["WorkspaceDashboardView"]
