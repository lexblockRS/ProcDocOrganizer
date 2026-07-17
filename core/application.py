"""
Aplicação principal do ProcDocOrganizer.
"""

import sys

from PySide6.QtWidgets import QApplication

from core.project_controller import ProjectController
from core.project_manager import ProjectManager
from core.project_state import ProjectState
from ui.main_window import MainWindow


class Application:
    """
    Classe responsável por inicializar a aplicação.
    """

    def __init__(self):

        self.app = QApplication(sys.argv)

        self.app.setApplicationName("ProcDocOrganizer")
        self.app.setOrganizationName("ProcDocOrganizer")
        self.app.setApplicationVersion("1.0")

        self._create_components()

    # ------------------------------------------------------------------

    def _create_components(self):
        """
        Cria e conecta todos os componentes principais da aplicação.
        """

        # Interface
        self.main_window = MainWindow()

        # Estado da aplicação
        self.project_state = ProjectState()

        # Serviços
        self.project_manager = ProjectManager()

        # Controladores
        self.project_controller = ProjectController(
            window=self.main_window,
            manager=self.project_manager,
            state=self.project_state,
        )

    # ------------------------------------------------------------------

    def run(self):
        """
        Executa a aplicação.
        """

        self.main_window.show()

        return self.app.exec()