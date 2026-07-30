import os
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication, QDialog

from applications import RscApplication
from core.application_registry import ApplicationRegistry
from core.project_manager import ProjectManager
from core.project_controller import ProjectController
from core.project_state import ProjectState
from core.project_session_factory import ProjectSessionFactory
from models import CreateEvidenceRequest
from presentation.functional_assignments import (
    FunctionalAssignmentsController,
)
from ui.dialogs import FunctionalAssignmentDialog
from ui.contribution_installer import DesktopContributionInstaller
from ui.main_window import MainWindow
from ui.views import EvidenceWorkspace, FunctionalAssignmentsView


class SignalStub:
    def __init__(self):
        self.callback = None

    def connect(self, callback):
        self.callback = callback


class ViewSpy:
    def __init__(self):
        self.assignment_selected = SignalStub()
        self.open_source_requested = SignalStub()
        self.refresh_requested = SignalStub()
        self.items = ()
        self.details = None
        self.selected = None
        self.message = ""

    def clear(self):
        self.items = ()
        self.details = None

    def set_items(self, items):
        self.items = tuple(items)

    def set_details(self, assignment, evidence, project):
        self.details = (assignment, evidence, project)

    def select_assignment(self, identifier):
        self.selected = identifier
        return True

    def show_message(self, message):
        self.message = message

    def show_error(self, message):
        self.message = message


class AcceptedDialog:
    def __init__(self, evidence, parent=None):
        self.evidence = evidence

    def exec(self):
        return QDialog.DialogCode.Accepted

    def values(self):
        return {
            "person_id": "person-1",
            "exercise_type_code": "comissao",
            "exercise_type_label": " Participação em comissão ",
            "role": " Membro ",
            "organization": " Universidade ",
            "unit": " Reitoria ",
            "administrative_reference": None,
            "start_date": "2024-01-01",
            "end_date": "",
        }


class FunctionalAssignmentPresentationTests(unittest.TestCase):
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
                page_number=2,
                title="Designação",
                source_snippet="designar o servidor",
            )
        )

    def test_controller_creates_lists_traces_and_navigates_to_source(self):
        view = ViewSpy()
        navigated = []
        controller = FunctionalAssignmentsController(
            view,
            dialog_factory=AcceptedDialog,
            evidence_navigation_requested=lambda identifier: (
                navigated.append(identifier) or True
            ),
        )
        controller.set_session(self.session)

        self.assertTrue(controller.create_from_evidence(self.evidence))

        self.assertEqual(len(view.items), 1)
        created = view.items[0]
        self.assertEqual(created.status, "raw")
        self.assertEqual(created.role, "Membro")
        self.assertEqual(
            created.source_evidence_reference, self.evidence.id
        )
        self.assertEqual(view.details[1], self.evidence)
        self.assertEqual(view.details[2], "Projeto RSC")
        self.assertTrue(controller.open_source())
        self.assertEqual(navigated, [self.evidence.id])

    def test_assignment_survives_project_reopening(self):
        controller = FunctionalAssignmentsController(
            ViewSpy(), dialog_factory=AcceptedDialog
        )
        controller.set_session(self.session)
        self.assertTrue(controller.create_from_evidence(self.evidence))

        reopened = self.factory.create(self.project)
        items = (
            reopened.rsc_session
            .list_functional_assignment_evidences_service.execute()
        )

        self.assertEqual(len(items), 1)
        self.assertEqual(
            items[0].source_evidence_reference, self.evidence.id
        )

    def test_common_project_has_no_rsc_session_or_available_action(self):
        common = ProjectManager().create_project(
            "Comum", Path(self.temporary_directory.name)
        )
        session = ProjectSessionFactory().create(common)
        workspace = EvidenceWorkspace()
        self.addCleanup(workspace.close)

        workspace.set_functional_interpretation_available(
            session.rsc_session is not None
        )

        self.assertIsNone(session.rsc_session)
        self.assertTrue(workspace.interpret_button.isHidden())

    def test_real_composition_shows_action_only_for_rsc_project(self):
        window = MainWindow()
        self.addCleanup(window.close)
        state = ProjectState()
        controller = ProjectController(
            window,
            ProjectManager(),
            state,
            DesktopContributionInstaller(window),
            session_factory=self.factory,
            application_registry=ApplicationRegistry([RscApplication()]),
        )
        common = ProjectManager().create_project(
            "Comum UI", Path(self.temporary_directory.name)
        )

        controller._load_project(common)
        self.assertFalse(
            window.action_functional_assignments.isVisible()
        )
        self.assertTrue(window.evidence_workspace.interpret_button.isHidden())

        controller._load_project(self.project)
        self.assertTrue(
            window.action_functional_assignments.isVisible()
        )
        window.show()
        self.app.processEvents()
        self.assertFalse(
            window.evidence_workspace.interpret_button.isHidden()
        )

    def test_dialog_requires_domain_required_fields_and_valid_iso_dates(self):
        dialog = FunctionalAssignmentDialog(self.evidence)
        self.addCleanup(dialog.close)
        ok = dialog.buttons.button(dialog.buttons.StandardButton.Ok)
        self.assertFalse(ok.isEnabled())
        for name in (
            "person_id", "exercise_type_code", "exercise_type_label",
            "role", "organization",
        ):
            dialog.fields[name].setText("valor")
        self.assertTrue(ok.isEnabled())
        dialog.fields["start_date"].setText("31/12/2024")
        self.assertFalse(ok.isEnabled())
        dialog.fields["start_date"].setText("2024-12-31")
        self.assertTrue(ok.isEnabled())

    def test_view_renders_traceability_and_emits_source_navigation(self):
        view = FunctionalAssignmentsView()
        self.addCleanup(view.close)
        controller = FunctionalAssignmentsController(
            view, dialog_factory=AcceptedDialog
        )
        controller.set_session(self.session)
        controller.create_from_evidence(self.evidence)

        self.assertEqual(view.list_widget.count(), 1)
        self.assertEqual(
            view.details["source"].text(), self.evidence.id
        )
        self.assertEqual(view.details["page"].text(), "2")
        self.assertEqual(
            view.details["snippet"].text(), "designar o servidor"
        )
        self.assertEqual(
            view.details["created"].text(),
            "Não registrada pelo modelo atual",
        )


if __name__ == "__main__":
    unittest.main()
