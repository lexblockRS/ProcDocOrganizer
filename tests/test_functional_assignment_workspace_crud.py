import os
from datetime import date
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import Mock, patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication, QDialog, QMessageBox

from applications.rsc.application import RscApplication
from applications.rsc.models import FunctionalAssignmentEvidenceStatus
from core.application_registry import ApplicationRegistry
from core.project_controller import ProjectController
from core.project_manager import ProjectManager
from core.project_session_factory import ProjectSessionFactory
from core.project_state import ProjectState
from core.application_lifecycle_host import ApplicationLifecycleHost
from models import CreateEvidenceRequest
from presentation import NotificationLevel, SelectionKind
from ui.contribution_installer import DesktopContributionInstaller
from ui.main_window import MainWindow


class AssignmentDialogDouble:
    values_result = {}
    accepted = True

    def __init__(self, _evidence, _parent=None):
        pass

    def exec(self):
        return (
            QDialog.DialogCode.Accepted
            if self.accepted
            else QDialog.DialogCode.Rejected
        )

    def values(self):
        return dict(self.values_result)


class FunctionalAssignmentWorkspaceCrudTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.temporary_directory = TemporaryDirectory()
        self.root = Path(self.temporary_directory.name)
        self.window = MainWindow()
        self.lifecycle_host = ApplicationLifecycleHost()
        self.state = ProjectState(self.lifecycle_host)
        registry = ApplicationRegistry([RscApplication()])
        self.controller = ProjectController(
            self.window,
            ProjectManager(),
            self.state,
            DesktopContributionInstaller(self.window),
            session_factory=ProjectSessionFactory(registry),
            application_registry=registry,
            lifecycle_host=self.lifecycle_host,
        )
        self.notifications = []
        self.window.notification_center.subscribe(
            self.notifications.append
        )
        self.project_path = self._create_project()
        self.evidence = self._create_evidence()
        self.assignment_controller = (
            self.controller.functional_assignments_controller
        )
        self.assignment_controller._dialog_factory = AssignmentDialogDouble
        AssignmentDialogDouble.accepted = True
        AssignmentDialogDouble.values_result = self._values()

    def tearDown(self):
        if self.state.has_project:
            self.controller.close_project()
        self.window.close()
        self.window.deleteLater()
        self.app.processEvents()
        self.temporary_directory.cleanup()

    def _create_project(self):
        dialog = Mock()
        dialog.exec.return_value = QDialog.DialogCode.Accepted
        dialog.get_project_name.return_value = "Projeto"
        dialog.get_project_folder.return_value = self.root
        dialog.get_application_id.return_value = "rsc"
        with patch(
            "core.project_controller.NewProjectDialog",
            return_value=dialog,
        ):
            self.controller.new_project()
        return self.root / "Projeto.pdop"

    def _create_evidence(self):
        source = self.root / "Portaria.pdf"
        source.write_bytes(b"%PDF-1.4 assignment")
        with patch(
            "core.project_controller.QFileDialog.getOpenFileNames",
            return_value=([str(source)], "Arquivos PDF"),
        ):
            self.controller.import_documents()
        document = (
            self.controller.session.document_repository
            .list_documents()[0]
        )
        return self.controller.session.evidence_service.create(
            CreateEvidenceRequest(
                document_identity=document.sha256,
                title="Portaria",
            )
        )

    @staticmethod
    def _values(role="Coordenador"):
        return {
            "person_id": "person-1",
            "exercise_type_code": "coordenacao",
            "exercise_type_label": "Coordenação",
            "role": role,
            "organization": "Instituto",
            "unit": "Campus",
            "administrative_reference": "Portaria 10",
            "start_date": "2024-01-01",
            "end_date": "",
        }

    @property
    def repository(self):
        return (
            self.controller.session.rsc_session
            .functional_assignment_evidence_repository
        )

    def _create(self):
        self.assertTrue(
            self.assignment_controller.create_from_evidence(self.evidence)
        )
        return self.repository.list_all()[0]

    def test_create_edit_pipeline_selection_notifications_and_reopen(self):
        created = self._create()
        self.assertIs(
            created.status,
            FunctionalAssignmentEvidenceStatus.RAW,
        )
        selection = self.window.selection_store.snapshot.selection
        self.assertIs(
            selection.identity.kind,
            SelectionKind.FUNCTIONAL_ASSIGNMENT,
        )
        self.assertEqual(selection.identity.identifier, str(created.id))
        self.assertIs(
            self.notifications[-1].level,
            NotificationLevel.SUCCESS,
        )

        AssignmentDialogDouble.values_result = self._values("Diretor")
        self.assertTrue(self.assignment_controller.edit())
        self.assertEqual(
            self.repository.get_by_id(created.id).role,
            "Diretor",
        )
        self.assertTrue(self.assignment_controller.advance())
        self.assertIs(
            self.repository.get_by_id(created.id).status,
            FunctionalAssignmentEvidenceStatus.IDENTIFIED,
        )
        self.assertTrue(self.assignment_controller.advance())
        self.assertIs(
            self.repository.get_by_id(created.id).status,
            FunctionalAssignmentEvidenceStatus.LINKED,
        )

        self.controller.close_project()
        with patch(
            "core.project_controller.QFileDialog.getExistingDirectory",
            return_value=str(self.project_path),
        ):
            self.controller.open_project()
        reopened = (
            self.controller.session.rsc_session
            .functional_assignment_evidence_repository
            .get_by_id(created.id)
        )
        self.assertEqual(reopened.role, "Diretor")
        self.assertIs(
            reopened.status,
            FunctionalAssignmentEvidenceStatus.LINKED,
        )

    def test_delete_is_scoped_to_assignment(self):
        created = self._create()
        with patch(
            "core.project_controller.QMessageBox.question",
            return_value=QMessageBox.StandardButton.Yes,
        ):
            self.assertTrue(self.assignment_controller.delete())

        self.assertIsNone(self.repository.get_by_id(created.id))
        self.assertIsNotNone(
            self.controller.session.evidence_service.get(self.evidence.id)
        )
        self.assertIs(
            self.window.selection_store.snapshot.selection.identity.kind,
            SelectionKind.NONE,
        )
        self.assertEqual(
            self.notifications[-1].message,
            "Interpretação funcional removida.",
        )

    def test_cancel_and_persistence_failure_notify(self):
        AssignmentDialogDouble.accepted = False
        self.assertFalse(
            self.assignment_controller.create_from_evidence(self.evidence)
        )
        self.assertEqual(
            self.notifications[-1].message,
            "Operação cancelada.",
        )

        AssignmentDialogDouble.accepted = True
        self._create()
        AssignmentDialogDouble.values_result = self._values("Diretor")
        with patch.object(
            self.assignment_controller._management_service,
            "update",
            side_effect=RuntimeError("SQLite indisponível"),
        ):
            self.assertFalse(self.assignment_controller.edit())
        self.assertIs(
            self.notifications[-1].level,
            NotificationLevel.ERROR,
        )


if __name__ == "__main__":
    unittest.main()
