import ast
import os
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import Mock, patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication, QDialog

from applications import RscApplication
from core.application_registry import ApplicationRegistry
from core.project_controller import ProjectController
from core.project_manager import ProjectManager
from core.project_session_factory import ProjectSessionFactory
from models.project import LEGACY_APPLICATION_ID
from ui.dialogs import NewProjectDialog


class NewProjectApplicationSelectionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.registry = ApplicationRegistry([RscApplication()])
        self.dialog = NewProjectDialog(
            applications=self.registry.applications
        )

    def tearDown(self):
        self.dialog.close()

    def test_dialog_lists_legacy_and_registered_applications(self):
        options = {
            self.dialog.application_selector.itemData(index):
            self.dialog.application_selector.itemText(index)
            for index in range(
                self.dialog.application_selector.count()
            )
        }

        self.assertEqual(
            options[LEGACY_APPLICATION_ID],
            "Projeto legado / ProcDocOrganizer",
        )
        self.assertEqual(options["rsc"], "RSC")

    def test_dialog_returns_selected_application_id(self):
        legacy_index = self.dialog.application_selector.findData(
            LEGACY_APPLICATION_ID
        )
        self.dialog.application_selector.setCurrentIndex(legacy_index)
        self.assertEqual(
            self.dialog.get_application_id(),
            LEGACY_APPLICATION_ID,
        )

        rsc_index = self.dialog.application_selector.findData("rsc")
        self.dialog.application_selector.setCurrentIndex(rsc_index)
        self.assertEqual(self.dialog.get_application_id(), "rsc")

    def test_dialog_does_not_import_rsc_application(self):
        source = (
            Path(__file__).parents[1]
            / "ui"
            / "dialogs"
            / "new_project_dialog.py"
        ).read_text(encoding="utf-8")

        self.assertNotIn("RscApplication", source)
        self.assertNotIn("applications.rsc", source)


class ProjectCreationApplicationFlowTests(unittest.TestCase):
    def test_manager_persists_selected_id_and_preserves_legacy_default(self):
        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            manager = ProjectManager()
            legacy = manager.create_project("Legado", root)
            rsc = manager.create_project(
                "RSC", root, application_id="rsc"
            )

            self.assertEqual(
                manager.open_project(legacy.project_path).application,
                LEGACY_APPLICATION_ID,
            )
            reopened_rsc = manager.open_project(rsc.project_path)
            self.assertEqual(reopened_rsc.application, "rsc")
            session = ProjectSessionFactory(
                ApplicationRegistry([RscApplication()])
            ).create(reopened_rsc)
            self.assertIsInstance(session.application, RscApplication)

    def test_controller_passes_registry_options_and_selected_id(self):
        registry = ApplicationRegistry([RscApplication()])
        controller = ProjectController.__new__(ProjectController)
        controller.window = object()
        controller.manager = Mock()
        controller.state = Mock()
        controller.application_registry = registry
        controller.evidence_controller = Mock()
        controller.evidence_controller.can_leave.return_value = True
        controller._load_project = Mock()
        controller.manager.create_project.return_value = object()

        dialog = Mock()
        dialog.exec.return_value = QDialog.DialogCode.Accepted
        dialog.get_project_name.return_value = "Projeto"
        dialog.get_project_folder.return_value = Path("destino")
        dialog.get_application_id.return_value = "rsc"

        with patch(
            "core.project_controller.NewProjectDialog",
            return_value=dialog,
        ) as dialog_class:
            controller.new_project()

        dialog_class.assert_called_once_with(
            controller.window,
            applications=registry.applications,
        )
        controller.manager.create_project.assert_called_once_with(
            "Projeto",
            Path("destino"),
            application_id="rsc",
        )

    def test_manager_and_factory_remain_application_agnostic(self):
        root = Path(__file__).parents[1]
        for relative_path in (
            "core/project_manager.py",
            "core/project_session_factory.py",
        ):
            with self.subTest(path=relative_path):
                source = (
                    root / relative_path
                ).read_text(encoding="utf-8")
                self.assertNotIn("RscApplication", source)
                self.assertNotIn("applications.rsc", source)

        manager_tree = ast.parse(
            (root / "core/project_manager.py").read_text(
                encoding="utf-8"
            )
        )
        manager_imports = {
            node.module or ""
            for node in ast.walk(manager_tree)
            if isinstance(node, ast.ImportFrom)
        }
        self.assertNotIn(
            "core.application_registry",
            manager_imports,
        )


if __name__ == "__main__":
    unittest.main()
