import os
from datetime import date
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication, QDialog

from applications import RscApplication
from applications.rsc.commands import (
    CreateFunctionalAssignmentEvidenceCommand,
    CreateFunctionalExerciseCommand,
)
from applications.rsc.models import FunctionalAssignmentEvidenceId
from core.application_registry import ApplicationRegistry
from core.project_manager import ProjectManager
from core.project_session_factory import ProjectSessionFactory
from models import CreateEvidenceRequest
from presentation.activities import ActivitiesController
from ui.views import ActivitiesView


class AcceptedActivityDialog:
    def __init__(self, exercise_count, parent=None):
        self.exercise_count = exercise_count

    def exec(self):
        return QDialog.DialogCode.Accepted

    def values(self):
        return {"description": "Participação em comissão"}


class FunctionalActivityFlowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.temporary_directory = TemporaryDirectory()
        self.addCleanup(self.temporary_directory.cleanup)
        root = Path(self.temporary_directory.name)
        self.project = ProjectManager().create_project(
            "RSC", root, application_id="rsc"
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
                page_number=4,
                title="Portaria",
                source_snippet="participação na comissão",
            )
        )
        self.assignments = []
        self.exercises = []
        for index in range(2):
            assignment = (
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
            )
            self.assignments.append(assignment)
            assignment_repository = (
                self.session.rsc_session
                .functional_assignment_evidence_repository
            )
            assignment_domain = assignment_repository.get_by_id(
                FunctionalAssignmentEvidenceId.from_string(assignment.id)
            )
            assignment_repository.update(
                assignment_domain.mark_identified().mark_linked()
            )
            self.exercises.append(
                self.session.rsc_session
                .create_functional_exercise_service.execute(
                    CreateFunctionalExerciseCommand(
                        person_id="person-1",
                        exercise_type_code="comissao",
                        exercise_type_label="Comissão",
                        role=f"Membro {index}",
                        context_organization="Universidade",
                        start_date=date(2024, 1, 1),
                        functional_assignment_evidence_ids=(
                            assignment.id,
                        ),
                    )
                )
            )

    def test_creates_activity_from_multiple_exercises_and_traces_document(self):
        view = ActivitiesView()
        self.addCleanup(view.close)
        navigated = []
        controller = ActivitiesController(
            view,
            dialog_factory=AcceptedActivityDialog,
            assignment_navigation_requested=lambda identifier: (
                navigated.append(identifier) or True
            ),
        )
        controller.set_session(self.session)

        self.assertTrue(controller.create(
            tuple(item.id for item in self.exercises)
        ))
        activity = (
            self.session.rsc_session.activity_repository.list_all()[0]
        )
        self.assertEqual(activity.state.value, "lembrada")
        self.assertEqual(
            tuple(str(item) for item in activity.functional_exercise_ids),
            tuple(item.id for item in self.exercises),
        )
        details = controller._service.build().selected_activity
        self.assertEqual(len(details.related_interpretations), 2)
        trace = details.related_interpretations[0]
        self.assertEqual(trace.evidence_id, self.evidence.id)
        self.assertEqual(trace.page_number, 4)
        self.assertEqual(trace.snippet, "participação na comissão")
        self.assertTrue(controller.open_assignment(trace.assignment_id))
        self.assertEqual(navigated, [trace.assignment_id])

    def test_activity_survives_project_reopening_with_relations(self):
        controller = ActivitiesController(
            ActivitiesView(), dialog_factory=AcceptedActivityDialog
        )
        self.addCleanup(controller.view.close)
        controller.set_session(self.session)
        self.assertTrue(controller.create((self.exercises[0].id,)))

        reopened = self.factory.create(self.project)
        activity = reopened.rsc_session.activity_repository.list_all()[0]
        self.assertEqual(
            tuple(str(item) for item in activity.functional_exercise_ids),
            (self.exercises[0].id,),
        )

    def test_rejects_activity_directly_from_interpretations(self):
        controller = ActivitiesController(
            ActivitiesView(), dialog_factory=AcceptedActivityDialog
        )
        self.addCleanup(controller.view.close)
        controller.set_session(self.session)
        self.assertFalse(controller.create(
            assignment_ids=tuple(item.id for item in self.assignments)
        ))
        self.assertEqual(
            self.session.rsc_session.activity_repository.list_all(),
            (),
        )

    def test_common_project_has_no_activity_creation_flow(self):
        common = ProjectManager().create_project(
            "Comum", Path(self.temporary_directory.name)
        )
        session = ProjectSessionFactory().create(common)
        view = ActivitiesView()
        self.addCleanup(view.close)
        controller = ActivitiesController(
            view, dialog_factory=AcceptedActivityDialog
        )
        self.assertFalse(controller.set_session(session))
        self.assertFalse(controller.create((self.exercises[0].id,)))

    def test_removed_evidence_is_presented_as_unavailable(self):
        controller = ActivitiesController(
            ActivitiesView(), dialog_factory=AcceptedActivityDialog
        )
        self.addCleanup(controller.view.close)
        controller.set_session(self.session)
        controller.create((self.exercises[0].id,))
        self.session.evidence_service.delete(self.evidence.id)
        self.assertTrue(controller.refresh())
        item = (
            controller._service.build()
            .selected_activity.related_interpretations[0]
        )
        self.assertFalse(item.source_available)
        self.assertFalse(item.evidence_available)
        self.assertIn("Evidence", item.unavailable_reason)

    def test_removed_document_keeps_evidence_and_historical_trace_visible(self):
        controller = ActivitiesController(
            ActivitiesView(), dialog_factory=AcceptedActivityDialog
        )
        self.addCleanup(controller.view.close)
        controller.set_session(self.session)
        controller.create((self.exercises[0].id,))
        document = self.session.document_repository.find_by_hash(
            self.evidence.document_identity
        )
        self.assertTrue(
            self.session.document_import_service.remove(document.id)
        )

        reopened = self.factory.create(self.project)
        reopened_controller = ActivitiesController(ActivitiesView())
        self.addCleanup(reopened_controller.view.close)
        self.assertTrue(reopened_controller.set_session(reopened))
        details = (
            reopened_controller._service.build().selected_activity
        )
        trace = details.related_interpretations[0]
        self.assertTrue(trace.evidence_available)
        self.assertFalse(trace.document_available)
        self.assertEqual(trace.evidence_id, self.evidence.id)
        self.assertIn("Documento de origem", trace.unavailable_reason)
        row = reopened_controller.view.related_list.item(0)
        self.assertIn(self.evidence.id, row.text())
        self.assertIn("não está mais disponível", row.text())


if __name__ == "__main__":
    unittest.main()
