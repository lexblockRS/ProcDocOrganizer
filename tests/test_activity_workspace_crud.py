import os
from datetime import date
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import Mock, patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication, QDialog, QMessageBox

from applications.rsc.application import RscApplication
from applications.rsc.commands import (
    CreateFunctionalAssignmentEvidenceCommand,
    CreateFunctionalExerciseCommand,
)
from applications.rsc.models import (
    ActivityState,
    FunctionalAssignmentEvidenceId,
)
from core.application_registry import ApplicationRegistry
from core.project_controller import ProjectController
from core.project_manager import ProjectManager
from core.project_session_factory import ProjectSessionFactory
from core.project_state import ProjectState
from models import CreateEvidenceRequest
from presentation import NotificationLevel, SelectionKind
from ui.contribution_installer import DesktopContributionInstaller
from ui.main_window import MainWindow


class ActivityDialogDouble:
    def __init__(self, description, accepted=True):
        self.description = description
        self.accepted = accepted

    def exec(self):
        return (
            QDialog.DialogCode.Accepted
            if self.accepted
            else QDialog.DialogCode.Rejected
        )

    def values(self):
        return {"description": self.description}


class ActivityWorkspaceCrudTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.temporary_directory = TemporaryDirectory()
        self.root = Path(self.temporary_directory.name)
        self.window = MainWindow()
        self.state = ProjectState()
        self.manager = ProjectManager()
        registry = ApplicationRegistry([RscApplication()])
        self.controller = ProjectController(
            window=self.window,
            manager=self.manager,
            state=self.state,
            contribution_installer=DesktopContributionInstaller(
                self.window
            ),
            session_factory=ProjectSessionFactory(registry),
            application_registry=registry,
        )
        self.notifications = []
        self.window.notification_center.subscribe(
            self.notifications.append
        )
        self.project_path = self._create_project()
        self.exercise_id = self._create_functional_exercise()
        self.window.show_activities()

    def tearDown(self):
        if self.state.has_project:
            if self.window.activities_view.is_editing:
                self.window.activities_view.cancel_edit()
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

    @property
    def repository(self):
        return self.controller.session.rsc_session.activity_repository

    def _create_functional_exercise(self):
        source = self.root / "activity-source.pdf"
        source.write_bytes(b"%PDF activity")
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
        rsc = self.controller.session.rsc_session
        assignment = (
            rsc.create_functional_assignment_evidence_service.execute(
                CreateFunctionalAssignmentEvidenceCommand(
                    person_id="person-1",
                    source_evidence_reference=evidence.id,
                    exercise_type_code="coordenacao",
                    exercise_type_label="Coordenação",
                    role="Coordenador",
                    organization="Universidade",
                    start_date=date(2024, 1, 1),
                )
            )
        )
        assignment_domain = (
            rsc.functional_assignment_evidence_repository.get_by_id(
                FunctionalAssignmentEvidenceId.from_string(assignment.id)
            )
        )
        rsc.functional_assignment_evidence_repository.update(
            assignment_domain.mark_identified().mark_linked()
        )
        exercise = rsc.create_functional_exercise_service.execute(
            CreateFunctionalExerciseCommand(
                person_id="person-1",
                exercise_type_code="coordenacao",
                exercise_type_label="Coordenação",
                role="Coordenador",
                context_organization="Universidade",
                start_date=date(2024, 1, 1),
                functional_assignment_evidence_ids=(assignment.id,),
            )
        )
        return exercise.id

    def _create_activity(self, description="Coordenação acadêmica"):
        dialog = ActivityDialogDouble(description)
        self.controller.activities_controller._dialog_factory = (
            lambda *_args: dialog
        )
        self.controller.activities_controller.create((self.exercise_id,))
        return self.repository.list_all()[-1]

    def test_create_select_edit_persist_and_reopen(self):
        created = self._create_activity()
        self.assertIs(created.state, ActivityState.REMEMBERED)
        self.assertEqual(created.functional_assignment_evidence_ids, ())
        self.assertEqual(
            tuple(str(item) for item in created.functional_exercise_ids),
            (self.exercise_id,),
        )
        self.assertEqual(
            self.window.activities_view.activity_list.count(),
            1,
        )
        selection = self.window.selection_store.snapshot.selection
        self.assertIs(selection.identity.kind, SelectionKind.ACTIVITY)
        self.assertEqual(selection.identity.identifier, created.activity_id)
        self.assertEqual(
            self.notifications[-1].message,
            "Activity criada.",
        )

        view = self.window.activities_view
        view.edit_action.trigger()
        self.assertTrue(view.is_editing)
        view.description_editor.setText("Coordenação de extensão")
        self.assertTrue(view.has_unsaved_changes)
        view.save_button.click()
        updated = self.repository.get(created.activity_id)
        self.assertEqual(updated.description, "Coordenação de extensão")
        self.assertEqual(
            view.details_description_label.text(),
            "Coordenação de extensão",
        )
        self.assertFalse(view.is_editing)
        self.assertEqual(
            self.notifications[-1].message,
            "Activity atualizada.",
        )

        self.controller.close_project()
        with patch(
            "core.project_controller.QFileDialog.getExistingDirectory",
            return_value=str(self.project_path),
        ):
            self.controller.open_project()
        reopened = self.controller.session.rsc_session.activity_repository.get(
            created.activity_id
        )
        self.assertEqual(reopened.description, "Coordenação de extensão")

    def test_edit_state_uses_aggregate_transition_and_reopens(self):
        created = self._create_activity()
        view = self.window.activities_view
        view.edit_action.trigger()
        index = view.state_editor.findData(
            ActivityState.UNDER_INVESTIGATION.value
        )
        self.assertGreaterEqual(index, 0)
        view.state_editor.setCurrentIndex(index)
        self.assertTrue(view.has_unsaved_changes)
        view.save_button.click()

        updated = self.repository.get(created.activity_id)
        self.assertIs(
            updated.state,
            ActivityState.UNDER_INVESTIGATION,
        )
        self.assertIn(
            "Em investigação",
            view.details_state_label.text(),
        )

        self.controller.close_project()
        with patch(
            "core.project_controller.QFileDialog.getExistingDirectory",
            return_value=str(self.project_path),
        ):
            self.controller.open_project()
        reopened = self.controller.session.rsc_session.activity_repository.get(
            created.activity_id
        )
        self.assertIs(
            reopened.state,
            ActivityState.UNDER_INVESTIGATION,
        )

    def test_invalid_state_jump_stays_in_inspector(self):
        created = self._create_activity()
        view = self.window.activities_view
        view.edit_action.trigger()
        index = view.state_editor.findData(ActivityState.PROVEN.value)
        view.state_editor.setCurrentIndex(index)
        view.save_button.click()

        self.assertTrue(view.is_editing)
        self.assertIn("ciclo sequencial", view.unsaved_label.text())
        self.assertIs(
            self.repository.get(created.activity_id).state,
            ActivityState.REMEMBERED,
        )

    def test_cancel_create_and_edit_preserve_repository(self):
        rejected = ActivityDialogDouble("Ignorada", accepted=False)
        self.controller.activities_controller._dialog_factory = (
            lambda *_args: rejected
        )
        self.controller.activities_controller.create((self.exercise_id,))
        self.assertEqual(self.repository.list_all(), ())
        self.assertEqual(
            self.notifications[-1].message,
            "Operação cancelada.",
        )

        created = self._create_activity("Descrição original")
        view = self.window.activities_view
        view.edit_action.trigger()
        view.description_editor.setText("Não salvar")
        view.cancel_button.click()
        self.assertEqual(
            self.repository.get(created.activity_id).description,
            "Descrição original",
        )
        self.assertEqual(
            view.details_description_label.text(),
            "Descrição original",
        )
        self.assertEqual(
            self.notifications[-1].message,
            "Operação cancelada.",
        )

    def test_delete_confirmation_notification_and_reopen(self):
        created = self._create_activity()
        with patch(
            "core.project_controller.QMessageBox.question",
            return_value=QMessageBox.StandardButton.No,
        ):
            self.window.activities_view.delete_action.trigger()
        self.assertIsNotNone(self.repository.get(created.activity_id))
        self.assertEqual(
            self.notifications[-1].message,
            "Operação cancelada.",
        )

        with patch(
            "core.project_controller.QMessageBox.question",
            return_value=QMessageBox.StandardButton.Yes,
        ):
            self.window.activities_view.delete_action.trigger()
        self.assertIsNone(self.repository.get(created.activity_id))
        self.assertEqual(
            self.window.activities_view.activity_list.count(),
            0,
        )
        self.assertIs(
            self.window.selection_store.snapshot.selection.identity.kind,
            SelectionKind.NONE,
        )
        self.assertEqual(
            self.notifications[-1].message,
            "Activity removida.",
        )

        self.controller.close_project()
        with patch(
            "core.project_controller.QFileDialog.getExistingDirectory",
            return_value=str(self.project_path),
        ):
            self.controller.open_project()
        self.assertEqual(
            self.controller.session.rsc_session
            .activity_repository.list_all(),
            (),
        )

    def test_validation_and_persistence_failures_are_visible(self):
        invalid = ActivityDialogDouble(" ")
        self.controller.activities_controller._dialog_factory = (
            lambda *_args: invalid
        )
        self.controller.activities_controller.create((self.exercise_id,))
        self.assertEqual(self.repository.list_all(), ())
        self.assertIs(
            self.notifications[-1].level,
            NotificationLevel.ERROR,
        )

        self._create_activity()
        view = self.window.activities_view
        view.edit_action.trigger()
        view.description_editor.setText("Atualização")
        with patch.object(
            self.controller.activities_controller._management_service,
            "update",
            side_effect=RuntimeError("SQLite indisponível"),
        ):
            view.save_button.click()
        self.assertTrue(view.is_editing)
        self.assertIn("SQLite", view.unsaved_label.text())
        self.assertIs(
            self.notifications[-1].level,
            NotificationLevel.ERROR,
        )


if __name__ == "__main__":
    unittest.main()
