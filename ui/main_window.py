"""
Janela principal do ProcDocOrganizer.
"""

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QLabel,
    QDockWidget,
    QMainWindow,
    QStackedWidget,
    QStatusBar,
    QToolBar,
)

from models.project import Project
from ui.views import HomeView
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

        self._create_actions()
        self._create_menu()
        self._create_toolbar()
        self._create_central_area()
        self._create_left_dock()
        self._create_right_dock()
        self._create_statusbar()

    # ------------------------------------------------------------------

    def _create_actions(self):

        self.action_new_project = QAction("Novo Projeto...", self)
        self.action_open_project = QAction("Abrir Projeto...", self)
        self.action_close_project = QAction("Fechar Projeto", self)
        self.action_exit = QAction("Sair", self)

        self.action_preferences = QAction("Preferências", self)

        self.action_import_files = QAction("Importar Arquivos", self)
        self.action_new_evidence = QAction("Nova Evidência", self)

        self.action_recalculate = QAction("Recalcular Pontuação", self)

        self.action_about = QAction("Sobre", self)

    # ------------------------------------------------------------------

    def _create_menu(self):

        menu = self.menuBar()

        file_menu = menu.addMenu("Arquivo")

        file_menu.addAction(self.action_new_project)
        file_menu.addAction(self.action_open_project)

        file_menu.addSeparator()

        file_menu.addAction(self.action_close_project)

        file_menu.addSeparator()

        file_menu.addAction(self.action_exit)

        edit_menu = menu.addMenu("Editar")
        edit_menu.addAction(self.action_preferences)

        evidence_menu = menu.addMenu("Evidências")
        evidence_menu.addAction(self.action_import_files)
        evidence_menu.addAction(self.action_new_evidence)

        classification_menu = menu.addMenu("Classificação")
        classification_menu.addAction(self.action_recalculate)

        menu.addMenu("Ferramentas")

        help_menu = menu.addMenu("Ajuda")
        help_menu.addAction(self.action_about)

    # ------------------------------------------------------------------

    def _create_toolbar(self):

        toolbar = QToolBar("Principal")
        toolbar.setMovable(False)

        toolbar.addAction(self.action_new_project)
        toolbar.addAction(self.action_open_project)

        toolbar.addSeparator()

        toolbar.addAction(self.action_import_files)

        self.addToolBar(toolbar)

    # ------------------------------------------------------------------

    def _create_central_area(self):

        self.stack = QStackedWidget()

        home_view = HomeView()

        self.views["home"] = home_view

        self.stack.addWidget(home_view)

        self.setCentralWidget(self.stack)

    # ------------------------------------------------------------------

    def _create_left_dock(self):

        self.project_tree = ProjectTreeWidget()

        dock = QDockWidget("Projeto", self)

        dock.setAllowedAreas(
            Qt.LeftDockWidgetArea |
            Qt.RightDockWidgetArea
        )

        dock.setWidget(self.project_tree)

        self.addDockWidget(Qt.LeftDockWidgetArea, dock)

    # ------------------------------------------------------------------

    def _create_right_dock(self):

        self.properties_label = QLabel(
            "Nenhum item selecionado",
            alignment=Qt.AlignmentFlag.AlignTop,
        )

        dock = QDockWidget("Propriedades", self)

        dock.setAllowedAreas(
            Qt.LeftDockWidgetArea |
            Qt.RightDockWidgetArea
        )

        dock.setWidget(self.properties_label)

        self.addDockWidget(Qt.RightDockWidgetArea, dock)

    # ------------------------------------------------------------------

    def _create_statusbar(self):

        status = QStatusBar()

        self.status_message = QLabel("Nenhum projeto aberto")
        self.version_label = QLabel("v1.0")

        status.addWidget(self.status_message)
        status.addPermanentWidget(self.version_label)

        self.setStatusBar(status)

    # ------------------------------------------------------------------

    def show_view(self, name: str):
        """
        Exibe uma view registrada.
        """

        view = self.views.get(name)

        if view is not None:
            self.stack.setCurrentWidget(view)

    # ------------------------------------------------------------------

    def set_project(self, project: Project):
        """
        Atualiza toda a interface para um projeto aberto.
        """

        self.project = project

        self.project_tree.load_project(project)

        self.status_message.setText(
            f"Projeto: {project.project_name}"
        )

        for view in self.views.values():
            view.on_project_opened(project)

    # ------------------------------------------------------------------

    def clear_project(self):
        """
        Limpa toda a interface.
        """

        self.project = None

        self.project_tree.clear_project()

        self.status_message.setText(
            "Nenhum projeto aberto"
        )

        for view in self.views.values():
            view.on_project_closed()