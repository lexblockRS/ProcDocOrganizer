import ast
import os
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import Mock, patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication, QDialog

from applications.rsc.application import RscApplication
from core.application_registry import ApplicationRegistry
from core.project_controller import ProjectController
from core.project_manager import ProjectManager
from core.project_session_factory import ProjectSessionFactory
from core.project_state import ProjectState
from presentation import (
    ApplicationState,
    NotificationLevel,
    PerspectiveId,
    SelectionContext,
    SelectionIdentity,
    SelectionKind,
    WorkspaceState,
)
from ui.contribution_installer import DesktopContributionInstaller
from ui.main_window import MainWindow


class ProjectLifecycleIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.temporary_directory = TemporaryDirectory()
        self.root = Path(self.temporary_directory.name)
        self.window = MainWindow()
        self.state = ProjectState()
        self.manager = ProjectManager()
        self.application_registry = ApplicationRegistry([RscApplication()])
        self.controller = ProjectController(
            window=self.window,
            manager=self.manager,
            state=self.state,
            contribution_installer=DesktopContributionInstaller(
                self.window
            ),
            session_factory=ProjectSessionFactory(
                self.application_registry
            ),
            application_registry=self.application_registry,
        )
        self.notifications = []
        self.window.notification_center.subscribe(
            self.notifications.append
        )

    def tearDown(self):
        if self.state.has_project:
            self.controller.close_project()
        self.window.close()
        self.window.deleteLater()
        self.app.processEvents()
        self.temporary_directory.cleanup()

    def _create_project(self, name="Projeto"):
        dialog = Mock()
        dialog.exec.return_value = QDialog.DialogCode.Accepted
        dialog.get_project_name.return_value = name
        dialog.get_project_folder.return_value = self.root
        dialog.get_application_id.return_value = "rsc"
        with patch(
            "core.project_controller.NewProjectDialog",
            return_value=dialog,
        ):
            self.controller.new_project()
        return self.root / f"{name}.pdop"

    def test_create_project_updates_complete_presentation(self):
        project_path = self._create_project()
        self.assertTrue(project_path.is_dir())
        self.assertTrue(self.state.has_project)
        self.assertIs(
            self.window.application_state_store.snapshot.state,
            ApplicationState.PROJECT_OPEN,
        )
        self.assertEqual(
            self.window.windowTitle(),
            "ProcDocOrganizer — Projeto",
        )
        self.assertTrue(self.window.action_close_project.isEnabled())
        self.assertEqual(
            self.window.workspace_store.snapshot.active_perspective,
            PerspectiveId("home"),
        )
        self.assertIs(
            self.window.workspace_host.active_widget,
            self.window.home_view,
        )
        self.assertEqual(
            self.notifications[-1].level,
            NotificationLevel.SUCCESS,
        )
        self.assertEqual(
            self.notifications[-1].message,
            "Projeto criado.",
        )

    def test_close_project_clears_state_selection_and_workspace(self):
        self._create_project()
        self.window.selection_store.select(
            SelectionContext(
                SelectionIdentity(SelectionKind.DOCUMENT, "document-1")
            )
        )
        self.controller.close_project()
        self.assertFalse(self.state.has_project)
        self.assertIs(
            self.window.application_state_store.snapshot.state,
            ApplicationState.NO_PROJECT,
        )
        self.assertEqual(self.window.windowTitle(), "ProcDocOrganizer")
        self.assertFalse(self.window.action_close_project.isEnabled())
        self.assertIs(
            self.window.workspace_store.snapshot.state,
            WorkspaceState.EMPTY,
        )
        self.assertIs(
            self.window.selection_store.snapshot.selection.identity.kind,
            SelectionKind.NONE,
        )
        self.assertEqual(
            self.notifications[-1].message,
            "Projeto fechado.",
        )

    def test_open_existing_project_restores_complete_presentation(self):
        project_path = self._create_project("Existente")
        self.controller.close_project()
        with patch(
            "core.project_controller.QFileDialog.getExistingDirectory",
            return_value=str(project_path),
        ):
            self.controller.open_project()
        self.assertTrue(self.state.has_project)
        self.assertEqual(
            self.window.windowTitle(),
            "ProcDocOrganizer — Existente",
        )
        self.assertIs(
            self.window.application_state_store.snapshot.state,
            ApplicationState.PROJECT_OPEN,
        )
        self.assertEqual(
            self.window.workspace_store.snapshot.active_perspective,
            PerspectiveId("home"),
        )
        self.assertEqual(
            self.notifications[-1].message,
            "Projeto aberto.",
        )

    def test_cancelled_create_and_open_are_noops(self):
        initial_application = self.window.application_state_store.snapshot
        initial_workspace = self.window.workspace_store.snapshot
        dialog = Mock()
        dialog.exec.return_value = QDialog.DialogCode.Rejected
        with patch(
            "core.project_controller.NewProjectDialog",
            return_value=dialog,
        ):
            self.controller.new_project()
        with patch(
            "core.project_controller.QFileDialog.getExistingDirectory",
            return_value="",
        ):
            self.controller.open_project()
        self.assertFalse(self.state.has_project)
        self.assertIs(
            self.window.application_state_store.snapshot,
            initial_application,
        )
        self.assertIs(
            self.window.workspace_store.snapshot,
            initial_workspace,
        )
        self.assertEqual(self.notifications, [])

    def test_create_failure_uses_operation_state_and_notification(self):
        with patch.object(
            self.manager,
            "create_project",
            side_effect=RuntimeError("falha simulada"),
        ):
            self._create_project()
        self.assertFalse(self.state.has_project)
        self.assertIs(
            self.window.application_state_store.snapshot.state,
            ApplicationState.ERROR,
        )
        self.assertEqual(
            self.notifications[-1].level,
            NotificationLevel.ERROR,
        )
        self.assertIn(
            "falha simulada",
            self.notifications[-1].message,
        )

    def test_menu_and_toolbar_share_state_driven_action(self):
        close_action = self.window.action_close_project
        self.assertIn(close_action, self.window.get_menu("file").actions())
        self.assertIn(
            close_action,
            self.window._toolbars_by_id["main"].actions(),
        )
        self.assertFalse(close_action.isEnabled())
        self._create_project()
        self.assertTrue(close_action.isEnabled())
        self.controller.close_project()
        self.assertFalse(close_action.isEnabled())


class ProjectLifecycleArchitectureTests(unittest.TestCase):
    def test_main_window_does_not_run_project_lifecycle(self):
        tree = ast.parse(
            Path("ui/main_window.py").read_text(encoding="utf-8")
        )
        called = {
            node.func.attr
            for node in ast.walk(tree)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
        }
        self.assertNotIn("create_project", called)
        self.assertNotIn("open_project", called)
        self.assertNotIn("close_project", called)
        self.assertNotIn("transition_to", called)

    def test_architectural_contract_modules_are_unchanged_by_integration(self):
        controller_source = Path(
            "core/project_controller.py"
        ).read_text(encoding="utf-8")
        self.assertIn("operation_executor", controller_source)
        self.assertIn("notification_center", controller_source)
        self.assertNotIn("applications.rsc", controller_source)


if __name__ == "__main__":
    unittest.main()
