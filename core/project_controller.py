"""
Controller responsável pelo gerenciamento de projetos.
"""

from pathlib import Path

from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QDialog,
    QMessageBox,
)

from ui.dialogs import NewProjectDialog
from ui.contribution_installer import DesktopContributionInstaller
from controllers import (
    DocumentsController,
    EvidenceController,
    SearchController,
)
from presentation.dashboard import DashboardController
from presentation.activities import ActivitiesController
from presentation.functional_assignments import (
    FunctionalAssignmentsController,
)
from presentation.functional_exercises import FunctionalExercisesController
from presentation import (
    ApplicationState,
    NavigationIntent,
    Notification,
    NotificationLevel,
    OperationId,
    PerspectiveId,
)

from models import DocumentProcessingStatus
from services.processing import DocumentProcessor

from .project_session_factory import ProjectSessionFactory
class ProjectController:
    """
    Coordena as operações relacionadas aos projetos.
    """

    DEFAULT_BATCH_LIMIT = 100

    def __init__(
        self,
        window,
        manager,
        state,
        contribution_installer: DesktopContributionInstaller,
        batch_limit: int = DEFAULT_BATCH_LIMIT,
        session_factory=None,
        application_registry=None,
        lifecycle_host=None,
        prepare_session_consumers=None,
        commit_session_consumers=None,
        rollback_session_consumers=None,
        close_session_consumers=None,
        active_project_id=None,
        initial_perspective: str = "home",
    ):
        self.window = window
        self.manager = manager
        self.state = state
        self.batch_limit = max(1, batch_limit)
        self.session_factory = session_factory or ProjectSessionFactory()
        self.application_registry = application_registry
        self.contribution_installer = contribution_installer
        if lifecycle_host is None:
            raise ValueError("lifecycle_host é obrigatório.")
        self.lifecycle_host = lifecycle_host
        self._prepare_session_consumers = prepare_session_consumers
        self._commit_session_consumers = commit_session_consumers
        self._rollback_session_consumers = rollback_session_consumers
        self._close_session_consumers = close_session_consumers
        self._active_project_id = active_project_id
        self._initial_perspective = initial_perspective
        self.selected_document = None
        self.document_processor = DocumentProcessor()
        self.dashboard_controller = DashboardController(
            self.window.views["home"]
        )
        self.activities_controller = ActivitiesController(
            self.window.views["activities"],
            parent=self.window,
            assignment_navigation_requested=(
                self._navigate_to_functional_assignment
            ),
            exercise_navigation_requested=(
                self._navigate_to_functional_exercise
            ),
            selection_store=self.window.selection_store,
            notify=self._show_activity_message,
            confirm_delete=self._confirm_delete_activity,
            confirm_unsaved=self._confirm_unsaved_activity,
        )
        self.functional_assignments_controller = (
            FunctionalAssignmentsController(
                self.window.views["functional_assignments"],
                parent=self.window,
                evidence_navigation_requested=self._navigate_to_evidence,
                selection_store=self.window.selection_store,
                notify=self._show_functional_assignment_message,
                confirm_delete=self._confirm_delete_functional_assignment,
            )
        )
        self.functional_exercises_controller = FunctionalExercisesController(
            self.window.views["functional_exercises"],
            parent=self.window,
            assignment_navigation_requested=(
                self._navigate_to_functional_assignment
            ),
            selection_store=self.window.selection_store,
            notify=self._show_functional_exercise_message,
            confirm_delete=self._confirm_delete_functional_exercise,
        )
        self.search_controller = SearchController(
            self.window.search_workspace,
            document_navigation_requested=self._navigate_from_search,
        )
        self.documents_controller = DocumentsController(
            self.window.documents_workspace,
            evidence_source_requested=self._create_evidence_from_documents,
            document_remove_requested=self._remove_document,
            document_open_requested=self._open_workspace_document,
            document_ocr_requested=self._process_workspace_document,
            selection_store=self.window.selection_store,
            document_metadata_update_requested=(
                self._update_document_metadata
            ),
            confirm_unsaved_metadata=(
                self._confirm_unsaved_document_metadata
            ),
            notify=self._show_document_metadata_message,
        )
        self.evidence_controller = EvidenceController(
            self.window.evidence_workspace,
            confirm_unsaved=self._confirm_unsaved_evidence,
            confirm_delete=self._confirm_delete_evidence,
            confirm_duplicates=self._confirm_duplicate_evidence,
            notify=self._show_evidence_message,
            document_navigation_requested=self._navigate_from_evidence,
            selection_store=self.window.selection_store,
            deletion_allowed=False,
        )
        self.search_controller.set_evidence_source_requested(
            self._create_evidence_from_search
        )
        self.window.set_close_guard(self.evidence_controller.can_leave)

        self._connect_signals()

    @property
    def session(self):
        """Projeção transitória da autoridade oficial."""

        return self.lifecycle_host.current_session

    # ------------------------------------------------------------------

    def _connect_signals(self):
        """
        Conecta os sinais da interface.
        """

        self.window.action_new_project.triggered.connect(
            self.new_project
        )

        self.window.action_open_project.triggered.connect(
            self.open_project
        )

        self.window.action_import_documents.triggered.connect(
            self.import_documents
        )

        self.window.action_process_document.triggered.connect(
            self.process_document
        )

        self.window.action_process_pending_documents.triggered.connect(
            self.process_pending_documents
        )

        self.window.action_search_processed_text.triggered.connect(
            self.show_search
        )
        self.window.action_documents_workspace.triggered.connect(
            self.show_documents
        )
        self.window.action_evidence_workspace.triggered.connect(
            self.show_evidences
        )
        self.window.action_activities.triggered.connect(
            self.show_activities
        )
        self.window.action_functional_assignments.triggered.connect(
            self.show_functional_assignments
        )
        self.window.action_functional_exercises.triggered.connect(
            self.show_functional_exercises
        )
        self.window.functional_assignments_view.create_exercise_requested.connect(
            self.create_functional_exercise
        )
        self.window.functional_exercises_view.create_activity_requested.connect(
            self.create_activity
        )
        self.window.functional_assignments_view.create_activity_requested.connect(
            self.create_activity_from_assignments
        )
        self.window.evidence_workspace.interpret_functionally_requested.connect(
            self.interpret_selected_evidence
        )
        self.window.action_new_evidence.triggered.connect(
            self.new_evidence
        )
        self.window.action_close_project.triggered.connect(
            self.close_project
        )
        self.window.action_exit.triggered.connect(self.window.close)

        self.window.project_tree.document_selected.connect(
            self._select_document
        )

    # ------------------------------------------------------------------

    def _load_project(self, project):
        """
        Inicializa um projeto na aplicação.
        """

        previous_session = self.lifecycle_host.current_session
        session = self.session_factory.create(project)
        prepared_consumers = None
        contributions_changed = False
        publish_started = False
        application = getattr(session, "application", None)
        contributions = (
            application.contributions()
            if application is not None
            else ()
        )

        try:
            if self._prepare_session_consumers is not None:
                prepared_consumers = self._prepare_session_consumers(session)
            if previous_session is None:
                self.contribution_installer.install(contributions)
            else:
                self.contribution_installer.replace(contributions)
            contributions_changed = True
        except Exception:
            self.lifecycle_host.dispose_session(session)
            self._abort_prepared_consumers(prepared_consumers)
            raise

        def publish(candidate, previous):
            nonlocal publish_started
            publish_started = True
            self._bind_session(candidate)
            if self._commit_session_consumers is not None:
                self._commit_session_consumers(
                    candidate, prepared_consumers, previous
                )

        def rollback(previous, candidate):
            if self._rollback_session_consumers is not None:
                self._rollback_session_consumers(
                    previous, candidate, prepared_consumers
                )
            if previous is None:
                self._unbind_session()
            else:
                self._bind_session(previous)
            if contributions_changed:
                self._restore_contributions(previous)

        try:
            self.lifecycle_host.activate_session(
                session,
                after_publish=publish,
                rollback=rollback,
            )
        except Exception:
            self._abort_prepared_consumers(prepared_consumers)
            if contributions_changed and not publish_started:
                self._restore_contributions(previous_session)
            raise

    def _bind_session(self, session):
        self.document_processor = getattr(
            session,
            "document_processor",
            getattr(self, "document_processor", None),
        )
        self.selected_document = None
        self.search_controller.set_search_service(session.search_service)
        self.evidence_controller.set_service(session.evidence_service)

        self.window.set_project(
            session.project,
            session.document_repository.list_documents(),
        )
        self.documents_controller.set_service(session.document_service)
        self.documents_controller.load()
        dashboard_controller = getattr(
            self, "dashboard_controller", None
        )
        if dashboard_controller is not None:
            dashboard_controller.set_session(session)
        activities_controller = getattr(
            self, "activities_controller", None
        )
        if activities_controller is not None:
            activities_controller.set_session(session)
        functional_controller = getattr(
            self, "functional_assignments_controller", None
        )
        if functional_controller is not None:
            functional_controller.set_session(session)
        exercise_controller = getattr(
            self, "functional_exercises_controller", None
        )
        if exercise_controller is not None:
            exercise_controller.set_session(session)
        is_rsc = getattr(session, "rsc_session", None) is not None
        evidence_workspace = getattr(
            self.window, "evidence_workspace", None
        )
        if evidence_workspace is not None:
            evidence_workspace.set_functional_interpretation_available(
                is_rsc
            )
        assignments_action = getattr(
            self.window, "action_functional_assignments", None
        )
        if assignments_action is not None:
            assignments_action.setVisible(is_rsc)
            assignments_action.setEnabled(is_rsc)
        exercises_action = getattr(
            self.window, "action_functional_exercises", None
        )
        if exercises_action is not None:
            exercises_action.setVisible(is_rsc)
            exercises_action.setEnabled(is_rsc)
        activities_action = getattr(
            self.window, "action_activities", None
        )
        if activities_action is not None:
            activities_action.setEnabled(
                getattr(session, "rsc_session", None) is not None
            )

    def _unbind_session(self):
        self.evidence_controller.set_service(None)
        self.documents_controller.set_service(None)
        self.search_controller.set_search_service(None)
        self.selected_document = None
        self.window.clear_project()
        for controller_name in (
            "dashboard_controller",
            "activities_controller",
            "functional_assignments_controller",
            "functional_exercises_controller",
        ):
            controller = getattr(self, controller_name, None)
            clear = getattr(controller, "clear_session", None)
            if callable(clear):
                clear()

    def _restore_contributions(self, session):
        if session is None:
            self.contribution_installer.clear()
            return
        application = getattr(session, "application", None)
        contributions = (
            application.contributions()
            if application is not None
            else ()
        )
        self.contribution_installer.replace(contributions)

    @staticmethod
    def _abort_prepared_consumers(prepared):
        close = getattr(prepared, "close", None)
        if callable(close):
            close()

    def _execute_lifecycle_operation(self, operation_id, work):
        executor = getattr(self.window, "operation_executor", None)
        if executor is None:
            return work()
        application_state = self.window.application_state_store
        snapshot = application_state.snapshot
        if snapshot.state is ApplicationState.ERROR:
            target = snapshot.previous_state or ApplicationState.NO_PROJECT
            application_state.transition_to(
                target,
                project_id=snapshot.project_id,
            )
        return executor.execute(
            OperationId(operation_id),
            lambda _context: work(),
        )

    def _publish_project_notification(
        self,
        level,
        title,
        message,
    ) -> bool:
        center = getattr(self.window, "notification_center", None)
        if center is None:
            return False
        center.publish(Notification(level, title, message))
        return True

    def _complete_project_open(self, project, message) -> None:
        project_id = (
            self._active_project_id(self.lifecycle_host.current_session)
            if self._active_project_id is not None
            else project.project_name
        )
        application_state = getattr(
            self.window, "application_state_store", None
        )
        if application_state is not None:
            if application_state.snapshot.has_project:
                application_state.transition_to(
                    ApplicationState.NO_PROJECT
                )
            application_state.transition_to(
                ApplicationState.PROJECT_OPEN,
                project_id=project_id,
            )
        navigation = getattr(
            self.window, "navigation_controller", None
        )
        if navigation is not None:
            initial_perspective = (
                self._initial_perspective(self.lifecycle_host.current_session)
                if callable(self._initial_perspective)
                else self._initial_perspective
            )
            if initial_perspective == "workspace_dashboard":
                navigation.navigate(
                    NavigationIntent.open_dashboard(project_id=project_id)
                )
            else:
                navigation.navigate_to(PerspectiveId(initial_perspective))
        self._publish_project_notification(
            NotificationLevel.SUCCESS,
            "Projeto",
            message,
        )

    def _complete_project_close(self) -> None:
        workspace = getattr(self.window, "workspace_store", None)
        if workspace is not None:
            workspace.clear()
        selection = getattr(self.window, "selection_store", None)
        if selection is not None:
            selection.clear()
        application_state = getattr(
            self.window, "application_state_store", None
        )
        if (
            application_state is not None
            and application_state.snapshot.state
            is not ApplicationState.NO_PROJECT
        ):
            application_state.transition_to(ApplicationState.NO_PROJECT)
        navigation = getattr(self.window, "navigation_controller", None)
        if navigation is not None:
            perspective_store = getattr(
                self.window, "perspective_store", None
            )
            available = (
                () if perspective_store is None else perspective_store.list_all()
            )
            if any(
                item.id == PerspectiveId("project_explorer")
                for item in available
            ):
                navigation.navigate_to(PerspectiveId("project_explorer"))
            navigation.clear_history()
        self._publish_project_notification(
            NotificationLevel.INFO,
            "Projeto",
            "Projeto fechado.",
        )

    def new_project(self):
        """
        Cria um novo projeto.
        """

        if not self.evidence_controller.can_leave():
            return

        descriptors = (
            self.application_registry.descriptors
            if self.application_registry is not None
            else ()
        )
        dialog = NewProjectDialog(
            self.window,
            descriptors=descriptors,
        )

        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        try:

            def create_and_load():
                project = self.manager.create_project(
                    dialog.get_project_name(),
                    dialog.get_project_folder(),
                    application_id=dialog.get_application_id(),
                )
                self._load_project(project)
                return project

            project = self._execute_lifecycle_operation(
                "project-create",
                create_and_load,
            )
            self._complete_project_open(project, "Projeto criado.")

        except FileExistsError as exc:

            if not self._publish_project_notification(
                NotificationLevel.WARNING,
                "Projeto já existe",
                str(exc),
            ):
                QMessageBox.warning(
                    self.window,
                    "Projeto já existe",
                    str(exc),
                )

            return

        except Exception as exc:

            message = f"Não foi possível criar o projeto: {exc}"
            if not self._publish_project_notification(
                NotificationLevel.ERROR,
                "Erro ao criar",
                message,
            ):
                QMessageBox.critical(
                    self.window,
                    "Erro",
                    f"Não foi possível criar o projeto.\n\n{exc}",
                )

            return

    # ------------------------------------------------------------------

    def open_project(self):
        """
        Abre um projeto existente.
        """

        if not self.evidence_controller.can_leave():
            return

        folder = QFileDialog.getExistingDirectory(
            self.window,
            "Selecionar Projeto",
        )

        if not folder:
            return

        try:

            def open_and_load():
                project = self.manager.open_project(Path(folder))
                self._load_project(project)
                return project

            project = self._execute_lifecycle_operation(
                "project-open",
                open_and_load,
            )
            self._complete_project_open(project, "Projeto aberto.")

        except FileNotFoundError as exc:

            if not self._publish_project_notification(
                NotificationLevel.WARNING,
                "Projeto inválido",
                str(exc),
            ):
                QMessageBox.warning(
                    self.window,
                    "Projeto inválido",
                    str(exc),
                )

            return

        except Exception as exc:

            message = f"Não foi possível abrir o projeto: {exc}"
            if not self._publish_project_notification(
                NotificationLevel.ERROR,
                "Erro ao abrir",
                message,
            ):
                QMessageBox.critical(
                    self.window,
                    "Erro",
                    f"Não foi possível abrir o projeto.\n\n{exc}",
                )

            return

    # ------------------------------------------------------------------

    def import_documents(self):
        """
        Importa documentos para o projeto atual.
        """

        if not self.state.has_project:

            QMessageBox.information(
                self.window,
                "Nenhum projeto",
                "Abra um projeto antes de importar documentos.",
            )

            return

        if not getattr(
            self.documents_controller,
            "can_leave_metadata",
            lambda: True,
        )():
            return

        files, _ = QFileDialog.getOpenFileNames(
            self.window,
            "Importar Documentos",
            "",
            "Arquivos PDF (*.pdf)",
        )

        if not files:
            self._publish_project_notification(
                NotificationLevel.INFO,
                "Documentos",
                "Importação cancelada.",
            )
            return

        invalid_files = tuple(
            path for path in files if Path(path).suffix.casefold() != ".pdf"
        )
        if invalid_files:
            self._publish_project_notification(
                NotificationLevel.ERROR,
                "Falha na importação",
                "Somente arquivos PDF podem ser importados.",
            )
            return

        try:

            results = self._execute_lifecycle_operation(
                "document-import",
                lambda: tuple(
                    self.session.document_import_service.import_file(path)
                    for path in files
                ),
            )

        except Exception as exc:
            self.documents_controller.refresh()
            if not self._publish_project_notification(
                NotificationLevel.ERROR,
                "Falha na importação",
                f"Não foi possível importar os documentos: {exc}",
            ):
                QMessageBox.critical(
                    self.window,
                    "Erro",
                    str(exc),
                )
            return

        self.documents_controller.refresh()
        self._refresh_dashboard()

        imported_count = sum(
            not item.is_duplicate for item in results
        )
        duplicate_count = len(results) - imported_count
        message = (
            "Documento importado."
            if imported_count == 1
            else f"{imported_count} documentos importados."
        )
        if duplicate_count:
            message += (
                f" {duplicate_count} arquivo(s) duplicado(s) "
                "já estava(m) registrado(s)."
            )
        self._publish_project_notification(
            NotificationLevel.SUCCESS,
            "Documentos",
            message,
        )

    def _update_document_metadata(
        self,
        document_identity,
        document_type,
    ):
        return self.session.document_metadata_service.update_document_type(
            document_identity,
            document_type,
        )

    def _confirm_unsaved_document_metadata(self):
        answer = QMessageBox.warning(
            self.window,
            "Alterações não salvas",
            "O documento possui alterações de metadados não salvas.",
            (
                QMessageBox.StandardButton.Save
                | QMessageBox.StandardButton.Discard
                | QMessageBox.StandardButton.Cancel
            ),
            QMessageBox.StandardButton.Cancel,
        )
        return {
            QMessageBox.StandardButton.Save: "save",
            QMessageBox.StandardButton.Discard: "discard",
        }.get(answer, "cancel")

    def _show_document_metadata_message(self, kind, message):
        levels = {
            "success": NotificationLevel.SUCCESS,
            "info": NotificationLevel.INFO,
            "error": NotificationLevel.ERROR,
        }
        self._publish_project_notification(
            levels.get(kind, NotificationLevel.INFO),
            "Documentos",
            message,
        )

    def _remove_document(self, document_identity) -> bool:
        document = self.session.document_repository.find_by_hash(
            document_identity
        )
        if document is None:
            self._publish_project_notification(
                NotificationLevel.ERROR,
                "Documentos",
                "Não foi possível localizar o documento selecionado.",
            )
            return False
        answer = QMessageBox.question(
            self.window,
            "Remover documento",
            f"Remover '{document.original_filename}' do acervo?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if answer != QMessageBox.StandardButton.Yes:
            self._publish_project_notification(
                NotificationLevel.INFO,
                "Documentos",
                "Remoção cancelada.",
            )
            return False
        try:
            removed = self.session.document_import_service.remove(document.id)
        except Exception as exc:
            self._publish_project_notification(
                NotificationLevel.ERROR,
                "Falha na remoção",
                f"Não foi possível remover o documento: {exc}",
            )
            return False
        if not removed:
            self._publish_project_notification(
                NotificationLevel.ERROR,
                "Falha na remoção",
                "Não foi possível remover o documento.",
            )
            return False
        self.window.selection_store.clear()
        self.documents_controller.refresh()
        self._refresh_dashboard()
        self._publish_project_notification(
            NotificationLevel.SUCCESS,
            "Documentos",
            "Documento removido.",
        )
        return True

    def _open_workspace_document(self, document_identity) -> bool:
        document = self.session.document_repository.find_by_hash(
            document_identity
        )
        if document is None:
            self._publish_project_notification(
                NotificationLevel.ERROR,
                "Documentos",
                "Não foi possível localizar o documento selecionado.",
            )
            return False
        try:
            self.window.show_document(
                self.state.current_project.project_path
                / document.relative_path
            )
        except Exception as exc:
            self._publish_project_notification(
                NotificationLevel.ERROR,
                "Falha ao abrir documento",
                f"Não foi possível abrir o documento: {exc}",
            )
            return False
        self._publish_project_notification(
            NotificationLevel.SUCCESS,
            "Documentos",
            "Documento aberto.",
        )
        return True

    def _process_workspace_document(self, document_identity) -> bool:
        document = self.session.document_repository.find_by_hash(
            document_identity
        )
        if document is None:
            self._publish_project_notification(
                NotificationLevel.ERROR,
                "Falha no OCR",
                "Não foi possível localizar o documento selecionado.",
            )
            return False
        self.selected_document = document
        self._publish_project_notification(
            NotificationLevel.INFO,
            "OCR",
            "OCR iniciado.",
        )
        self.process_document()
        self.documents_controller.refresh()
        if document.processing_status in (
            DocumentProcessingStatus.FAILED,
            DocumentProcessingStatus.CANCELLED,
        ):
            self._publish_project_notification(
                NotificationLevel.ERROR,
                "Falha no OCR",
                "Não foi possível concluir o OCR.",
            )
            return False
        self._publish_project_notification(
            NotificationLevel.SUCCESS,
            "OCR",
            "OCR concluído.",
        )
        return True

    # ------------------------------------------------------------------

    def _select_document(self, document):
        if not self.evidence_controller.can_leave():
            return
        self.selected_document = document

        if document is None:
            self.window.clear_document_properties()
            self.window.show_view("home")
            return

        self.window.set_document_properties(document)
        self.window.show_document(
            self.state.current_project.project_path
            / document.relative_path
        )

    # ------------------------------------------------------------------

    def show_search(self):
        """
        Exibe a pesquisa textual quando há um projeto aberto.
        """

        if not self.state.has_project:
            QMessageBox.information(
                self.window,
                "Nenhum projeto",
                "Abra um projeto antes de pesquisar documentos.",
            )
            return

        if not self.evidence_controller.can_leave():
            return

        self.window.show_search()

    def show_documents(self):
        if not self.state.has_project:
            QMessageBox.information(
                self.window, "Nenhum projeto",
                "Abra um projeto antes de consultar documentos.",
            )
            return
        if not self.evidence_controller.can_leave():
            return
        self.documents_controller.refresh()
        self.window.show_documents()

    def _navigate_from_search(self, request) -> bool:
        return self._navigate_to_documents(request)

    def _navigate_from_evidence(self, request) -> bool:
        return self._navigate_to_documents(request)

    def _navigate_to_documents(self, request) -> bool:
        if not self.state.has_project:
            return False
        if not self.evidence_controller.can_leave():
            return False
        if not self.documents_controller.refresh():
            self._show_evidence_message(
                "error",
                "Falha ao abrir o documento.",
            )
            return False
        self.window.show_documents()
        if not self.documents_controller.navigate(request):
            self._show_evidence_message(
                "error",
                "Falha ao abrir o documento.",
            )
            return False
        outcome = getattr(
            self.documents_controller,
            "last_navigation_outcome",
            None,
        )
        if outcome == getattr(
            self.documents_controller,
            "NAVIGATION_PAGE_MISSING",
            "page_missing",
        ):
            self._show_evidence_message(
                "warning",
                "Página inexistente. Documento aberto.",
            )
        else:
            self._show_evidence_message(
                "success",
                "Documento aberto.",
            )
        return True

    def show_evidences(self):
        if not self.state.has_project:
            QMessageBox.information(
                self.window, "Nenhum projeto",
                "Abra um projeto antes de gerenciar evidências.",
            )
            return
        self.evidence_controller.load()
        self.window.show_evidences()

    def show_activities(self):
        if not self.state.has_project:
            QMessageBox.information(
                self.window,
                "Nenhum projeto",
                "Abra um projeto RSC antes de consultar atividades.",
            )
            return
        if getattr(self.session, "rsc_session", None) is None:
            QMessageBox.information(
                self.window,
                "Atividades indisponíveis",
                "O projeto atual não utiliza o módulo RSC.",
            )
            return
        if not self.evidence_controller.can_leave():
            return
        self.activities_controller.refresh()
        self.window.show_activities()

    def _show_activity_message(self, kind, message):
        levels = {
            "success": NotificationLevel.SUCCESS,
            "info": NotificationLevel.INFO,
            "warning": NotificationLevel.WARNING,
            "error": NotificationLevel.ERROR,
        }
        self._publish_project_notification(
            levels.get(kind, NotificationLevel.INFO),
            "Activities",
            message,
        )

    def _show_functional_assignment_message(self, kind, message):
        levels = {
            "success": NotificationLevel.SUCCESS,
            "info": NotificationLevel.INFO,
            "error": NotificationLevel.ERROR,
        }
        self._publish_project_notification(
            levels.get(kind, NotificationLevel.INFO),
            "Interpretação funcional",
            message,
        )
        self.window.functional_assignments_view.show_message(message)

    def _confirm_delete_functional_assignment(self, assignment):
        return QMessageBox.question(
            self.window,
            "Excluir interpretação funcional",
            f"Excluir a interpretação de '{assignment.role}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        ) == QMessageBox.StandardButton.Yes

    def _show_functional_exercise_message(self, kind, message):
        levels = {
            "success": NotificationLevel.SUCCESS,
            "info": NotificationLevel.INFO,
            "error": NotificationLevel.ERROR,
        }
        self._publish_project_notification(
            levels.get(kind, NotificationLevel.INFO),
            "Exercícios funcionais",
            message,
        )
        self.window.functional_exercises_view.show_message(message)

    def _confirm_delete_functional_exercise(self, exercise):
        return QMessageBox.question(
            self.window,
            "Excluir exercício funcional",
            f"Excluir o exercício '{exercise.role}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        ) == QMessageBox.StandardButton.Yes

    def _confirm_delete_activity(self, activity):
        return QMessageBox.question(
            self.window,
            "Excluir Activity",
            f"Excluir '{activity.description}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        ) == QMessageBox.StandardButton.Yes

    def _confirm_unsaved_activity(self):
        answer = QMessageBox.warning(
            self.window,
            "Alterações não salvas",
            "A Activity possui alterações não salvas.",
            (
                QMessageBox.StandardButton.Save
                | QMessageBox.StandardButton.Discard
                | QMessageBox.StandardButton.Cancel
            ),
            QMessageBox.StandardButton.Cancel,
        )
        return {
            QMessageBox.StandardButton.Save: "save",
            QMessageBox.StandardButton.Discard: "discard",
        }.get(answer, "cancel")

    def show_functional_assignments(self):
        if (
            not self.state.has_project
            or getattr(self.session, "rsc_session", None) is None
        ):
            return
        self.functional_assignments_controller.refresh()
        self.window.show_functional_assignments()

    def show_functional_exercises(self):
        if (
            not self.state.has_project
            or getattr(self.session, "rsc_session", None) is None
        ):
            return
        self.functional_exercises_controller.refresh()
        self.window.show_functional_exercises()

    def create_functional_exercise(self):
        identifiers = (
            self.window.functional_assignments_view
            .selected_assignment_ids()
        )
        if not self.functional_exercises_controller.create(identifiers):
            return False
        self.window.show_functional_exercises()
        self._refresh_dashboard()
        return True

    def create_activity(self):
        identifiers = (
            self.window.functional_exercises_view.selected_exercise_ids()
        )
        if not self.activities_controller.create(identifiers):
            return False
        self.window.show_activities()
        self._refresh_dashboard()
        return True

    def create_activity_from_assignments(self):
        identifiers = (
            self.window.functional_assignments_view
            .selected_assignment_ids()
        )
        if not self.activities_controller.create(
            assignment_ids=identifiers
        ):
            return False
        self.window.show_activities()
        self._refresh_dashboard()
        return True

    def _navigate_to_functional_assignment(self, assignment_id):
        self.window.show_functional_assignments()
        if not self.functional_assignments_controller.select(assignment_id):
            return False
        return True

    def _navigate_to_functional_exercise(self, exercise_id):
        if not self.functional_exercises_controller.select(exercise_id):
            return False
        self.window.show_functional_exercises()
        return True

    def interpret_selected_evidence(self):
        evidence = self.evidence_controller.selected_evidence
        if evidence is None:
            return False
        if not self.functional_assignments_controller.create_from_evidence(
            evidence
        ):
            return False
        selected = self.functional_assignments_controller._selected
        self.window.show_functional_assignments()
        if selected is not None:
            self.functional_assignments_controller.select(selected)
        self._refresh_dashboard()
        return True

    def _navigate_to_evidence(self, evidence_id):
        if not self.evidence_controller.load():
            return False
        self.window.show_evidences()
        if not self.evidence_controller.select(evidence_id):
            return False
        return True

    def new_evidence(self):
        if not self.state.has_project:
            self.show_evidences()
            return
        if not self.evidence_controller.start_create():
            return
        self.window.show_evidences()

    def _create_evidence_from_search(self, candidate):
        if not self.state.has_project:
            self.window.search_workspace.show_message(
                "Abra um projeto antes de criar uma evidência."
            )
            return False
        if not self.evidence_controller.start_create_from_source(candidate):
            return False
        self.window.show_evidences()
        return True

    def _create_evidence_from_documents(self, candidate):
        if not self.state.has_project:
            self.window.documents_workspace.show_message(
                "Abra um projeto antes de criar uma evidência."
            )
            return False
        if not self.evidence_controller.start_create_from_source(candidate):
            return False
        self.window.show_evidences()
        return True

    def close_project(self):
        if not self.state.has_project:
            self.contribution_installer.clear()
            return
        if not getattr(
            self.documents_controller,
            "can_leave_metadata",
            lambda: True,
        )():
            return
        if not getattr(
            getattr(self, "activities_controller", None),
            "can_leave",
            lambda: True,
        )():
            return
        if not self.evidence_controller.can_leave():
            return

        try:
            self._execute_lifecycle_operation(
                "project-close",
                self._close_active_project,
            )
        except Exception as exc:
            published = self._publish_project_notification(
                NotificationLevel.ERROR,
                "Erro ao fechar",
                f"Não foi possível fechar o projeto: {exc}",
            )
            if not published:
                raise
            return
        self._complete_project_close()

    def _close_active_project(self):
        active = self.lifecycle_host.current_session
        self.contribution_installer.clear()
        def publish(_previous):
            self._unbind_session()
            if self._close_session_consumers is not None:
                self._close_session_consumers()

        def rollback(previous):
            self._bind_session(previous)
            self._restore_contributions(previous)

        try:
            self.lifecycle_host.close_session(
                after_publish=publish,
                rollback=rollback,
            )
        except Exception:
            if active is not None and self.lifecycle_host.current_session is active:
                self._restore_contributions(active)
            raise
        evidence_workspace = getattr(
            self.window, "evidence_workspace", None
        )
        if evidence_workspace is not None:
            evidence_workspace.set_functional_interpretation_available(False)
        assignments_action = getattr(
            self.window, "action_functional_assignments", None
        )
        if assignments_action is not None:
            assignments_action.setVisible(False)
            assignments_action.setEnabled(False)
        exercises_action = getattr(
            self.window, "action_functional_exercises", None
        )
        if exercises_action is not None:
            exercises_action.setVisible(False)
            exercises_action.setEnabled(False)


    def _confirm_unsaved_evidence(self):
        answer = QMessageBox.warning(
            self.window, "Alterações não salvas",
            "Deseja salvar as alterações da evidência?",
            QMessageBox.StandardButton.Save
            | QMessageBox.StandardButton.Discard
            | QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Save,
        )
        return {
            QMessageBox.StandardButton.Save: "save",
            QMessageBox.StandardButton.Discard: "discard",
        }.get(answer, "cancel")

    def _confirm_delete_evidence(self, evidence):
        return QMessageBox.question(
            self.window, "Excluir evidência",
            f"Deseja excluir a evidência '{evidence.title}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        ) == QMessageBox.StandardButton.Yes

    def _confirm_duplicate_evidence(self, evidences):
        details = "\n".join(
            f"• {item.title} — página {item.page_number or '-'} — "
            f"{item.document_identity[:12]}…"
            for item in evidences
        )
        return QMessageBox.question(
            self.window, "Possível duplicidade",
            "Foram encontradas evidências semelhantes:\n\n"
            f"{details}\n\nDeseja criar mesmo assim?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        ) == QMessageBox.StandardButton.Yes

    def _show_evidence_message(self, kind, message):
        self.window.evidence_workspace.show_message(message)
        levels = {
            "success": NotificationLevel.SUCCESS,
            "info": NotificationLevel.INFO,
            "error": NotificationLevel.ERROR,
        }
        self._publish_project_notification(
            levels.get(kind, NotificationLevel.INFO),
            "Evidence",
            message,
        )
        if kind == "success":
            self._refresh_dashboard()

    # ------------------------------------------------------------------

    def process_document(self):
        if self.selected_document is None:
            return

        document = self.selected_document
        selected_path = document.relative_path
        selected_page = self.window.pdf_view.current_page()
        if document.processing_status == DocumentProcessingStatus.PROCESSING:
            QMessageBox.information(
                self.window,
                "Documento em processamento",
                "O documento já está sendo processado.",
            )
            return

        try:
            result = self._process_document(document)

        except Exception as exc:
            error_message = self._record_processing_failure(
                document,
                exc,
            )
            self._refresh_dashboard()

            QMessageBox.critical(
                self.window,
                "Erro",
                f"Não foi possível processar o documento.\n\n{error_message}",
            )
            return

        self._refresh_processed_document(
            selected_path,
            selected_page,
        )
        self._refresh_dashboard()

        if document.processing_status == DocumentProcessingStatus.PROCESSED:
            message = "O texto nativo do documento foi processado."
        elif document.processing_status == DocumentProcessingStatus.OCR_REQUIRED:
            message = "Documento sem texto pesquisável. OCR necessário."
        else:
            message = "Não foi possível processar o documento."
            if result.error:
                message += f"\n\n{result.error}"

        QMessageBox.information(
            self.window,
            "Processamento concluído",
            message,
        )

    # ------------------------------------------------------------------

    def process_pending_documents(self):
        """
        Processa sequencialmente os documentos sem resultado válido.
        """

        if not self.state.has_project:
            QMessageBox.information(
                self.window,
                "Nenhum projeto",
                "Abra um projeto antes de processar documentos.",
            )
            return

        documents, skipped, ocr_required = self._find_pending_documents()

        if not documents:
            message = "Todos os documentos já possuem um resultado válido."

            if ocr_required:
                message += (
                    f"\n\n{ocr_required} documento(s) sem texto "
                    "pesquisável requer(em) OCR."
                )

            QMessageBox.information(
                self.window,
                "Nenhum documento pendente",
                message,
            )
            return

        documents = self._confirm_batch_limit(documents)

        if not documents:
            return

        self._process_batch(documents, skipped, ocr_required)
        self._refresh_project_view()

    # ------------------------------------------------------------------

    def _find_pending_documents(self):
        """
        Separa documentos reutilizáveis dos que exigem processamento.
        """

        pending_documents = []
        skipped = 0
        ocr_required = 0
        changed = False

        for document in self.session.document_repository.list_documents():
            try:
                result = self.document_processor.get_valid_result(
                    self.state.current_project,
                    document,
                )
            except Exception:
                pending_documents.append(document)
                continue

            if result is None:
                pending_documents.append(document)
                continue

            changed = self._apply_processing_result(document, result) or changed
            if result.status == "ocr_required":
                ocr_required += 1
            else:
                skipped += 1

        if changed:
            self.session.document_repository.save()

        return pending_documents, skipped, ocr_required

    # ------------------------------------------------------------------

    def _confirm_batch_limit(self, documents):
        """
        Limita a operação e solicita confirmação para o primeiro lote.
        """

        if len(documents) <= self.batch_limit:
            return documents

        answer = QMessageBox.question(
            self.window,
            "Limite de processamento",
            f"Há {len(documents)} documentos pendentes. "
            f"Será processado apenas o primeiro lote de "
            f"{self.batch_limit} documentos. Deseja continuar?",
            QMessageBox.StandardButton.Yes
            | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.Yes,
        )

        if answer != QMessageBox.StandardButton.Yes:
            return []

        return documents[:self.batch_limit]

    # ------------------------------------------------------------------

    def _process_batch(
        self,
        documents,
        skipped: int,
        ocr_required: int,
    ):
        """
        Executa um lote sequencial e tolerante a falhas individuais.
        """

        dialog = self.window.create_processing_progress(len(documents))
        completed = 0
        failed = 0
        cancelled = 0
        dialog.show()
        QApplication.processEvents()

        for index, document in enumerate(documents):
            if dialog.wasCanceled():
                cancelled = len(documents[index:])
                self._mark_batch_as_cancelled(documents[index:])
                break

            position = index + 1
            self.window.update_processing_progress(
                dialog,
                document,
                position,
                len(documents),
                completed,
                ocr_required,
                failed,
                skipped,
            )
            QApplication.processEvents()

            try:
                self._process_document(document)
            except Exception as exc:
                self._record_processing_failure(document, exc)
                failed += 1
            else:
                if (
                    document.processing_status
                    == DocumentProcessingStatus.PROCESSED
                ):
                    completed += 1
                elif (
                    document.processing_status
                    == DocumentProcessingStatus.OCR_REQUIRED
                ):
                    ocr_required += 1
                else:
                    failed += 1

            dialog.setValue(position)
            QApplication.processEvents()

        dialog.close()

        QMessageBox.information(
            self.window,
            "Processamento em lote concluído",
            f"Concluídos: {completed}\n"
            f"OCR necessário: {ocr_required}\n"
            f"Falhas: {failed}\n"
            f"Ignorados: {skipped}\n"
            f"Cancelados: {cancelled}",
        )

    # ------------------------------------------------------------------

    def _process_document(self, document):
        """
        Processa e persiste o estado de um único documento.
        """

        document.processing_status = DocumentProcessingStatus.PENDING
        self.session.document_repository.update(document)
        self.session.document_repository.save()

        document.processing_status = DocumentProcessingStatus.PROCESSING
        self.session.document_repository.update(document)
        self.session.document_repository.save()

        result = self.document_processor.process(
            self.state.current_project,
            document,
        )

        self._apply_processing_result(document, result)
        self.session.document_repository.update(document)
        self.session.document_repository.save()
        return result

    # ------------------------------------------------------------------

    @staticmethod
    def _apply_processing_result(document, result) -> bool:
        """
        Copia o resultado para os metadados persistidos do documento.
        """

        values = (
            ("sha256", result.document_sha256),
            ("processed_at", result.processed_at),
            ("processing_status", result.status),
        )
        changed = False

        for attribute, value in values:
            if getattr(document, attribute) != value:
                setattr(document, attribute, value)
                changed = True

        return changed

    # ------------------------------------------------------------------

    def _record_processing_failure(self, document, exc) -> str:
        """
        Registra uma falha inesperada sem interromper o lote.
        """

        document.processed_at = document.now()
        document.processing_status = DocumentProcessingStatus.FAILED
        error_message = str(exc)

        try:
            self.session.document_repository.update(document)
            self.session.document_repository.save()
        except Exception as save_exc:
            error_message = (
                f"{error_message}\n\n"
                "Também não foi possível registrar a falha: "
                f"{save_exc}"
            )

        return error_message

    # ------------------------------------------------------------------

    def _mark_batch_as_cancelled(self, documents) -> None:
        """
        Mantém os documentos não iniciados elegíveis para novo lote.
        """

        for document in documents:
            document.processing_status = DocumentProcessingStatus.CANCELLED
            self.session.document_repository.update(document)

        self.session.document_repository.save()

    # ------------------------------------------------------------------

    def _refresh_project_view(self) -> None:
        """
        Atualiza a lista e preserva o documento selecionado, quando houver.
        """

        self.window.set_project(
            self.state.current_project,
            self.session.document_repository.list_documents(),
        )
        self._refresh_dashboard()
        if self.selected_document is None:
            return

        self.window.set_document_properties(self.selected_document)
        self.window.show_document(
            self.state.current_project.project_path
            / self.selected_document.relative_path
        )

    # ------------------------------------------------------------------

    def _refresh_processed_document(
        self,
        relative_path: str,
        page: int,
    ) -> None:
        """
        Atualiza o documento processado sem recarregar a interface do projeto.
        """

        document = next(
            (
                item
                for item in self.session.document_repository
                if item.relative_path == relative_path
            ),
            None,
        )

        if document is None:
            return

        self.selected_document = document
        self.window.set_document_properties(document)
        self.window.show_view("pdf")

        if page > 0 and self.window.pdf_view.current_page() != page:
            self.window.pdf_view.show_page(page)

    def _refresh_dashboard(self) -> bool:
        dashboard_controller = getattr(
            self, "dashboard_controller", None
        )
        if dashboard_controller is None:
            return False
        return dashboard_controller.refresh()
