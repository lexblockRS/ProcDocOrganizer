"""Janela mínima para criação e reabertura de Projects da plataforma."""

from __future__ import annotations

from decimal import Decimal, InvalidOperation

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QStatusBar,
    QTabWidget,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

from applications.rsc.results_view_model import ResultsViewModel
from applications.rsc.evaluation_report_view_model import (
    EvaluationReportViewModel,
)
from applications.rsc.workspace_dashboard_view_model import (
    WorkspaceDashboardViewModel,
)
from applications.rsc.review_workspace_view_model import ReviewWorkspaceViewModel
from applications.rsc.operational_actions import ExecuteEvaluationAction
from ui.evaluation_report_view import EvaluationReportView
from ui.results_view import ResultsView
from ui.workspace_dashboard import WorkspaceDashboardView
from ui.review_workspace import ReviewWorkspaceView
from presentation import NavigationIntent, NavigationIntentType, SelectionKind, WorkspaceSnapshot


class ProjectExplorerWindow(QMainWindow):
    """Interface restrita ao ciclo visual de Project."""

    navigation_requested = Signal(object)
    new_project_requested = Signal()
    open_project_requested = Signal()
    close_project_requested = Signal()

    def __init__(
        self,
        *,
        navigation_controller=None,
        workspace_store=None,
    ) -> None:
        super().__init__()
        self._service = None
        self._navigation_controller = navigation_controller
        self._workspace_store = workspace_store
        self._workspace_snapshot = None if workspace_store is None else workspace_store.snapshot
        self._workspace_unsubscribe = (
            None if workspace_store is None else workspace_store.subscribe(self.apply_workspace_snapshot)
        )
        self._applying_workspace = False
        self._dashboard_view: WorkspaceDashboardView | None = None
        self._review_view: ReviewWorkspaceView | None = None
        self._results_view: ResultsView | None = None
        self._evaluation_report_view: EvaluationReportView | None = None
        self._disposed = False

        self.setWindowTitle("ProcDocOrganizer — Project Explorer")
        self.resize(760, 480)
        self._create_actions()
        self._create_menu()
        self._create_toolbar()
        self._create_main_area()
        self._create_status_bar()
        self._render_empty()

    @property
    def project(self):
        return None if self._service is None else self._service.project

    @property
    def workspace_root(self):
        return None if self._service is None else self._service.workspace_root

    @property
    def last_execution_result(self):
        return (
            None
            if self._service is None
            else self._service.last_execution_result
        )

    @property
    def last_evaluation_at(self):
        return (
            None if self._service is None else self._service.last_evaluation_at
        )

    def _create_actions(self) -> None:
        self.action_new = QAction("Novo Projeto", self)
        self.action_open = QAction("Abrir Projeto", self)
        self.action_close = QAction("Fechar Projeto", self)
        self.action_exit = QAction("Sair", self)
        self.action_about = QAction("Sobre", self)

        self.action_new.triggered.connect(self.new_project_requested.emit)
        self.action_open.triggered.connect(self.open_project_requested.emit)
        self.action_close.triggered.connect(self.close_project_requested.emit)
        self.action_exit.triggered.connect(self.close)
        self.action_about.triggered.connect(self.show_about)

    def _create_menu(self) -> None:
        file_menu = self.menuBar().addMenu("Arquivo")
        file_menu.addAction(self.action_new)
        file_menu.addAction(self.action_open)
        file_menu.addAction(self.action_close)
        file_menu.addSeparator()
        file_menu.addAction(self.action_exit)

        help_menu = self.menuBar().addMenu("Ajuda")
        help_menu.addAction(self.action_about)

    def _create_toolbar(self) -> None:
        toolbar = QToolBar("Projetos", self)
        toolbar.setObjectName("projectExplorerToolbar")
        toolbar.setMovable(False)
        toolbar.addAction(self.action_new)
        toolbar.addAction(self.action_open)
        toolbar.addAction(self.action_close)
        self.addToolBar(toolbar)

    def _create_main_area(self) -> None:
        panel = QWidget(self)
        layout = QVBoxLayout(panel)
        project_panel = QWidget(panel)
        project_layout = QFormLayout(project_panel)
        self.name_value = QLabel()
        self.aggregate_id_value = QLabel()
        self.application_value = QLabel()
        self.state_value = QLabel()
        self.revision_value = QLabel()
        self.workspace_value = QLabel()
        self.created_at_value = QLabel()
        for title, widget in (
            ("Nome:", self.name_value),
            ("Aggregate ID:", self.aggregate_id_value),
            ("Application:", self.application_value),
            ("Estado:", self.state_value),
            ("Revision:", self.revision_value),
            ("Workspace:", self.workspace_value),
            ("Data de criação:", self.created_at_value),
        ):
            widget.setTextInteractionFlags(
                widget.textInteractionFlags()
            )
            project_layout.addRow(title, widget)
        layout.addWidget(project_panel)

        evidence_group = QGroupBox("Evidências", panel)
        evidence_layout = QVBoxLayout(evidence_group)
        self.evidence_list = QListWidget(evidence_group)
        self.evidence_list.currentItemChanged.connect(
            self._evidence_selection_changed
        )
        evidence_layout.addWidget(self.evidence_list)
        evidence_buttons = QHBoxLayout()
        self.add_evidence_button = QPushButton("Adicionar", evidence_group)
        self.edit_evidence_button = QPushButton("Editar", evidence_group)
        self.remove_evidence_button = QPushButton("Remover", evidence_group)
        self.add_evidence_button.clicked.connect(self.add_evidence)
        self.edit_evidence_button.clicked.connect(
            self.edit_selected_evidence
        )
        self.remove_evidence_button.clicked.connect(
            self.remove_selected_evidence
        )
        for button in (
            self.add_evidence_button,
            self.edit_evidence_button,
            self.remove_evidence_button,
        ):
            evidence_buttons.addWidget(button)
        evidence_buttons.addStretch()
        evidence_layout.addLayout(evidence_buttons)
        layout.addWidget(evidence_group)

        fact_group = QGroupBox("Execution Facts", panel)
        fact_layout = QVBoxLayout(fact_group)
        self.execution_fact_list = QListWidget(fact_group)
        self.execution_fact_list.currentItemChanged.connect(
            self._execution_fact_selection_changed
        )
        fact_layout.addWidget(self.execution_fact_list)
        fact_buttons = QHBoxLayout()
        self.add_execution_fact_button = QPushButton("Adicionar", fact_group)
        self.edit_execution_fact_button = QPushButton("Editar", fact_group)
        self.remove_execution_fact_button = QPushButton("Remover", fact_group)
        self.add_execution_fact_button.clicked.connect(
            self.add_execution_fact
        )
        self.edit_execution_fact_button.clicked.connect(
            self.edit_selected_execution_fact
        )
        self.remove_execution_fact_button.clicked.connect(
            self.remove_selected_execution_fact
        )
        for button in (
            self.add_execution_fact_button,
            self.edit_execution_fact_button,
            self.remove_execution_fact_button,
        ):
            fact_buttons.addWidget(button)
        fact_buttons.addStretch()
        fact_layout.addLayout(fact_buttons)
        layout.addWidget(fact_group)

        binding_group = QGroupBox("Enquadramento normativo", panel)
        binding_layout = QVBoxLayout(binding_group)
        self.binding_value = QLabel("—", binding_group)
        binding_layout.addWidget(self.binding_value)
        binding_buttons = QHBoxLayout()
        self.add_binding_button = QPushButton("Associar", binding_group)
        self.edit_binding_button = QPushButton("Alterar", binding_group)
        self.remove_binding_button = QPushButton("Remover", binding_group)
        self.add_binding_button.clicked.connect(self.add_binding)
        self.edit_binding_button.clicked.connect(self.edit_selected_binding)
        self.remove_binding_button.clicked.connect(
            self.remove_selected_binding
        )
        for button in (
            self.add_binding_button,
            self.edit_binding_button,
            self.remove_binding_button,
        ):
            binding_buttons.addWidget(button)
        binding_buttons.addStretch()
        binding_layout.addLayout(binding_buttons)
        layout.addWidget(binding_group)

        self.execute_evaluation_button = QPushButton(
            "Executar Avaliação", panel
        )
        self.execute_evaluation_button.clicked.connect(
            self.request_evaluation
        )
        self.execution_summary = QLabel("—", panel)
        self.view_results_button = QPushButton("Ver Resultado", panel)
        self.view_results_button.clicked.connect(self.show_results)
        self.view_report_button = QPushButton("Visualizar Relatório", panel)
        self.view_report_button.clicked.connect(self.show_evaluation_report)
        layout.addWidget(self.execute_evaluation_button)
        layout.addWidget(self.view_results_button)
        layout.addWidget(self.view_report_button)
        layout.addWidget(self.execution_summary)
        self.workspace_tabs = QTabWidget(self)
        self._dashboard_placeholder = QLabel(
            "Abra um projeto para visualizar o Dashboard.", self
        )
        self.workspace_tabs.addTab(
            self._dashboard_placeholder, "Workspace Dashboard"
        )
        self.workspace_tabs.addTab(panel, "Project Explorer")
        self._review_placeholder = QLabel(
            "Abra um projeto para iniciar a revisao.", self
        )
        self.workspace_tabs.addTab(self._review_placeholder, "Review Workspace")
        self._results_placeholder = QLabel(
            "Execute uma avaliação para visualizar os resultados.", self
        )
        self.workspace_tabs.addTab(self._results_placeholder, "Results")
        self._report_placeholder = QLabel(
            "Execute uma avaliação para visualizar o relatório.", self
        )
        self.workspace_tabs.addTab(
            self._report_placeholder, "Evaluation Report"
        )
        self.setCentralWidget(self.workspace_tabs)

    def _create_status_bar(self) -> None:
        self.setStatusBar(QStatusBar(self))

    def bind_service(self, service) -> None:
        if service is None:
            raise ValueError("service não pode ser None.")
        self._service = service
        self._results_view = None
        self._evaluation_report_view = None
        self._render_project()
        self.statusBar().showMessage("Projeto carregado.")

    def unbind_service(self) -> None:
        self._service = None
        self._results_view = None
        self._evaluation_report_view = None
        self._render_empty()
        self.statusBar().showMessage("Nenhum projeto aberto.")

    def create_evidence(
        self,
        *,
        title: str,
        description: str = "",
    ):
        if self.project is None:
            raise RuntimeError("Nenhum Project está aberto.")
        evidence = self._service.create_evidence(
            project_id=self.project.aggregate_id,
            title=title,
            description=description,
        )
        self._refresh_evidences(select_id=evidence.aggregate_id)
        self._refresh_dashboard()
        self.statusBar().showMessage("Evidence adicionada.")
        return evidence

    def add_evidence(self) -> None:
        if self.project is None:
            return
        title, accepted = QInputDialog.getText(
            self, "Adicionar Evidence", "Título:"
        )
        if accepted and title.strip():
            self.create_evidence(title=title)

    def edit_evidence(
        self,
        evidence_id: str,
        *,
        title: str,
        description: str | None = None,
    ):
        if self.project is None:
            raise RuntimeError("Nenhum Project está aberto.")
        updated = self._service.edit_evidence(
            evidence_id,
            project_id=self.project.aggregate_id,
            title=title,
            description=description,
        )
        self._refresh_evidences(select_id=updated.aggregate_id)
        self._refresh_dashboard()
        self.statusBar().showMessage("Evidence atualizada.")
        return updated

    def edit_selected_evidence(self) -> None:
        evidence_id = self._selected_evidence_id()
        if evidence_id is None:
            return
        evidence = self._service.get_evidence(evidence_id)
        title, accepted = QInputDialog.getText(
            self,
            "Editar Evidence",
            "Título:",
            text=evidence.title,
        )
        if accepted and title.strip():
            self.edit_evidence(evidence_id, title=title)

    def remove_evidence(self, evidence_id: str) -> None:
        if self.project is None:
            raise RuntimeError("Nenhum Project está aberto.")
        self._service.delete_evidence(
            evidence_id,
            project_id=self.project.aggregate_id,
        )
        self._refresh_evidences()
        self._refresh_dashboard()
        self.statusBar().showMessage("Evidence removida.")

    def remove_selected_evidence(self) -> None:
        evidence_id = self._selected_evidence_id()
        if evidence_id is not None:
            self.remove_evidence(evidence_id)

    def create_execution_fact(
        self,
        *,
        fact_type: str,
        description: str,
        quantity: Decimal | None,
        unit: str,
    ):
        evidence_id = self._selected_evidence_id()
        if self.project is None or evidence_id is None:
            raise RuntimeError("Selecione uma Evidence.")
        fact = self._service.create_fact(
            project_id=self.project.aggregate_id,
            evidence_id=evidence_id,
            fact_type=fact_type,
            description=description,
            quantity=quantity,
            unit=unit,
        )
        self._refresh_execution_facts(select_id=fact.aggregate_id)
        self._refresh_dashboard()
        self.statusBar().showMessage("ExecutionFact adicionado.")
        return fact

    def add_execution_fact(self) -> None:
        if self._selected_evidence_id() is None:
            return
        fact_type, accepted = QInputDialog.getText(
            self, "Adicionar ExecutionFact", "Tipo:"
        )
        if not accepted or not fact_type.strip():
            return
        description, accepted = QInputDialog.getText(
            self, "Adicionar ExecutionFact", "Descrição:"
        )
        if not accepted or not description.strip():
            return
        unit, accepted = QInputDialog.getText(
            self, "Adicionar ExecutionFact", "Unidade:"
        )
        if not accepted or not unit.strip():
            return
        quantity_text, accepted = QInputDialog.getText(
            self,
            "Adicionar ExecutionFact",
            "Quantidade (opcional):",
        )
        if not accepted:
            return
        try:
            quantity = (
                None
                if not quantity_text.strip()
                else Decimal(quantity_text.strip())
            )
        except InvalidOperation:
            QMessageBox.warning(
                self,
                "Adicionar ExecutionFact",
                "Quantidade inválida.",
            )
            return
        self.create_execution_fact(
            fact_type=fact_type,
            description=description,
            quantity=quantity,
            unit=unit,
        )

    def edit_execution_fact(
        self,
        execution_fact_id: str,
        *,
        description: str,
    ):
        evidence_id = self._selected_evidence_id()
        if self.project is None or evidence_id is None:
            raise RuntimeError("Selecione uma Evidence.")
        updated = self._service.edit_fact(
            execution_fact_id,
            project_id=self.project.aggregate_id,
            evidence_id=evidence_id,
            description=description,
        )
        self._refresh_execution_facts(select_id=updated.aggregate_id)
        self._refresh_dashboard()
        self.statusBar().showMessage("ExecutionFact atualizado.")
        return updated

    def edit_selected_execution_fact(self) -> None:
        fact_id = self._selected_execution_fact_id()
        if fact_id is None:
            return
        fact = self._service.get_fact(fact_id)
        description, accepted = QInputDialog.getText(
            self,
            "Editar ExecutionFact",
            "Descrição:",
            text=fact.description,
        )
        if accepted and description.strip():
            self.edit_execution_fact(
                fact_id, description=description
            )

    def remove_execution_fact(self, execution_fact_id: str) -> None:
        evidence_id = self._selected_evidence_id()
        if self.project is None or evidence_id is None:
            raise RuntimeError("Selecione uma Evidence.")
        self._service.delete_fact(
            execution_fact_id,
            project_id=self.project.aggregate_id,
            evidence_id=evidence_id,
        )
        self._refresh_execution_facts()
        self._refresh_dashboard()
        self.statusBar().showMessage("ExecutionFact removido.")

    def remove_selected_execution_fact(self) -> None:
        fact_id = self._selected_execution_fact_id()
        if fact_id is not None:
            self.remove_execution_fact(fact_id)

    def create_binding(
        self,
        *,
        criterion_id: str,
    ):
        fact_id = self._selected_execution_fact_id()
        if fact_id is None:
            raise RuntimeError("Selecione um ExecutionFact.")
        binding = self._service.create_binding(
            execution_fact_id=fact_id,
            criterion_id=criterion_id,
        )
        self._refresh_binding()
        self._refresh_dashboard()
        self.statusBar().showMessage("Binding criado.")
        return binding

    def rebind_execution_fact(
        self,
        *,
        criterion_id: str,
    ):
        fact_id = self._selected_execution_fact_id()
        if fact_id is None:
            raise RuntimeError("Selecione um ExecutionFact.")
        updated = self._service.rebind(
            execution_fact_id=fact_id,
            criterion_id=criterion_id,
        )
        self._refresh_binding()
        self._refresh_dashboard()
        self.statusBar().showMessage("Binding atualizado.")
        return updated

    def add_binding(self) -> None:
        criterion_id = self._select_catalog_criterion(
            "Associar ao catálogo"
        )
        if criterion_id is not None:
            self.create_binding(criterion_id=criterion_id)

    def edit_selected_binding(self) -> None:
        criterion_id = self._select_catalog_criterion(
            "Alterar enquadramento"
        )
        if criterion_id is not None:
            self.rebind_execution_fact(criterion_id=criterion_id)

    def remove_selected_binding(self) -> None:
        fact_id = self._selected_execution_fact_id()
        if fact_id is None:
            return
        self._service.delete_binding_for_fact(fact_id)
        self._refresh_binding()
        self._refresh_dashboard()
        self.statusBar().showMessage("Binding removido.")

    def _select_catalog_criterion(self, title: str) -> str | None:
        definitions = self._service.criterion_definitions()
        labels = tuple(
            f"{item.code} — {item.description}" for item in definitions
        )
        selected, accepted = QInputDialog.getItem(
            self, title, "Critério:", labels, 0, False
        )
        if not accepted:
            return None
        return definitions[labels.index(selected)].code

    def execute_evaluation(self):
        if self.project is None:
            raise RuntimeError("Nenhum Project está aberto.")
        result = self._service.execute()
        self.view_results_button.setEnabled(True)
        self.view_report_button.setEnabled(True)
        self.execution_summary.setText(
            f"ExecutionFacts: {result.execution_fact_count} | "
            f"Bindings: {result.valid_binding_count} | "
            f"CriterionScores: {result.criterion_score_count} | "
            f"RequirementScores: {result.requirement_score_count} | "
            f"Pontuação: {result.total_score} | "
            f"Incompatibilidades: {result.incompatibility_count} | "
            f"Tempo: {result.elapsed_seconds:.3f} s"
        )
        self.statusBar().showMessage("Avaliação concluída.")
        self._refresh_dashboard()
        return result

    def open_results(self) -> ResultsView:
        if self.last_execution_result is None:
            raise RuntimeError("Nenhuma avaliação foi executada.")
        view_model = ResultsViewModel(
            self.last_execution_result.process
        )
        self._results_view = ResultsView(view_model.summary, self)
        self._replace_output_tab(3, self._results_view, "Results")
        return self._results_view

    def show_results(self) -> None:
        if self._navigation_controller is not None:
            self._dispatch_navigation(NavigationIntent.open_evaluation(
                self.project.aggregate_id,
                project_id=self.project.aggregate_id,
                origin="project_explorer",
            ))
            return
        self.open_results().show()

    def open_evaluation_report(self) -> EvaluationReportView:
        if self.last_execution_result is None:
            raise RuntimeError("Nenhuma avaliação foi executada.")
        result = self.last_execution_result
        view_model = EvaluationReportViewModel(
            result.process, elapsed_seconds=result.elapsed_seconds
        )
        self._evaluation_report_view = EvaluationReportView(
            view_model.report, self
        )
        self._replace_output_tab(
            4, self._evaluation_report_view, "Evaluation Report"
        )
        return self._evaluation_report_view

    def show_evaluation_report(self) -> None:
        if self._navigation_controller is not None:
            self._dispatch_navigation(NavigationIntent.open_report(
                self.project.aggregate_id,
                project_id=self.project.aggregate_id,
                origin="project_explorer",
            ))
            return
        self.open_evaluation_report().show()

    def request_evaluation(self) -> None:
        try:
            self.execute_evaluation()
        except Exception as exc:
            self.statusBar().showMessage("Falha na validação.")
            QMessageBox.warning(
                self, "Executar Avaliação", f"Falha na validação: {exc}"
            )
            return
        QMessageBox.information(
            self, "Executar Avaliação", "Avaliação concluída."
        )

    def show_about(self) -> None:
        QMessageBox.about(
            self,
            "Sobre",
            "ProcDocOrganizer Project Explorer\nProduct 1.0",
        )

    def _render_project(self) -> None:
        project = self.project
        if project is None:
            self._render_empty()
            return
        self._reset_output_tabs()
        self.name_value.setText(project.name)
        self.aggregate_id_value.setText(project.aggregate_id)
        self.application_value.setText(project.application_id)
        self.state_value.setText(project.state.value)
        self.revision_value.setText(str(self._service.operational_revision))
        self.workspace_value.setText(str(self.workspace_root))
        self.created_at_value.setText("Não disponível")
        self.action_close.setEnabled(True)
        self.execute_evaluation_button.setEnabled(True)
        self.view_results_button.setEnabled(
            self.last_execution_result is not None
        )
        self.view_report_button.setEnabled(
            self.last_execution_result is not None
        )
        self._refresh_evidences()
        self._refresh_dashboard(activate=True)

    def _render_empty(self) -> None:
        self._reset_output_tabs()
        for label in (
            self.name_value,
            self.aggregate_id_value,
            self.application_value,
            self.state_value,
            self.revision_value,
            self.workspace_value,
            self.created_at_value,
        ):
            label.setText("—")
        self.action_close.setEnabled(False)
        self.execute_evaluation_button.setEnabled(False)
        self.view_results_button.setEnabled(False)
        self.view_report_button.setEnabled(False)
        self.execution_summary.setText("—")
        self.evidence_list.clear()
        self.execution_fact_list.clear()
        self.binding_value.setText("—")
        self.add_evidence_button.setEnabled(False)
        self._update_evidence_actions()
        self._update_execution_fact_actions()
        self._refresh_binding()
        self._show_dashboard_placeholder()
        self.statusBar().showMessage("Nenhum projeto aberto.")

    def _show_dashboard_placeholder(self) -> None:
        placeholder = QLabel(
            "Abra um projeto para visualizar o Dashboard.", self
        )
        old_widget = self.workspace_tabs.widget(0)
        self.workspace_tabs.removeTab(0)
        self.workspace_tabs.insertTab(
            0, placeholder, "Workspace Dashboard"
        )
        self._dashboard_placeholder = placeholder
        self._dashboard_view = None
        if old_widget is not None and old_widget is not placeholder:
            old_widget.deleteLater()
        if self.workspace_tabs.count() > 2:
            review_placeholder = QLabel(
                "Abra um projeto para iniciar a revisao.", self
            )
            old_review = self.workspace_tabs.widget(2)
            self.workspace_tabs.removeTab(2)
            self.workspace_tabs.insertTab(
                2, review_placeholder, "Review Workspace"
            )
            self._review_placeholder = review_placeholder
            self._review_view = None
            if old_review is not None and old_review is not review_placeholder:
                old_review.deleteLater()

    def _refresh_dashboard(self, *, activate: bool = False) -> None:
        if self.project is None:
            self._show_dashboard_placeholder()
            return
        process = (
            None
            if self.last_execution_result is None
            else self.last_execution_result.process
        )
        snapshot, review_snapshot = self._service.presentation_snapshots(
            self.project,
            process=process,
            last_evaluation=self.last_evaluation_at,
            workspace_snapshot=self._workspace_snapshot,
        )
        dashboard = WorkspaceDashboardViewModel(snapshot).dashboard
        view = WorkspaceDashboardView(dashboard, self)
        view.navigation_requested.connect(self._dispatch_navigation)
        view.operational_requested.connect(self._execute_operational_action)
        old_widget = self.workspace_tabs.widget(0)
        self.workspace_tabs.removeTab(0)
        self.workspace_tabs.insertTab(0, view, "Workspace Dashboard")
        self._dashboard_view = view
        if old_widget is not None and old_widget is not view:
            old_widget.deleteLater()
        if activate:
            self.workspace_tabs.setCurrentIndex(0)
        self._refresh_review(review_snapshot)

    def _refresh_review(self, snapshot=None) -> None:
        if self.project is None:
            return
        process = None if self.last_execution_result is None else self.last_execution_result.process
        if snapshot is None:
            snapshot = self._service.review_snapshot(
                self.project, process=process,
                last_evaluation=self.last_evaluation_at,
                workspace_snapshot=self._workspace_snapshot,
            )
        view = ReviewWorkspaceView(ReviewWorkspaceViewModel(snapshot).data, self)
        view.navigation_requested.connect(self._dispatch_navigation)
        view.operational_requested.connect(self._execute_operational_action)
        old_widget = self.workspace_tabs.widget(2)
        self.workspace_tabs.removeTab(2)
        self.workspace_tabs.insertTab(2, view, "Review Workspace")
        self._review_view = view
        if old_widget is not None and old_widget is not view:
            old_widget.deleteLater()

    def _dispatch_navigation(
        self, intent: NavigationIntent
    ) -> None:
        if not isinstance(intent, NavigationIntent):
            raise TypeError("intent deve ser NavigationIntent.")
        if self._navigation_controller is not None:
            self._navigation_controller.navigate(intent)
        else:
            self.navigation_requested.emit(intent)
        return

    def apply_workspace_snapshot(self, snapshot: WorkspaceSnapshot) -> None:
        if not isinstance(snapshot, WorkspaceSnapshot):
            raise TypeError("snapshot deve ser WorkspaceSnapshot.")
        self._workspace_snapshot = snapshot
        if self.project is None:
            return
        self._applying_workspace = True
        self._refresh_dashboard()
        perspective_tabs = {
            "workspace_dashboard": 0,
            "project_explorer": 1,
            "review_workspace": 2,
            "results": 3,
            "evaluation_report": 4,
        }
        if snapshot.active_perspective is not None:
            index = perspective_tabs.get(snapshot.active_perspective.value)
            if index is not None:
                self.workspace_tabs.setCurrentIndex(index)
        selection = snapshot.selection.identity
        target_id = selection.identifier
        if selection.kind is SelectionKind.DOCUMENT and target_id is not None:
            self.workspace_tabs.setCurrentIndex(1)
            evidence = self._service.find_evidence_for_document(
                self.project.aggregate_id, target_id
            )
            if evidence is not None:
                self._refresh_evidences(select_id=evidence.aggregate_id)
        elif selection.kind is SelectionKind.EVIDENCE:
            self.workspace_tabs.setCurrentIndex(1)
            self._refresh_evidences(select_id=target_id)
        elif selection.kind is SelectionKind.EXECUTION_FACT and target_id is not None:
            fact = self._service.get_fact(target_id)
            self.workspace_tabs.setCurrentIndex(1)
            self._refresh_evidences(select_id=fact.evidence_id)
            self._refresh_execution_facts(select_id=target_id)
        elif selection.kind in (
            SelectionKind.CRITERION,
            SelectionKind.REQUIREMENT,
        ):
            self.workspace_tabs.setCurrentIndex(1)
        self._applying_workspace = False

    def perspective_widget(self, perspective_id: str) -> QWidget:
        """Materializa uma perspectiva produtiva no shell hospedeiro."""
        index_by_id = {
            "workspace_dashboard": 0,
            "project_explorer": 1,
            "review_workspace": 2,
            "results": 3,
            "evaluation_report": 4,
        }
        if perspective_id not in index_by_id:
            raise KeyError(perspective_id)
        if perspective_id == "results" and self.last_execution_result is not None:
            self.open_results()
        elif (
            perspective_id == "evaluation_report"
            and self.last_execution_result is not None
        ):
            self.open_evaluation_report()
        self.workspace_tabs.setCurrentIndex(index_by_id[perspective_id])
        return self

    def _replace_output_tab(
        self, index: int, widget: QWidget, title: str
    ) -> None:
        current = self.workspace_tabs.widget(index)
        if current is widget:
            return
        self.workspace_tabs.removeTab(index)
        self.workspace_tabs.insertTab(index, widget, title)
        if current is not None and current not in (
            self._results_placeholder,
            self._report_placeholder,
        ):
            current.deleteLater()

    def _reset_output_tabs(self) -> None:
        if not hasattr(self, "workspace_tabs"):
            return
        for index, placeholder, title in (
            (3, self._results_placeholder, "Results"),
            (4, self._report_placeholder, "Evaluation Report"),
        ):
            current = self.workspace_tabs.widget(index)
            if current is placeholder:
                continue
            self.workspace_tabs.removeTab(index)
            self.workspace_tabs.insertTab(index, placeholder, title)
            if current is not None:
                current.deleteLater()

    def _execute_operational_action(self, action: ExecuteEvaluationAction) -> None:
        if not isinstance(action, ExecuteEvaluationAction):
            raise TypeError("action deve ser ExecuteEvaluationAction.")
        if self.project is None or action.project_id != self.project.aggregate_id:
            self.statusBar().showMessage("Projeto indisponível para avaliação.")
            return
        self.statusBar().showMessage("Avaliação iniciada.")
        self.request_evaluation()

    def _refresh_evidences(self, *, select_id: str | None = None) -> None:
        self.evidence_list.clear()
        if self.project is not None:
            for evidence in self._service.list_evidences(
                self.project.aggregate_id
            ):
                item = QListWidgetItem(evidence.title)
                item.setData(
                    Qt.ItemDataRole.UserRole, evidence.aggregate_id
                )
                self.evidence_list.addItem(item)
                if evidence.aggregate_id == select_id:
                    self.evidence_list.setCurrentItem(item)
        self.add_evidence_button.setEnabled(
            self.project is not None
        )
        self._update_evidence_actions()
        self._refresh_execution_facts()

    def _selected_evidence_id(self) -> str | None:
        item = self.evidence_list.currentItem()
        if item is None:
            return None
        return item.data(Qt.ItemDataRole.UserRole)

    def _update_evidence_actions(self, *_args) -> None:
        enabled = (
            self.project is not None
            and self.evidence_list.currentItem() is not None
        )
        self.edit_evidence_button.setEnabled(enabled)
        self.remove_evidence_button.setEnabled(enabled)

    def _evidence_selection_changed(self, *_args) -> None:
        self._update_evidence_actions()
        if self._service is None:
            return
        self._refresh_execution_facts()
        evidence_id = self._selected_evidence_id()
        if not self._applying_workspace and evidence_id is not None:
            self._dispatch_navigation(NavigationIntent.open_evidence(
                evidence_id, project_id=self.project.aggregate_id,
                origin="project_explorer",
            ))

    def _refresh_execution_facts(
        self, *, select_id: str | None = None
    ) -> None:
        self.execution_fact_list.clear()
        if self._service is None:
            self._update_execution_fact_actions()
            return
        evidence_id = self._selected_evidence_id()
        if evidence_id is not None:
            for fact in self._service.list_facts(
                evidence_id
            ):
                item = QListWidgetItem(
                    f"{fact.fact_type}: {fact.description}"
                )
                item.setData(
                    Qt.ItemDataRole.UserRole, fact.aggregate_id
                )
                self.execution_fact_list.addItem(item)
                if fact.aggregate_id == select_id:
                    self.execution_fact_list.setCurrentItem(item)
        self.add_execution_fact_button.setEnabled(evidence_id is not None)
        self._update_execution_fact_actions()

    def _selected_execution_fact_id(self) -> str | None:
        item = self.execution_fact_list.currentItem()
        if item is None:
            return None
        return item.data(Qt.ItemDataRole.UserRole)

    def _update_execution_fact_actions(self, *_args) -> None:
        enabled = self._selected_execution_fact_id() is not None
        self.edit_execution_fact_button.setEnabled(enabled)
        self.remove_execution_fact_button.setEnabled(enabled)

    def _execution_fact_selection_changed(self, *_args) -> None:
        self._update_execution_fact_actions()
        self._refresh_binding()
        fact_id = self._selected_execution_fact_id()
        if not self._applying_workspace and fact_id is not None:
            self._dispatch_navigation(NavigationIntent.open_execution_fact(
                fact_id, project_id=self.project.aggregate_id,
                origin="project_explorer",
            ))

    def _refresh_binding(self) -> None:
        fact_id = self._selected_execution_fact_id()
        binding = (
            None
            if fact_id is None
            else self._service.get_binding_for_fact(fact_id)
        )
        if binding is None:
            self.binding_value.setText("—")
        else:
            self.binding_value.setText(
                f"{binding.criterion_id} · {binding.requirement_id}"
            )
        self.add_binding_button.setEnabled(
            fact_id is not None and binding is None
        )
        self.edit_binding_button.setEnabled(binding is not None)
        self.remove_binding_button.setEnabled(binding is not None)

    def closeEvent(self, event) -> None:
        if not self._disposed:
            if self._workspace_unsubscribe is not None:
                self._workspace_unsubscribe()
            self._disposed = True
        event.accept()


__all__ = ["ProjectExplorerWindow"]
