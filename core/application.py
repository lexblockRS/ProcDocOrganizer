"""
Aplicação principal do ProcDocOrganizer.
"""

import sys
import logging
from pathlib import Path

from PySide6.QtWidgets import QApplication

from core.application_registry import ApplicationRegistry
from core.contribution_manager import ContributionManager
from core.project_controller import ProjectController
from core.project_manager import ProjectManager
from core.project_session_factory import ProjectSessionFactory
from core.project_state import ProjectState
from core.application_lifecycle_host import ApplicationLifecycleHost
from core.version import (
    APPLICATION_DISPLAY_NAME,
    APPLICATION_NAME,
    TECHNICAL_VERSION,
)
from ui.contribution_installer import DesktopContributionInstaller
from platform_sdk import ApplicationCatalog
from ui.platform_main_window import PlatformMainWindow
from ui.project_explorer import ProjectExplorerWindow


class Application:
    """
    Classe responsável por inicializar a aplicação.
    """

    def __init__(
        self,
        *,
        productive_database_path: str | Path | None = None,
        productive_workspace_base: str | Path | None = None,
    ):

        self.app = QApplication.instance() or QApplication(sys.argv)

        self.app.setApplicationName(APPLICATION_NAME)
        self.app.setApplicationDisplayName(APPLICATION_DISPLAY_NAME)
        self.app.setOrganizationName("ProcDocOrganizer")
        self.app.setApplicationVersion(TECHNICAL_VERSION)

        self._create_components(
            productive_database_path=productive_database_path,
            productive_workspace_base=productive_workspace_base,
        )

    # ------------------------------------------------------------------

    def _create_components(
        self,
        *,
        productive_database_path: str | Path | None,
        productive_workspace_base: str | Path | None,
    ):
        """
        Cria e conecta todos os componentes principais da aplicação.
        """

        catalog = ApplicationCatalog.discover()
        contribution_manager = ContributionManager()
        contribution_manager.register_many(catalog.contributions)

        self.application_registry = ApplicationRegistry(
            catalog.applications
        )

        # Interface
        self.main_window = PlatformMainWindow(contribution_manager)
        productive_root = Path(__file__).resolve().parents[1] / "projects"
        self.legacy_productive_database_path = Path(
            productive_database_path
            if productive_database_path is not None
            else productive_root / "productive-shell.sqlite"
        )
        self.legacy_productive_workspace_base = Path(
            productive_workspace_base
            if productive_workspace_base is not None
            else productive_root / "workspaces"
        )
        self.legacy_productive_database_detected = (
            self.legacy_productive_database_path.is_file()
        )
        if self.legacy_productive_database_detected:
            logging.getLogger(__name__).warning(
                "Banco produtivo legado preservado fora da autoridade: %s",
                self.legacy_productive_database_path,
            )
        self.productive_workspace = ProjectExplorerWindow(
            navigation_controller=(
                self.main_window.navigation_controller
            ),
            workspace_store=self.main_window.workspace_store,
        )
        self.main_window.install_productive_workspace(
            self.productive_workspace
        )
        # Estado da aplicação
        self.lifecycle_host = ApplicationLifecycleHost()
        self.project_state = ProjectState(self.lifecycle_host)
        self._productive_service = None

        # Serviços
        self.project_manager = ProjectManager()
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
            lifecycle_host=self.lifecycle_host,
            prepare_session_consumers=self._prepare_productive_service,
            commit_session_consumers=self._commit_productive_service,
            rollback_session_consumers=self._rollback_productive_service,
            close_session_consumers=self._close_productive_service,
            active_project_id=lambda _session: (
                self._productive_service.project.aggregate_id
                if self._productive_service is not None
                else _session.project.project_name
            ),
            initial_perspective=lambda _session: (
                "workspace_dashboard"
                if self._productive_service is not None
                else "home"
            ),
        )
        self.productive_workspace.new_project_requested.connect(
            self.project_controller.new_project
        )
        self.productive_workspace.open_project_requested.connect(
            self.project_controller.open_project
        )
        self.productive_workspace.close_project_requested.connect(
            self.project_controller.close_project
        )
        self.main_window.home_view.retry_requested.connect(
            self.project_controller.dashboard_controller.refresh
        )

    def _prepare_productive_service(self, session):
        factory = getattr(
            getattr(session, "application", None),
            "create_productive_service",
            None,
        )
        return None if factory is None else factory(session)

    def _commit_productive_service(
        self, _session, service, _previous_session
    ) -> None:
        previous = self._productive_service
        if service is None:
            self.productive_workspace.unbind_service()
        else:
            self.productive_workspace.bind_service(service)
        self.main_window.workspace_store.clear()
        self.main_window.selection_store.clear()
        self._productive_service = service
        if previous is not None and previous is not service:
            previous.close()

    def _rollback_productive_service(
        self, _previous_session, _candidate_session, candidate_service
    ) -> None:
        if candidate_service is not None:
            candidate_service.close()
        if self._productive_service is None:
            self.productive_workspace.unbind_service()
        else:
            self.productive_workspace.bind_service(self._productive_service)

    def _close_productive_service(self) -> None:
        service = self._productive_service
        try:
            self.productive_workspace.unbind_service()
            self.main_window.workspace_store.clear()
            self.main_window.selection_store.clear()
            self.main_window.navigation_controller.clear_history()
        except Exception:
            if service is not None:
                self.productive_workspace.bind_service(service)
            raise
        self._productive_service = None
        if service is not None:
            service.close()

    # ------------------------------------------------------------------

    def run(self):
        """
        Executa a aplicação.
        """

        self.main_window.show()

        return self.app.exec()
