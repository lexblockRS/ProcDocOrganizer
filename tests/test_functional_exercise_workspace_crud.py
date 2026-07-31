import os
from datetime import date
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import Mock, patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication, QDialog, QMessageBox

from applications.rsc.application import RscApplication
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


class ExerciseDialogDouble:
    accepted = True
    role = "Coordenador"

    def __init__(self, assignments, _parent=None):
        self.assignments = assignments

    def exec(self):
        return (
            QDialog.DialogCode.Accepted
            if self.accepted else QDialog.DialogCode.Rejected
        )

    def values(self):
        first = self.assignments[0]
        return {
            "person_id": first.person_id,
            "exercise_type_code": first.exercise_type_code,
            "exercise_type_label": first.exercise_type_label,
            "role": self.role,
            "context_organization": first.organization,
            "context_unit": first.unit,
            "context_reference": first.administrative_reference,
            "start_date": date(2024, 1, 1),
            "end_date": None,
        }


class AssignmentDialogDouble:
    def __init__(self, _evidence, _parent=None):
        pass

    def exec(self):
        return QDialog.DialogCode.Accepted

    def values(self):
        return {
            "person_id": "person-1",
            "exercise_type_code": "coordenacao",
            "exercise_type_label": "Coordenação",
            "role": "Coordenador",
            "organization": "Instituto",
            "unit": "Campus",
            "administrative_reference": "Portaria 10",
            "start_date": "2024-01-01",
            "end_date": "",
        }


class FunctionalExerciseWorkspaceCrudTests(unittest.TestCase):
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
        self.assignment = self._create_assignment()
        self.exercise_controller = (
            self.controller.functional_exercises_controller
        )
        self.exercise_controller._dialog_factory = ExerciseDialogDouble
        ExerciseDialogDouble.accepted = True
        ExerciseDialogDouble.role = "Coordenador"

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

    def _create_assignment(self):
        source = self.root / "fonte.pdf"
        source.write_bytes(b"%PDF exercise")
        with patch(
            "core.project_controller.QFileDialog.getOpenFileNames",
            return_value=([str(source)], "Arquivos PDF"),
        ):
            self.controller.import_documents()
        document = self.controller.session.document_repository.list_documents()[0]
        evidence = self.controller.session.evidence_service.create(
            CreateEvidenceRequest(
                document_identity=document.sha256,
                title="Portaria",
            )
        )
        assignment_controller = (
            self.controller.functional_assignments_controller
        )
        assignment_controller._dialog_factory = AssignmentDialogDouble
        assignment_controller.create_from_evidence(evidence)
        assignment_controller.advance()
        assignment_controller.advance()
        return (
            self.controller.session.rsc_session
            .functional_assignment_evidence_repository.list_all()[0]
        )

    @property
    def repository(self):
        return (
            self.controller.session.rsc_session
            .functional_exercise_repository
        )

    def test_create_edit_selection_notification_and_reopen(self):
        self.assertTrue(
            self.exercise_controller.create((str(self.assignment.id),))
        )
        created = self.repository.list_all()[0]
        selection = self.window.selection_store.snapshot.selection
        self.assertIs(
            selection.identity.kind,
            SelectionKind.FUNCTIONAL_EXERCISE,
        )
        self.assertEqual(selection.identity.identifier, str(created.id))
        self.assertIs(
            self.notifications[-1].level,
            NotificationLevel.SUCCESS,
        )

        ExerciseDialogDouble.role = "Diretor"
        self.assertTrue(self.exercise_controller.edit())
        self.assertEqual(
            self.repository.get_by_id(created.id).role.name,
            "Diretor",
        )

        self.controller.close_project()
        with patch(
            "core.project_controller.QFileDialog.getExistingDirectory",
            return_value=str(self.project_path),
        ):
            self.controller.open_project()
        reopened = (
            self.controller.session.rsc_session
            .functional_exercise_repository.get_by_id(created.id)
        )
        self.assertEqual(reopened.role.name, "Diretor")
        self.assertEqual(
            reopened.functional_assignment_evidence_ids,
            (self.assignment.id,),
        )

    def test_delete_preserves_assignment_and_cancel_notifies(self):
        ExerciseDialogDouble.accepted = False
        self.assertFalse(
            self.exercise_controller.create((str(self.assignment.id),))
        )
        self.assertEqual(
            self.notifications[-1].message,
            "Operação cancelada.",
        )

        ExerciseDialogDouble.accepted = True
        self.exercise_controller.create((str(self.assignment.id),))
        created = self.repository.list_all()[0]
        with patch(
            "core.project_controller.QMessageBox.question",
            return_value=QMessageBox.StandardButton.Yes,
        ):
            self.assertTrue(self.exercise_controller.delete())
        self.assertIsNone(self.repository.get_by_id(created.id))
        self.assertIsNotNone(
            self.controller.session.rsc_session
            .functional_assignment_evidence_repository.get_by_id(
                self.assignment.id
            )
        )
        self.assertIs(
            self.window.selection_store.snapshot.selection.identity.kind,
            SelectionKind.NONE,
        )
