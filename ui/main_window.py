"""
Janela principal do ProcDocOrganizer.
"""

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QLabel,
    QDockWidget,
    QMainWindow,
    QMenu,
    QProgressDialog,
    QSplitter,
    QStackedWidget,
    QStatusBar,
    QToolBar,
)

from models import Document, Project
from ui.views import (
    DocumentsWorkspace, EvidenceWorkspace, HomeView, PdfView, SearchWorkspace,
)
from ui.widgets import ProjectTreeWidget


class MainWindow(QMainWindow):
    """
    Janela principal da aplicação.
    """

    def __init__(self):
        super().__init__()

        self.setWindowTitle("ProcDocOrganizer")
        self.resize(1400, 900)

        self.project = None
        self.views = {}
        self._base_menus_by_id: dict[str, QMenu] = {}
        self._application_menus_by_id: dict[str, QMenu] = {}

        self._create_actions()
        self._create_menu()
        self._create_toolbar()
        self._create_central_area()
        self._create_right_dock()
        self._create_statusbar()

    # ------------------------------------------------------------------

    def _create_actions(self):

        self.action_new_project = QAction("Novo Projeto...", self)
        self.action_open_project = QAction("Abrir Projeto...", self)
        self.action_close_project = QAction("Fechar Projeto", self)
        self.action_exit = QAction("Sair", self)

        self.action_preferences = QAction("Preferências", self)

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

        toolbar.setMovable(False)

        toolbar.addAction(self.action_new_project)
        toolbar.addAction(self.action_open_project)

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

        self.addToolBar(toolbar)

    # ------------------------------------------------------------------

    def _create_central_area(self):

        self.stack = QStackedWidget()

        home_view = HomeView()
        pdf_view = PdfView()
        search_workspace = SearchWorkspace()
        evidence_workspace = EvidenceWorkspace()
        documents_workspace = DocumentsWorkspace()

        self.views["home"] = home_view
        self.views["pdf"] = pdf_view
        self.views["search"] = search_workspace
        self.views["evidence"] = evidence_workspace
        self.views["documents"] = documents_workspace
        self.pdf_view = pdf_view
        self.search_workspace = search_workspace
        self.evidence_workspace = evidence_workspace
        self.documents_workspace = documents_workspace

        self.stack.addWidget(home_view)
        self.stack.addWidget(pdf_view)
        self.stack.addWidget(search_workspace)
        self.stack.addWidget(evidence_workspace)
        self.stack.addWidget(documents_workspace)

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

        dock.setWidget(
            self.properties_label
        )

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

    # ------------------------------------------------------------------

    def show_view(
        self,
        name: str,
    ):
        """
        Exibe uma view registrada.
        """

        view = self.views.get(name)

        if view is not None:
            self.stack.setCurrentWidget(view)

    # ------------------------------------------------------------------

    def set_project(
        self,
        project: Project,
        documents: list[Document] | None = None,
    ):
        """
        Atualiza toda a interface para um projeto aberto.
        """

        self.project = project
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
        self.show_view("home")

        for view in self.views.values():
            callback = getattr(view, "on_project_opened", None)
            if callback is not None:
                callback(project)

    # ------------------------------------------------------------------

    def clear_project(self):
        """
        Limpa toda a interface.
        """

        self.project = None
        self.action_evidence_workspace.setEnabled(False)
        self.action_new_evidence.setEnabled(False)
        self.action_documents_workspace.setEnabled(False)

        self.project_tree.clear_project()

        self.status_message.setText(
            "Nenhum projeto aberto"
        )

        self.clear_document_properties()
        self.search_workspace.clear()
        self.pdf_view.clear_document()
        self.show_view("home")

        for view in self.views.values():
            if view is self.evidence_workspace:
                continue
            callback = getattr(view, "on_project_closed", None)
            if callback is not None:
                callback()

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
            event.accept()
        else:
            event.ignore()

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
