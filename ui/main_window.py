"""
Janela principal do ProcDocOrganizer.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QActionGroup
from PySide6.QtWidgets import (
    QComboBox,
    QLabel,
    QDockWidget,
    QMainWindow,
    QMenu,
    QProgressDialog,
    QSplitter,
    QStatusBar,
    QTabWidget,
    QToolBar,
    QWidget,
)

from contracts import ContributionCategory
from core.contribution_manager import ContributionManager
from presentation import (
    ApplicationState,
    ApplicationStateSnapshot,
    ApplicationStateStore,
    NavigationController,
    NavigationIntentType,
    Notification,
    NotificationCenter,
    OperationExecutor,
    PerspectiveDefinition,
    PerspectiveId,
    PerspectiveSnapshot,
    PerspectiveStore,
    SelectionStore,
    SelectionKind,
    WorkspaceSnapshot,
    WorkspaceStore,
    PresentationContextStore,
    PresentationSnapshot,
    ResourceIdentity,
    ResourceType,
    DocumentResourceProjector,
    EvidenceResourceProjector,
    RequirementResourceProjector,
)
from presentation.resource_inspector_view_model import (
    ResourceInspectorViewModel,
)
from ui.builtin_perspectives import create_builtin_perspective_views
from ui.main_window_contributions import (
    WindowActionSpec,
    WindowToolbarSpec,
    WindowViewSpec,
    create_compatibility_contribution_manager,
)
from ui.widgets import ProjectTreeWidget
from ui.view_manager import ViewManager
from ui.workspace_host import WorkspaceHost
from ui.resource_inspector import ResourceInspectorView

if TYPE_CHECKING:
    from models import Document, Project


class MainWindow(QMainWindow):
    """
    Janela principal da aplicação.
    """

    def __init__(
        self,
        contribution_manager: ContributionManager | None = None,
    ):
        super().__init__()

        self.contribution_manager = (
            contribution_manager
            if contribution_manager is not None
            else create_compatibility_contribution_manager()
        )
        self.setWindowTitle("ProcDocOrganizer")
        self.resize(1400, 900)

        self._base_menus_by_id: dict[str, QMenu] = {}
        self._application_menus_by_id: dict[str, QMenu] = {}
        self._create_presentation_components()

        self._create_actions()
        self._create_menu()
        self._create_toolbar()
        self._create_central_area()
        self._install_contributions()
        self._create_right_dock()
        self._create_statusbar()
        self._install_presentation_integration()

    def _create_presentation_components(self) -> None:
        self.application_state_store = ApplicationStateStore()
        self.selection_store = SelectionStore()
        self.perspective_store = PerspectiveStore()
        self.workspace_store = WorkspaceStore(self.perspective_store)
        self.presentation_context_store = PresentationContextStore(
            self.application_state_store,
            self.selection_store,
            self.perspective_store,
            self.workspace_store,
        )
        self.navigation_controller = NavigationController(
            self.perspective_store,
            self.workspace_store,
            self.selection_store,
            presentation_context=self.presentation_context_store,
        )
        self.notification_center = NotificationCenter()
        self.operation_executor = OperationExecutor(
            self.application_state_store
        )
        self.resource_projectors = {
            ResourceType.DOCUMENT: DocumentResourceProjector(),
            ResourceType.EVIDENCE: EvidenceResourceProjector(),
            ResourceType.REQUIREMENT: RequirementResourceProjector(),
        }
        self._presentation_unsubscribers = []

    # ------------------------------------------------------------------

    def _create_actions(self):

        self.action_new_project = QAction("Novo Projeto...", self)
        self.action_open_project = QAction("Abrir Projeto...", self)
        self.action_close_project = QAction("Fechar Projeto", self)
        self.action_exit = QAction("Sair", self)

        self.action_preferences = QAction("Preferências", self)

        self.action_back = QAction("Voltar", self)
        self.action_back.setObjectName("navigationBackAction")
        self.action_back.setShortcut("Alt+Left")
        self.action_back.setEnabled(False)
        self.action_back.triggered.connect(self._go_back)
        self.action_forward = QAction("Avançar", self)
        self.action_forward.setObjectName("navigationForwardAction")
        self.action_forward.setShortcut("Alt+Right")
        self.action_forward.setEnabled(False)
        self.action_forward.triggered.connect(self._go_forward)

        self.action_import_documents = QAction(
            "Importar Documentos...",
            self
        )

        self.action_process_document = QAction(
            "Processar Documento",
            self,
        )
        self.action_process_document.setEnabled(False)

        self.action_process_pending_documents = QAction(
            "Processar todos os documentos pendentes",
            self,
        )

        self.action_search_processed_text = QAction(
            "Pesquisar textos processados...",
            self,
        )
        self.action_documents_workspace = QAction("Documentos", self)
        self.action_documents_workspace.setEnabled(False)
        self.action_new_evidence = QAction(
            "Nova Evidência",
            self,
        )
        self.action_evidence_workspace = QAction("Evidências...", self)
        self.action_evidence_workspace.setEnabled(False)
        self.action_new_evidence.setEnabled(False)

        self.action_recalculate = QAction(
            "Recalcular Pontuação",
            self,
        )

        self.action_about = QAction("Sobre", self)

    # ------------------------------------------------------------------

    def _create_menu(self):

        menu = self.menuBar()

        # ---------------- Arquivo ----------------

        file_menu = menu.addMenu("Arquivo")
        self._base_menus_by_id["file"] = file_menu

        file_menu.addAction(self.action_new_project)
        file_menu.addAction(self.action_open_project)

        file_menu.addSeparator()

        file_menu.addAction(self.action_close_project)

        file_menu.addSeparator()

        file_menu.addAction(self.action_exit)

        # ---------------- Editar ----------------

        edit_menu = menu.addMenu("Editar")
        self._base_menus_by_id["edit"] = edit_menu

        edit_menu.addAction(self.action_back)
        edit_menu.addAction(self.action_forward)
        edit_menu.addSeparator()
        edit_menu.addAction(self.action_preferences)

        # ---------------- Evidências ----------------

        evidence_menu = menu.addMenu("Evidências")
        self._base_menus_by_id["evidence"] = evidence_menu

        evidence_menu.addAction(
            self.action_import_documents
        )
        evidence_menu.addAction(self.action_documents_workspace)

        evidence_menu.addAction(
            self.action_process_document
        )

        evidence_menu.addAction(
            self.action_process_pending_documents
        )

        evidence_menu.addAction(
            self.action_search_processed_text
        )

        evidence_menu.addAction(
            self.action_new_evidence
        )
        evidence_menu.addAction(self.action_evidence_workspace)

        # ---------------- Classificação ----------------

        classification_menu = menu.addMenu(
            "Classificação"
        )
        self._base_menus_by_id["classification"] = classification_menu

        classification_menu.addAction(
            self.action_recalculate
        )
        # ---------------- Ferramentas ----------------

        tools_menu = menu.addMenu("Ferramentas")
        self._base_menus_by_id["tools"] = tools_menu

        # ---------------- Ajuda ----------------

        help_menu = menu.addMenu("Ajuda")
        self._base_menus_by_id["help"] = help_menu

        help_menu.addAction(self.action_about)

        view_menu = menu.addMenu("Exibir")
        self._base_menus_by_id["view"] = view_menu
        self.perspectives_menu = view_menu.addMenu("Perspectivas")

    # ------------------------------------------------------------------

    def get_menu(self, menu_id: str) -> QMenu:
        """Retorna um menu registrado pelo seu identificador estável."""

        self._validate_menu_value(menu_id, "menu_id")

        menu = self._base_menus_by_id.get(menu_id)
        if menu is None:
            menu = self._application_menus_by_id.get(menu_id)
        if menu is None:
            raise KeyError(f"Menu não registrado: {menu_id}.")

        return menu

    def create_application_menu(
        self,
        menu_id: str,
        title: str,
    ) -> QMenu:
        """Cria e registra um menu dinâmico de nível superior."""

        self._validate_menu_value(menu_id, "menu_id")
        self._validate_menu_value(title, "title")

        if (
            menu_id in self._base_menus_by_id
            or menu_id in self._application_menus_by_id
        ):
            raise ValueError(f"ID de menu já registrado: {menu_id}.")

        application_menu = QMenu(title, self.menuBar())
        self.menuBar().addMenu(application_menu)
        self._application_menus_by_id[menu_id] = application_menu

        return application_menu

    def remove_application_menu(self, menu_id: str) -> None:
        """Remove um menu dinâmico; IDs dinâmicos ausentes são ignorados."""

        self._validate_menu_value(menu_id, "menu_id")

        if menu_id in self._base_menus_by_id:
            raise ValueError(
                f"Menu permanente não pode ser removido: {menu_id}."
            )

        application_menu = self._application_menus_by_id.pop(
            menu_id, None
        )
        if application_menu is None:
            return

        self.menuBar().removeAction(application_menu.menuAction())
        application_menu.clear()
        application_menu.deleteLater()

    @staticmethod
    def _validate_menu_value(value: str, name: str) -> None:
        if not isinstance(value, str):
            raise TypeError(f"{name} deve ser uma string.")
        if not value.strip():
            raise ValueError(f"{name} não pode ser vazio.")

    # ------------------------------------------------------------------

    def _create_toolbar(self):

        toolbar = QToolBar("Principal")
        toolbar.setObjectName("main")
        self._toolbars_by_id = {"main": toolbar}

        toolbar.setMovable(False)

        toolbar.addAction(self.action_new_project)
        toolbar.addAction(self.action_open_project)
        toolbar.addAction(self.action_close_project)

        toolbar.addSeparator()

        toolbar.addAction(self.action_back)
        toolbar.addAction(self.action_forward)

        toolbar.addSeparator()

        toolbar.addAction(
            self.action_import_documents
        )
        toolbar.addAction(self.action_documents_workspace)

        toolbar.addAction(
            self.action_process_document
        )

        toolbar.addAction(
            self.action_process_pending_documents
        )

        toolbar.addAction(
            self.action_search_processed_text
        )
        toolbar.addAction(self.action_evidence_workspace)
        toolbar.addSeparator()
        self.perspective_selector = QComboBox(toolbar)
        self.perspective_selector.setObjectName("perspectiveSelector")
        self.perspective_selector.setToolTip("Perspectiva ativa")
        toolbar.addWidget(self.perspective_selector)
        self.addToolBar(toolbar)

    # ------------------------------------------------------------------

    def _create_central_area(self):

        self.workspace_host = WorkspaceHost()
        self.stack = self.workspace_host
        self.view_manager = ViewManager(self.stack)

        builtin_views = create_builtin_perspective_views(
            self.contribution_manager,
            {
                "new_project": self.action_new_project.trigger,
                "open_project": self.action_open_project.trigger,
                "documents": self.action_documents_workspace.trigger,
                "search": self.action_search_processed_text.trigger,
                "evidence": self.action_evidence_workspace.trigger,
                "import_documents": self.action_import_documents.trigger,
                "process_documents": (
                    self.action_process_pending_documents.trigger
                ),
            },
        )
        for view_id, view in builtin_views.items():
            self.view_manager.register(view_id, view)
        self.views = self.view_manager.views
        for view_id, attribute_name in (
            ("pdf", "pdf_view"),
            ("search", "search_workspace"),
            ("evidence", "evidence_workspace"),
            ("documents", "documents_workspace"),
            ("home", "home_view"),
        ):
            setattr(self, attribute_name, builtin_views[view_id])

        self.project_tree = ProjectTreeWidget()
        self.project_tree.setMinimumWidth(180)
        self.stack.setMinimumWidth(300)

        self.content_splitter = QSplitter(
            Qt.Orientation.Horizontal,
            self,
        )
        self.content_splitter.setChildrenCollapsible(False)
        self.content_splitter.setHandleWidth(8)
        self.content_splitter.setOpaqueResize(True)
        self.content_splitter.addWidget(self.project_tree)
        self.content_splitter.addWidget(self.stack)
        self.content_splitter.setStretchFactor(0, 0)
        self.content_splitter.setStretchFactor(1, 1)
        self.content_splitter.setSizes([280, 900])

        self.setCentralWidget(self.content_splitter)

    def _install_contributions(self) -> None:
        """Materializa contribuições sem reconhecer Applications concretas."""

        self._installed_window_actions = []
        for registration in self.contribution_manager.by_category(
            ContributionCategory.ACTION
        ):
            contribution = registration.contribution
            if not isinstance(contribution, WindowActionSpec):
                continue
            if hasattr(self, contribution.attribute_name):
                raise ValueError(
                    "Atributo de action duplicado: "
                    f"{contribution.attribute_name}."
                )
            action = QAction(contribution.text, self)
            action.setVisible(contribution.visible)
            action.setEnabled(contribution.enabled)
            if contribution.tooltip is not None:
                action.setToolTip(contribution.tooltip)
            if contribution.object_name is not None:
                action.setObjectName(contribution.object_name)
            self.get_menu(contribution.menu_id).addAction(action)
            setattr(self, contribution.attribute_name, action)
            self._installed_window_actions.append(
                (action, contribution)
            )

        for registration in self.contribution_manager.by_category(
            ContributionCategory.VIEW
        ):
            contribution = registration.contribution
            if not isinstance(contribution, WindowViewSpec):
                continue
            if contribution.view_id in self.views:
                raise ValueError(
                    f"View duplicada: {contribution.view_id}."
                )
            view = contribution.factory()
            self.view_manager.register(contribution.view_id, view)
            setattr(self, contribution.attribute_name, view)
            setattr(
                self,
                contribution.show_method_name,
                lambda view_id=contribution.view_id: self.show_view(view_id),
            )
            if contribution.open_project_action is not None:
                view.open_project_requested.connect(
                    getattr(
                        self,
                        contribution.open_project_action,
                    ).trigger
                )

        for registration in self.contribution_manager.by_category(
            ContributionCategory.TOOLBAR
        ):
            contribution = registration.contribution
            if not isinstance(contribution, WindowToolbarSpec):
                continue
            toolbar = self._toolbars_by_id.get(contribution.toolbar_id)
            if toolbar is None:
                raise KeyError(
                    f"Toolbar não registrada: {contribution.toolbar_id}."
                )
            toolbar.addAction(
                getattr(self, contribution.action_attribute)
            )

    # ------------------------------------------------------------------

    def _create_right_dock(self):

        self.properties_label = QLabel(

            "Nenhum item selecionado",

            alignment=Qt.AlignmentFlag.AlignTop,

        )

        dock = QDockWidget(

            "Propriedades",
            self,

        )

        dock.setAllowedAreas(

            Qt.LeftDockWidgetArea
            | Qt.RightDockWidgetArea

        )

        self.resource_inspector = ResourceInspectorView(
            ResourceInspectorViewModel.empty().data,
            self,
        )
        self.resource_inspector.navigation_requested.connect(
            self.navigation_controller.navigate
        )
        inspector_tabs = QTabWidget(dock)
        inspector_tabs.addTab(self.resource_inspector, "Resource")
        inspector_tabs.addTab(self.properties_label, "Documento")
        dock.setWidget(inspector_tabs)
        self.resource_inspector_dock = dock

        self.addDockWidget(
            Qt.RightDockWidgetArea,
            dock,
        )

    # ------------------------------------------------------------------

    def _create_statusbar(self):

        status = QStatusBar()

        self.status_message = QLabel(
            "Nenhum projeto aberto"
        )

        self.version_label = QLabel("v1.0")

        status.addWidget(
            self.status_message
        )

        status.addPermanentWidget(
            self.version_label
        )

        self.setStatusBar(status)

    def _install_presentation_integration(self) -> None:
        titles = {
            "home": "Visão geral",
            "pdf": "Documento",
            "search": "Pesquisa",
            "evidence": "Evidências",
            "documents": "Documentos",
            "timeline": "Timeline",
            "reports": "Relatórios",
        }
        for order, (view_id, view) in enumerate(
            self.views.items(), start=1
        ):
            self.perspective_store.register(
                PerspectiveDefinition(
                    id=PerspectiveId(view_id),
                    title=titles.get(
                        view_id,
                        view_id.replace("_", " ").title(),
                    ),
                    order=order,
                    icon=None,
                    requires_project=view_id != "home",
                    factory=lambda widget=view: widget,
                )
            )

        self._presentation_unsubscribers.extend(
            (
                self.application_state_store.subscribe(
                    self._on_application_state_changed
                ),
                self.workspace_store.subscribe(
                    self._on_workspace_changed
                ),
                self.perspective_store.subscribe(
                    self._on_perspectives_changed
                ),
                self.notification_center.subscribe(
                    self._on_notification
                ),
                self.presentation_context_store.subscribe(
                    self._on_resource_context_changed
                ),
            )
        )
        self._install_perspective_navigation()
        self._on_application_state_changed(
            self.application_state_store.snapshot
        )
        self.navigation_controller.navigate_to(PerspectiveId("home"))
        self._on_resource_context_changed(
            self.presentation_context_store.snapshot
        )

    def install_productive_workspace(self, workspace: QWidget) -> None:
        """Registra o Workspace produtivo na infraestrutura oficial."""
        perspective_widget = getattr(workspace, "perspective_widget", None)
        if not callable(perspective_widget):
            raise TypeError(
                "workspace deve fornecer perspective_widget(id)."
            )
        if self.workspace_host.indexOf(workspace) < 0:
            self.workspace_host.addWidget(workspace)
        definitions = (
            ("workspace_dashboard", "Workspace Dashboard"),
            ("review_workspace", "Review Workspace"),
            ("project_explorer", "Project Explorer"),
            ("results", "Results Explorer"),
            ("evaluation_report", "Evaluation Report"),
        )
        first_order = len(self.perspective_store.list_all()) + 1
        for offset, (identifier, title) in enumerate(definitions):
            perspective_id = PerspectiveId(identifier)
            self.perspective_store.register(PerspectiveDefinition(
                id=perspective_id,
                title=title,
                order=first_order + offset,
                icon=None,
                requires_project=identifier != "project_explorer",
                factory=lambda value=identifier: perspective_widget(value),
            ))
        route_ids = {
            NavigationIntentType.OPEN_DASHBOARD: "workspace_dashboard",
            NavigationIntentType.OPEN_DOCUMENT: "project_explorer",
            NavigationIntentType.OPEN_EVIDENCE: "project_explorer",
            NavigationIntentType.OPEN_EXECUTION_FACT: "project_explorer",
            NavigationIntentType.OPEN_REQUIREMENT: "project_explorer",
            NavigationIntentType.OPEN_CRITERION: "project_explorer",
            NavigationIntentType.OPEN_EVALUATION: "results",
            NavigationIntentType.OPEN_REPORT: "evaluation_report",
        }
        for intent_type, identifier in route_ids.items():
            self.navigation_controller.register_route(
                intent_type, PerspectiveId(identifier)
            )
        self.productive_workspace = workspace

    def _go_back(self) -> None:
        self.navigation_controller.go_back()
        self._update_history_actions()

    def _go_forward(self) -> None:
        self.navigation_controller.go_forward()
        self._update_history_actions()

    def _update_history_actions(self) -> None:
        self.action_back.setEnabled(
            self.navigation_controller.can_go_back
        )
        self.action_forward.setEnabled(
            self.navigation_controller.can_go_forward
        )

    def _on_resource_context_changed(
        self, snapshot: PresentationSnapshot
    ) -> None:
        identity = self._resource_identity(snapshot)
        if identity is None:
            data = ResourceInspectorViewModel.empty().data
        else:
            projector = self.resource_projectors.get(identity.resource_type)
            if projector is None:
                data = ResourceInspectorViewModel.unavailable(identity).data
            else:
                try:
                    resource = projector.project(identity, snapshot.workspace)
                except Exception:
                    data = ResourceInspectorViewModel.unavailable(identity).data
                else:
                    data = ResourceInspectorViewModel.from_resource(
                        resource
                    ).data
        self.resource_inspector.set_data(data)
        self._update_history_actions()

    @staticmethod
    def _resource_identity(
        snapshot: PresentationSnapshot,
    ) -> ResourceIdentity | None:
        selection = snapshot.workspace.selection.identity
        if selection.identifier is None:
            return None
        type_by_kind = {
            SelectionKind.DOCUMENT: ResourceType.DOCUMENT,
            SelectionKind.EVIDENCE: ResourceType.EVIDENCE,
            SelectionKind.EXECUTION_FACT: ResourceType.EXECUTION_FACT,
            SelectionKind.REQUIREMENT: ResourceType.REQUIREMENT,
        }
        resource_type = type_by_kind.get(selection.kind)
        if resource_type is None:
            return None
        return ResourceIdentity(resource_type, selection.identifier)

    def _install_perspective_navigation(self) -> None:
        self._perspective_action_group = QActionGroup(self)
        self._perspective_action_group.setExclusive(True)
        self.perspective_selector.currentIndexChanged.connect(
            self._navigate_from_perspective_selector
        )
        self._on_perspectives_changed(self.perspective_store.snapshot)

    def _on_perspectives_changed(
        self, snapshot: PerspectiveSnapshot
    ) -> None:
        self.perspectives_menu.clear()
        for action in self._perspective_action_group.actions():
            self._perspective_action_group.removeAction(action)
            action.deleteLater()
        self.perspective_selector.blockSignals(True)
        self.perspective_selector.clear()
        application = self.application_state_store.snapshot
        is_available = application.state not in (
            ApplicationState.BUSY,
            ApplicationState.CLOSING,
        )
        for definition in snapshot.available:
            action = QAction(definition.title, self)
            action.setCheckable(True)
            action.setData(definition.id.value)
            action.setChecked(definition.id == snapshot.active)
            action.setEnabled(
                is_available
                and (
                    application.has_project
                    or not definition.requires_project
                )
            )
            action.triggered.connect(
                lambda _checked=False, perspective_id=definition.id: (
                    self.navigation_controller.navigate_to(perspective_id)
                )
            )
            self._perspective_action_group.addAction(action)
            self.perspectives_menu.addAction(action)
            self.perspective_selector.addItem(
                definition.title,
                definition.id.value,
            )
            index = self.perspective_selector.count() - 1
            self.perspective_selector.model().item(index).setEnabled(
                action.isEnabled()
            )
            if definition.id == snapshot.active:
                self.perspective_selector.setCurrentIndex(index)
        self.perspective_selector.blockSignals(False)

    def _navigate_from_perspective_selector(self, index: int) -> None:
        value = self.perspective_selector.itemData(index)
        if value is not None:
            self.navigation_controller.navigate_to(PerspectiveId(value))

    def _on_application_state_changed(
        self, snapshot: ApplicationStateSnapshot
    ) -> None:
        previous_project_id = getattr(self, "_history_project_id", None)
        if snapshot.project_id != previous_project_id:
            self.navigation_controller.clear_history()
            self._history_project_id = snapshot.project_id
            self._update_history_actions()
        has_project = snapshot.has_project
        is_available = snapshot.state not in (
            ApplicationState.BUSY,
            ApplicationState.CLOSING,
        )
        self.setWindowTitle(
            (
                f"ProcDocOrganizer — {snapshot.project_id}"
                if has_project and snapshot.project_id is not None
                else "ProcDocOrganizer"
            )
        )
        self.action_new_project.setEnabled(is_available)
        self.action_open_project.setEnabled(is_available)
        self.action_close_project.setEnabled(has_project and is_available)
        self.action_documents_workspace.setEnabled(
            has_project and is_available
        )
        self.action_evidence_workspace.setEnabled(
            has_project and is_available
        )
        self.action_new_evidence.setEnabled(has_project and is_available)
        for definition, action in zip(
            self.perspective_store.list_all(),
            self._perspective_action_group.actions(),
            strict=True,
        ):
            enabled = (
                is_available
                and (has_project or not definition.requires_project)
            )
            action.setEnabled(enabled)
            index = self.perspective_selector.findData(
                definition.id.value
            )
            self.perspective_selector.model().item(index).setEnabled(enabled)

        if snapshot.state is ApplicationState.BUSY:
            self.status_message.setText("Operação em andamento")
        elif snapshot.state is ApplicationState.ERROR:
            self.status_message.setText(
                f"Erro: {snapshot.error}"
            )
        elif not snapshot.has_project:
            self.status_message.setText("Nenhum projeto aberto")
        elif snapshot.project_id is not None:
            self.status_message.setText(
                f"Projeto: {snapshot.project_id}"
            )

    def _on_workspace_changed(
        self, snapshot: WorkspaceSnapshot
    ) -> None:
        if snapshot.active_perspective is None:
            return
        definition = self.perspective_store.get(
            snapshot.active_perspective
        )
        widget = definition.factory()
        if not isinstance(widget, QWidget):
            raise TypeError(
                "factory da perspectiva deve retornar QWidget."
            )
        self.workspace_host.set_active_widget(widget)
        for action in self._perspective_action_group.actions():
            action.setChecked(
                action.data() == snapshot.active_perspective.value
            )
        index = self.perspective_selector.findData(
            snapshot.active_perspective.value
        )
        if index >= 0:
            self.perspective_selector.blockSignals(True)
            self.perspective_selector.setCurrentIndex(index)
            self.perspective_selector.blockSignals(False)

    def _on_notification(self, notification: Notification) -> None:
        timeout = (
            0
            if notification.timeout is None
            else round(notification.timeout * 1000)
        )
        self.statusBar().showMessage(notification.message, timeout)

    # ------------------------------------------------------------------

    def show_view(
        self,
        name: str,
    ):
        """
        Exibe uma view registrada.
        """

        if not isinstance(name, str) or not name.strip():
            return False
        perspective_id = PerspectiveId(name)
        if not self.perspective_store.contains(perspective_id):
            return False
        self.navigation_controller.navigate_to(perspective_id)
        return (
            self.perspective_store.snapshot.active
            == perspective_id
        )

    # ------------------------------------------------------------------

    def set_project(
        self,
        project: Project,
        documents: list[Document] | None = None,
    ):
        """
        Atualiza toda a interface para um projeto aberto.
        """

        root = self.project_tree.topLevelItem(0)
        had_project = (
            root is not None
            and root.text(0) != "Nenhum projeto aberto"
        )
        self.action_evidence_workspace.setEnabled(True)
        self.action_new_evidence.setEnabled(True)
        self.action_documents_workspace.setEnabled(True)

        self.project_tree.load_project(
            project,
            documents,
        )

        self.status_message.setText(
            f"Projeto: {project.project_name}"
        )

        self.clear_document_properties()
        self.search_workspace.clear()
        self.pdf_view.clear_document()

        if had_project:
            self.view_manager.notify_project_changed(project)
        else:
            self.view_manager.notify_project_opened(project)

    # ------------------------------------------------------------------

    def clear_project(self):
        """
        Limpa toda a interface.
        """

        self.action_evidence_workspace.setEnabled(False)
        self.action_new_evidence.setEnabled(False)
        self.action_documents_workspace.setEnabled(False)
        for action, contribution in self._installed_window_actions:
            if contribution.disable_on_project_close:
                action.setEnabled(False)

        self.project_tree.clear_project()

        self.status_message.setText(
            "Nenhum projeto aberto"
        )

        self.clear_document_properties()
        self.search_workspace.clear()
        self.pdf_view.clear_document()

        self.view_manager.notify_project_closed(
            exclude=(self.evidence_workspace,)
        )

    # ------------------------------------------------------------------

    def show_search(self):
        """
        Exibe o painel de pesquisa textual.
        """

        self.show_view("search")
        self.search_workspace.focus_search()

    def show_evidences(self):
        """Exibe o workspace central de evidências."""

        self.show_view("evidence")

    def show_documents(self):
        """Exibe a infraestrutura inicial do catálogo documental."""

        self.show_view("documents")

    def set_close_guard(self, guard) -> None:
        self._close_guard = guard

    def closeEvent(self, event) -> None:
        guard = getattr(self, "_close_guard", None)
        if guard is None or guard():
            self._dispose_presentation_integration()
            event.accept()
        else:
            event.ignore()

    def _dispose_presentation_integration(self) -> None:
        productive_workspace = getattr(
            self, "productive_workspace", None
        )
        if productive_workspace is not None:
            productive_workspace.close()
        while self._presentation_unsubscribers:
            self._presentation_unsubscribers.pop()()

    # ------------------------------------------------------------------

    def set_document_properties(self, document: Document):
        self.properties_label.setText(
            "\n".join(
                (
                    f"Nome: {document.name}",
                    f"Caminho: {document.relative_path}",
                    f"Importado em: {document.imported_at}",
                    f"Páginas: {document.pages}",
                    f"Status: {document.status}",
                    self._processing_status_text(document),
                    f"SHA-256: {document.sha256}",
                )
            )
        )
        self.action_process_document.setEnabled(True)

    # ------------------------------------------------------------------

    @staticmethod
    def _processing_status_text(document: Document) -> str:
        """
        Retorna a descrição visual do estado de processamento.
        """

        if document.processing_status == "ocr_required":
            return "Documento sem texto pesquisável. OCR necessário."

        return f"Processamento: {document.processing_status}"

    # ------------------------------------------------------------------

    def clear_document_properties(self):
        self.properties_label.setText("Nenhum item selecionado")
        self.action_process_document.setEnabled(False)

    # ------------------------------------------------------------------

    def create_processing_progress(self, total: int) -> QProgressDialog:
        """
        Cria o diálogo de progresso para processamento em lote.
        """

        dialog = QProgressDialog(
            "Preparando processamento...",
            "Cancelar",
            0,
            total,
            self,
        )
        dialog.setWindowTitle("Processamento em lote")
        dialog.setWindowModality(Qt.WindowModality.WindowModal)
        dialog.setAutoClose(False)
        dialog.setAutoReset(False)
        dialog.setMinimumDuration(0)

        return dialog

    # ------------------------------------------------------------------

    @staticmethod
    def update_processing_progress(
        dialog: QProgressDialog,
        document: Document,
        position: int,
        total: int,
        completed: int,
        ocr_required: int,
        failed: int,
        skipped: int,
    ) -> None:
        """
        Atualiza exclusivamente a apresentação do progresso em lote.
        """

        dialog.setLabelText(
            f"Processando: {document.name}\n"
            f"Documento {position} de {total} | "
            f"Concluídos: {completed} | OCR necessário: {ocr_required} | "
            f"Falhas: {failed} | "
            f"Ignorados: {skipped}"
        )
        dialog.setValue(position - 1)

    # ------------------------------------------------------------------

    def show_document(self, document_path, page: int | None = None):
        """
        Exibe um documento na área central.
        """

        self.pdf_view.open_document(document_path)
        self.show_view("pdf")

        if page is not None:
            self.pdf_view.show_page(page)
