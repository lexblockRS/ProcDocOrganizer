import os
from datetime import date
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication, QDialog

from applications import RscApplication
from applications.rsc.commands import (
    CreateFunctionalAssignmentEvidenceCommand,
)
from applications.rsc.models import FunctionalAssignmentEvidenceId
from core.application_registry import ApplicationRegistry
from core.project_controller import ProjectController
from core.project_manager import ProjectManager
from core.project_session_factory import ProjectSessionFactory
from core.project_state import ProjectState
from core.application_lifecycle_host import ApplicationLifecycleHost
from models import CreateEvidenceRequest
from presentation.functional_exercises import FunctionalExercisesController
from ui.contribution_installer import DesktopContributionInstaller
from ui.main_window import MainWindow
from ui.views import FunctionalExercisesView


class SignalStub:
    def __init__(self):
        self.callback = None

    def connect(self, callback):
        self.callback = callback


class ViewSpy:
    def __init__(self):
        self.exercise_selected = SignalStub()
        self.open_assignment_requested = SignalStub()
        self.refresh_requested = SignalStub()
        self.items = ()
        self.details = None
        self.message = ""

    def clear(self):
        self.items = ()
        self.details = None

    def show_loading(self):
        self.message = "loading"

    def set_items(self, items):
        self.items = tuple(items)

    def select_exercise(self, identifier):
        self.selected = identifier
        return True

    def set_details(self, exercise, related):
        self.details = (exercise, related)

    def show_message(self, message):
        self.message = message

    def show_error(self, message):
        self.message = message


class AcceptedExerciseDialog:
    def __init__(self, assignments, parent=None):
        self.assignments = assignments

    def exec(self):
        return QDialog.DialogCode.Accepted

    def values(self):
        first = self.assignments[0]
        return {
            "person_id": first.person_id,
            "exercise_type_code": first.exercise_type_code,
            "exercise_type_label": first.exercise_type_label,
            "role": first.role,
            "context_organization": first.organization,
            "context_unit": first.unit,
            "context_reference": first.administrative_reference,
            "start_date": date(2024, 1, 1),
            "end_date": None,
        }


class InvalidPeriodDialog(AcceptedExerciseDialog):
    def values(self):
        values = super().values()
        values["end_date"] = date(2023, 12, 31)
        return values


class FunctionalExercisePresentationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.temporary_directory = TemporaryDirectory()
        self.addCleanup(self.temporary_directory.cleanup)
        root = Path(self.temporary_directory.name)
        self.project = ProjectManager().create_project(
            "Projeto RSC", root, application_id="rsc"
        )
        self.factory = ProjectSessionFactory(
            ApplicationRegistry([RscApplication()])
        )
        self.session = self.factory.create(self.project)
        source = root / "fonte.pdf"
        source.write_bytes(b"%PDF-fonte")
        document = (
            self.session.document_import_service.import_file(source).document
        )
        self.evidence = self.session.evidence_service.create(
            CreateEvidenceRequest(
                document_identity=document.sha256,
                page_number=3,
                title="Portaria",
                source_snippet="designado para atuar",
            )
        )
        self.assignments = tuple(
            self.session.rsc_session
            .create_functional_assignment_evidence_service.execute(
                CreateFunctionalAssignmentEvidenceCommand(
                    person_id="person-1",
                    source_evidence_reference=self.evidence.id,
                    exercise_type_code="comissao",
                    exercise_type_label="Comissão",
                    role=f"Membro {index}",
                    organization="Universidade",
                    start_date=date(2024, 1, 1),
                )
            )
            for index in range(2)
        )
        assignment_repository = (
            self.session.rsc_session
            .functional_assignment_evidence_repository
        )
        for assignment in self.assignments:
            domain_assignment = assignment_repository.get_by_id(
                FunctionalAssignmentEvidenceId.from_string(assignment.id)
            )
            assignment_repository.update(
                domain_assignment.mark_identified().mark_linked()
            )

    def test_creates_from_multiple_assignments_lists_and_traces_source(self):
        view = ViewSpy()
        navigated = []
        controller = FunctionalExercisesController(
            view,
            dialog_factory=AcceptedExerciseDialog,
            assignment_navigation_requested=lambda identifier: (
                navigated.append(identifier) or True
            ),
        )
        controller.set_session(self.session)

        self.assertTrue(
            controller.create(tuple(item.id for item in self.assignments))
        )
        self.assertEqual(len(view.items), 1)
        self.assertEqual(
            view.items[0].functional_assignment_evidence_ids,
            tuple(item.id for item in self.assignments),
        )
        exercise, related = view.details
        self.assertEqual(exercise.status, "active")
        self.assertEqual(len(related), 2)
        self.assertEqual(related[0][1].page_number, 3)
        self.assertEqual(
            related[0][1].source_snippet, "designado para atuar"
        )
        self.assertTrue(controller.open_assignment(related[0][0].id))
        self.assertEqual(navigated, [related[0][0].id])

    def test_requires_selection_and_rejects_duplicate_reference(self):
        view = ViewSpy()
        notifications = []
        controller = FunctionalExercisesController(
            view,
            dialog_factory=AcceptedExerciseDialog,
            notify=lambda kind, message: notifications.append(
                (kind, message)
            ),
        )
        controller.set_session(self.session)
        self.assertFalse(controller.create(()))
        self.assertIn("Selecione", view.message)
        self.assertFalse(controller.create(
            (self.assignments[0].id, self.assignments[0].id)
        ))
        self.assertEqual(notifications[-1][0], "error")

    def test_period_validation_is_reported_without_persistence(self):
        view = ViewSpy()
        notifications = []
        controller = FunctionalExercisesController(
            view,
            dialog_factory=InvalidPeriodDialog,
            notify=lambda kind, message: notifications.append(
                (kind, message)
            ),
        )
        controller.set_session(self.session)
        self.assertFalse(controller.create((self.assignments[0].id,)))
        self.assertEqual(notifications[-1][0], "error")
        self.assertEqual(view.items, ())

    def test_sqlite_exercise_survives_reopening(self):
        controller = FunctionalExercisesController(
            ViewSpy(), dialog_factory=AcceptedExerciseDialog
        )
        controller.set_session(self.session)
        self.assertTrue(controller.create((self.assignments[0].id,)))

        reopened = self.factory.create(self.project)
        listed = (
            reopened.rsc_session
            .list_functional_exercises_service.execute()
        )
        self.assertEqual(len(listed), 1)
        self.assertEqual(
            listed[0].functional_assignment_evidence_ids,
            (self.assignments[0].id,),
        )

    def test_view_shows_document_page_snippet_and_removed_source(self):
        controller = FunctionalExercisesController(
            ViewSpy(), dialog_factory=AcceptedExerciseDialog
        )
        controller.set_session(self.session)
        controller.create((self.assignments[0].id,))
        exercise = controller.view.items[0]
        view = FunctionalExercisesView()
        self.addCleanup(view.close)
        view.set_items((exercise,))
        view.set_details(
            exercise, ((self.assignments[0], self.evidence),)
        )
        text = view.related_list.item(0).text()
        self.assertIn("página 3", text)
        self.assertIn("designado para atuar", text)
        view.set_details(exercise, ((self.assignments[0], None),))
        self.assertIn(
            "indisponível", view.related_list.item(0).text()
        )

    def test_actions_are_exposed_only_for_rsc_projects(self):
        window = MainWindow()
        self.addCleanup(window.close)
        lifecycle_host = ApplicationLifecycleHost()
        controller = ProjectController(
            window,
            ProjectManager(),
            ProjectState(lifecycle_host),
            DesktopContributionInstaller(window),
            session_factory=self.factory,
            application_registry=ApplicationRegistry([RscApplication()]),
            lifecycle_host=lifecycle_host,
        )
        common = ProjectManager().create_project(
            "Comum", Path(self.temporary_directory.name)
        )
        controller._load_project(common)
        self.assertFalse(window.action_functional_exercises.isVisible())
        controller._load_project(self.project)
        self.assertTrue(window.action_functional_exercises.isVisible())


if __name__ == "__main__":
    unittest.main()
