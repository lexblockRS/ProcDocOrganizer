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

from models import DocumentProcessingStatus
from services.processing import DocumentProcessor

from .project_session_factory import ProjectSessionFactory
from .application_lifecycle_host import ApplicationLifecycleHost


_APPLICATION_LIFECYCLE_HOST = ApplicationLifecycleHost()


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
    ):
        self.window = window
        self.manager = manager
        self.state = state
        self.batch_limit = max(1, batch_limit)
        self.session_factory = session_factory or ProjectSessionFactory()
        self.application_registry = application_registry
        self.contribution_installer = contribution_installer

        self.session = None
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
        )
        self.functional_assignments_controller = (
            FunctionalAssignmentsController(
                self.window.views["functional_assignments"],
                parent=self.window,
                evidence_navigation_requested=self._navigate_to_evidence,
            )
        )
        self.functional_exercises_controller = FunctionalExercisesController(
            self.window.views["functional_exercises"],
            parent=self.window,
            assignment_navigation_requested=(
                self._navigate_to_functional_assignment
            ),
        )
        self.search_controller = SearchController(
            self.window.search_workspace,
            document_navigation_requested=self._navigate_from_search,
        )
        self.documents_controller = DocumentsController(
            self.window.documents_workspace,
            evidence_source_requested=self._create_evidence_from_documents,
            document_remove_requested=self._remove_document,
        )
        self.evidence_controller = EvidenceController(
            self.window.evidence_workspace,
            confirm_unsaved=self._confirm_unsaved_evidence,
            confirm_delete=self._confirm_delete_evidence,
            confirm_duplicates=self._confirm_duplicate_evidence,
            notify=self._show_evidence_message,
            document_navigation_requested=self._navigate_from_evidence,
        )
        self.search_controller.set_evidence_source_requested(
            self._create_evidence_from_search
        )
        self.window.set_close_guard(self.evidence_controller.can_leave)

        self._connect_signals()

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

        previous_session = self.session
        session = self.session_factory.create(project)
        application = getattr(session, "application", None)
        contributions = (
            application.contributions()
            if application is not None
            else ()
        )

        if self.session is None:
            self.contribution_installer.install(contributions)
        else:
            self.contribution_installer.replace(contributions)

        self.session = session
        self.document_processor = getattr(
            session,
            "document_processor",
            getattr(self, "document_processor", None),
        )
        self.state.open_project(project)
        self.selected_document = None
        self.search_controller.set_search_service(session.search_service)
        self.evidence_controller.set_service(session.evidence_service)

        self.window.set_project(
            project,
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
        _APPLICATION_LIFECYCLE_HOST.activate_session(session)
        if previous_session is not None:
            _APPLICATION_LIFECYCLE_HOST.dispose_session(previous_session)

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

            project = self.manager.create_project(
                dialog.get_project_name(),
                dialog.get_project_folder(),
                application_id=dialog.get_application_id(),
            )
            self._load_project(project)

        except FileExistsError as exc:

            QMessageBox.warning(
                self.window,
                "Projeto já existe",
                str(exc),
            )

            return

        except Exception as exc:

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

            project = self.manager.open_project(
                Path(folder)
            )
            self._load_project(project)

        except FileNotFoundError as exc:

            QMessageBox.warning(
                self.window,
                "Projeto inválido",
                str(exc),
            )

            return

        except Exception as exc:

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

        files, _ = QFileDialog.getOpenFileNames(
            self.window,
            "Importar Documentos",
            "",
            "Arquivos PDF (*.pdf);;Todos os Arquivos (*)",
        )

        if not files:
            return

        try:
            results = tuple(
                self.session.document_import_service.import_file(path)
                for path in files
            )

        except Exception as exc:
            QMessageBox.critical(
                self.window,
                "Erro",
                str(exc),
            )

            return

        self.window.set_project(
            self.state.current_project,
            self.session.document_repository.list_documents(),
        )
        self._refresh_dashboard()

        stored_only = sum(
            not self.document_processor.parser_registry.supports(
                self.state.current_project.project_path
                / item.document.relative_path
            )
            for item in results
        )
        format_message = (
            f"\n{stored_only} arquivo(s) foi/foram armazenado(s), "
            "mas o processamento textual atual aceita somente PDF."
            if stored_only
            else ""
        )
        QMessageBox.information(
            self.window,
            "Importação concluída",
            f"{sum(not item.is_duplicate for item in results)} "
            "documento(s) importado(s); "
            f"{sum(item.is_duplicate for item in results)} duplicado(s)."
            + format_message,
        )

    def _remove_document(self, document_identity) -> bool:
        document = self.session.document_repository.find_by_hash(
            document_identity
        )
        if document is None:
            return False
        answer = QMessageBox.question(
            self.window,
            "Remover documento",
            f"Remover '{document.original_filename}' do acervo?",
        )
        if answer != QMessageBox.StandardButton.Yes:
            return False
        if not self.session.document_import_service.remove(document.id):
            return False
        self.documents_controller.refresh()
        self.window.set_project(
            self.state.current_project,
            self.session.document_repository.list_documents(),
        )
        self.window.show_documents()
        self._refresh_dashboard()
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
            return False
        if not self.documents_controller.navigate(request):
            return False
        self.window.show_documents()
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
        if not self.functional_assignments_controller.select(assignment_id):
            return False
        self.window.show_functional_assignments()
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
        self.window.show_functional_assignments()
        self._refresh_dashboard()
        return True

    def _navigate_to_evidence(self, evidence_id):
        if not self.evidence_controller.load():
            return False
        if not self.evidence_controller.select(evidence_id):
            return False
        self.window.show_evidences()
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
            _APPLICATION_LIFECYCLE_HOST.dispose_session(self.session)
            self.session = None
            return
        if not self.evidence_controller.can_leave():
            return
        self.contribution_installer.clear()
        _APPLICATION_LIFECYCLE_HOST.dispose_session(self.session)
        self.evidence_controller.set_service(None)
        self.documents_controller.set_service(None)
        self.search_controller.set_search_service(None)
        self.session = None
        self.selected_document = None
        self.state.close_project()
        self.window.clear_project()
        dashboard_controller = getattr(
            self, "dashboard_controller", None
        )
        if dashboard_controller is not None:
            dashboard_controller.clear_session()
        activities_controller = getattr(
            self, "activities_controller", None
        )
        if activities_controller is not None:
            activities_controller.clear_session()
        functional_controller = getattr(
            self, "functional_assignments_controller", None
        )
        if functional_controller is not None:
            functional_controller.clear_session()
        exercise_controller = getattr(
            self, "functional_exercises_controller", None
        )
        if exercise_controller is not None:
            exercise_controller.clear_session()
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
        if kind == "success":
            self._refresh_dashboard()
        if kind == "error":
            QMessageBox.warning(self.window, "Evidências", message)

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
