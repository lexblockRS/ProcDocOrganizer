import os
from datetime import date
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication, QDialog
from PySide6.QtCore import Qt

from applications import RscApplication
from core.application_registry import ApplicationRegistry
from core.project_controller import ProjectController
from core.project_manager import ProjectManager
from core.project_session_factory import ProjectSessionFactory
from core.project_state import ProjectState
from core.application_lifecycle_host import ApplicationLifecycleHost
from models import EvidenceDraft, EvidenceSourceCandidate
from services.processing import ProcessingRepository, ProcessingResult
from ui.contribution_installer import DesktopContributionInstaller
from ui.main_window import MainWindow


class AssignmentDialog:
    def __init__(self, evidence, parent=None):
        self.evidence = evidence

    def exec(self):
        return QDialog.DialogCode.Accepted

    def values(self):
        return {
            "person_id": "person-1",
            "exercise_type_code": "comissao",
            "exercise_type_label": "Comissão",
            "role": "Membro",
            "organization": "Universidade",
            "unit": "Reitoria",
            "administrative_reference": "Portaria 1",
            "start_date": "2024-01-01",
            "end_date": "",
        }


class ExerciseDialog:
    def __init__(self, assignments, parent=None):
        self.assignments = assignments

    def exec(self):
        return QDialog.DialogCode.Accepted

    def values(self):
        return {
            "person_id": "person-1",
            "exercise_type_code": "comissao",
            "exercise_type_label": "Comissão",
            "role": "Membro",
            "context_organization": "Universidade",
            "context_unit": "Reitoria",
            "context_reference": "Portaria 1",
            "start_date": date(2024, 1, 1),
            "end_date": None,
        }


class ActivityDialog:
    def __init__(self, count, parent=None):
        self.count = count

    def exec(self):
        return QDialog.DialogCode.Accepted

    def values(self):
        return {"description": "Participação em comissão"}


class RscPipelineEndToEndTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_complete_pipeline_reopens_and_navigates_back_to_page(self):
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            manager = ProjectManager()
            project = manager.create_project(
                "Pipeline RSC", root, application_id="rsc"
            )
            factory = ProjectSessionFactory(
                ApplicationRegistry([RscApplication()])
            )
            window = MainWindow()
            self.addCleanup(window.close)
            lifecycle_host = ApplicationLifecycleHost()
            controller = ProjectController(
                window,
                manager,
                ProjectState(lifecycle_host),
                DesktopContributionInstaller(window),
                session_factory=factory,
                application_registry=ApplicationRegistry(
                    [RscApplication()]
                ),
                lifecycle_host=lifecycle_host,
            )
            controller._load_project(project)

            source = root / "portaria.pdf"
            source.write_bytes(b"%PDF-fixture")
            document = (
                controller.session.document_import_service
                .import_file(source).document
            )
            ProcessingRepository(project).save(ProcessingResult(
                document_sha256=document.sha256,
                processed_at="2024-01-01T00:00:00",
                status="processed",
                page_count=5,
                pages=[
                    {"page": 5, "text": "participação na comissão"}
                ],
            ))
            controller.documents_controller.refresh()

            candidate = EvidenceSourceCandidate(
                document_identity=document.sha256,
                page_number=5,
                suggested_title="Portaria",
                source_snippet="participação na comissão",
            )
            self.assertTrue(
                controller.evidence_controller.start_create_from_source(
                    candidate
                )
            )
            self.assertTrue(controller.evidence_controller.save())
            evidence = controller.evidence_controller.selected_evidence

            controller.functional_assignments_controller._dialog_factory = (
                AssignmentDialog
            )
            self.assertTrue(controller.interpret_selected_evidence())
            self.assertTrue(
                controller.functional_assignments_controller.advance()
            )
            self.assertTrue(
                controller.functional_assignments_controller.advance()
            )
            assignment = (
                controller.session.rsc_session
                .list_functional_assignment_evidences_service.execute()[0]
            )
            window.functional_assignments_view.select_assignment(
                assignment.id
            )
            window.functional_assignments_view.list_widget.item(0).setSelected(
                True
            )

            controller.functional_exercises_controller._dialog_factory = (
                ExerciseDialog
            )
            self.assertTrue(controller.create_functional_exercise())
            exercise = (
                controller.session.rsc_session
                .list_functional_exercises_service.execute()[0]
            )
            window.functional_exercises_view.select_exercise(exercise.id)
            window.functional_exercises_view.list_widget.item(0).setSelected(
                True
            )

            controller.activities_controller._dialog_factory = ActivityDialog
            self.assertTrue(controller.create_activity())
            activity = (
                controller.session.rsc_session
                .activity_repository.list_all()[0]
            )
            ids = (
                evidence.id,
                assignment.id,
                exercise.id,
                activity.activity_id,
            )

            controller.close_project()
            controller._load_project(project)
            self.assertEqual(
                ids[3],
                controller.session.rsc_session
                .activity_repository.list_all()[0].activity_id,
            )

            controller.show_activities()
            self.assertEqual(
                window.activities_view.activity_list.currentItem().data(
                    Qt.ItemDataRole.UserRole
                ),
                ids[3],
            )
            exercise_row = window.activities_view.exercise_list.item(0)
            window.activities_view.exercise_list.setCurrentItem(exercise_row)
            window.activities_view.open_exercise_button.click()
            self.app.processEvents()
            self.assertIs(
                window.stack.currentWidget(),
                window.functional_exercises_view,
            )
            self.assertEqual(
                window.functional_exercises_view.list_widget.currentItem()
                .data(Qt.ItemDataRole.UserRole),
                ids[2],
            )

            related = window.functional_exercises_view.related_list.item(0)
            window.functional_exercises_view.related_list.setCurrentItem(
                related
            )
            window.functional_exercises_view.open_assignment_button.click()
            self.app.processEvents()
            self.assertEqual(
                window.functional_assignments_view.list_widget.currentItem()
                .data(Qt.ItemDataRole.UserRole),
                ids[1],
            )
            self.assertIn(
                "participação na comissão",
                window.functional_assignments_view.details["snippet"].text(),
            )

            window.functional_assignments_view.open_source_button.click()
            self.app.processEvents()
            self.assertEqual(
                controller.evidence_controller.selected_evidence.id,
                ids[0],
            )
            window.evidence_workspace.open_document_button.click()
            self.app.processEvents()
            self.assertIs(
                window.stack.currentWidget(),
                window.documents_workspace,
            )
            self.assertEqual(
                controller.documents_controller.selected_identity,
                document.sha256,
            )
            self.assertEqual(
                controller.documents_controller.selected_page_number, 5
            )
            self.assertEqual(
                window.documents_workspace.current_page.page_number, 5
            )
            self.assertIn(
                "participação na comissão",
                window.documents_workspace.current_page.text,
            )

    def test_common_rsc_common_switch_clears_functional_state(self):
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            manager = ProjectManager()
            common = manager.create_project("Comum 1", root)
            rsc = manager.create_project(
                "RSC", root, application_id="rsc"
            )
            other_common = manager.create_project("Comum 2", root)
            window = MainWindow()
            self.addCleanup(window.close)
            lifecycle_host = ApplicationLifecycleHost()
            controller = ProjectController(
                window,
                manager,
                ProjectState(lifecycle_host),
                DesktopContributionInstaller(window),
                session_factory=ProjectSessionFactory(
                    ApplicationRegistry([RscApplication()])
                ),
                application_registry=ApplicationRegistry(
                    [RscApplication()]
                ),
                lifecycle_host=lifecycle_host,
            )

            controller._load_project(common)
            self.assertIsNone(controller.session.rsc_session)
            controller.close_project()
            controller._load_project(rsc)
            self.assertIsNotNone(controller.session.rsc_session)
            self.assertTrue(window.action_functional_exercises.isVisible())
            controller.close_project()
            controller._load_project(other_common)

            self.assertIsNone(controller.session.rsc_session)
            self.assertFalse(window.action_functional_assignments.isVisible())
            self.assertFalse(window.action_functional_exercises.isVisible())
            self.assertFalse(window.action_activities.isEnabled())
            self.assertIsNone(
                controller.activities_controller._session
            )
            self.assertIsNone(
                controller.functional_exercises_controller._session
            )
            self.assertEqual(
                window.activities_view.activity_list.count(), 0
            )
            self.assertEqual(
                window.functional_exercises_view.list_widget.count(), 0
            )


if __name__ == "__main__":
    unittest.main()
