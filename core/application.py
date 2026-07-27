"""
Aplicação principal do ProcDocOrganizer.
"""

import sys

from PySide6.QtWidgets import QApplication

from core.application_registry import ApplicationRegistry
from core.contribution_manager import ContributionManager
from core.project_controller import ProjectController
from core.project_manager import ProjectManager
from core.project_session_factory import ProjectSessionFactory
from core.project_state import ProjectState
from ui.contribution_installer import DesktopContributionInstaller
from platform_sdk import ApplicationCatalog
from ui.platform_main_window import PlatformMainWindow


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

        catalog = ApplicationCatalog.discover()
        contribution_manager = ContributionManager()
        contribution_manager.register_many(catalog.contributions)

        # Interface
        self.main_window = PlatformMainWindow(contribution_manager)

        # Estado da aplicação
        self.project_state = ProjectState()

        # Serviços
        self.project_manager = ProjectManager()
        self.application_registry = ApplicationRegistry(
            catalog.applications
        )
        self.project_session_factory = ProjectSessionFactory(
            self.application_registry
        )
        self.contribution_installer = DesktopContributionInstaller(
            self.main_window
        )

        # Controladores
        self.project_controller = ProjectController(
            window=self.main_window,
            manager=self.project_manager,
            state=self.project_state,
            session_factory=self.project_session_factory,
            application_registry=self.application_registry,
            contribution_installer=self.contribution_installer,
        )
        self.main_window.home_view.retry_requested.connect(
            self.project_controller.dashboard_controller.refresh
        )

    # ------------------------------------------------------------------

    def run(self):
        """
        Executa a aplicação.
        """

        self.main_window.show()

        return self.app.exec()
