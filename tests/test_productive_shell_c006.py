import os
from decimal import Decimal
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from platform_sdk import Document
from models import Document as CanonicalDocument
from presentation import (
    ApplicationState,
    NavigationIntent,
    NavigationIntentType,
    PerspectiveId,
    ResourceInspectorState,
    WorkspaceFilter,
)
from core.application import Application
from ui.evaluation_report_view import EvaluationReportView
from ui.results_view import ResultsView


class ProductiveShellC006Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = TemporaryDirectory()
        root = Path(self.temporary_directory.name)
        self.application = Application(
            productive_database_path=root / "projects.sqlite",
            productive_workspace_base=root / "workspaces",
        )
        self.window = self.application.main_window
        self.explorer = self.application.productive_workspace

    def tearDown(self) -> None:
        if self.application.lifecycle_host.current_session is not None:
            self.application.project_controller.close_project()
        self.window.close()
        self.application.app.processEvents()
        self.temporary_directory.cleanup()

    def _create_project(self, name="Projeto produtivo"):
        physical = self.application.project_manager.create_project(
            name, Path(self.temporary_directory.name), application_id="rsc"
        )
        self.application.project_controller._load_project(physical)
        self.application.project_controller._complete_project_open(
            physical, "Projeto criado."
        )
        return self.explorer.project

    def _attach_document(self, evidence, *, document_id, name):
        canonical = CanonicalDocument(
            id=document_id,
            name=name,
            original_filename=name,
            stored_filename=name,
            relative_path=f"documents/{name}",
            imported_at=CanonicalDocument.now(),
            created_at=CanonicalDocument.now(),
            updated_at=CanonicalDocument.now(),
            sha256="a" * 64,
        )
        self.application.lifecycle_host.current_session.document_repository.create(
            canonical
        )
        return self.explorer._service.attach_document(
            evidence.aggregate_id,
            project_id=self.explorer.project.aggregate_id,
            document=Document(
                document_id=document_id,
                name=name,
                relative_path=f"documents/{name}",
                document_type="application/pdf",
                sha256="a" * 64,
            ),
        )

    def _create_evaluatable_project(self):
        project = self._create_project()
        evidence = self.explorer.create_evidence(title="Ata")
        self._attach_document(
            evidence, document_id="ata-documento", name="ata.pdf"
        )
        fact = self.explorer.create_execution_fact(
            fact_type="PARTICIPACAO_EVENTO",
            description="Três participações",
            quantity=Decimal("3"),
            unit="Por evento",
        )
        self.explorer.create_binding(
            criterion_id="DEC13048-ANX-II-ITEM-07"
        )
        self.explorer._refresh_dashboard()
        return project, evidence, fact

    def test_application_composition_root_registers_productive_perspectives(self):
        registered = {
            item.id.value
            for item in self.window.perspective_store.list_all()
        }
        self.assertTrue({
            "workspace_dashboard",
            "review_workspace",
            "project_explorer",
            "results",
            "evaluation_report",
        }.issubset(registered))
        self.assertIs(
            self.window.productive_workspace,
            self.application.productive_workspace,
        )
        self.assertIsNotNone(self.window.resource_inspector)
        self.assertTrue(self.window.isWindow())
        self.assertFalse(self.explorer.isWindow())
        self.assertIs(self.explorer.parent(), self.window.workspace_host)

        for perspective in (
            "project_explorer",
            "workspace_dashboard",
            "review_workspace",
            "results",
            "evaluation_report",
        ):
            definition = self.window.perspective_store.get(
                PerspectiveId(perspective)
            )
            self.assertTrue(callable(definition.factory))

    def test_project_open_starts_dashboard_in_official_context(self):
        project = self._create_project()

        self.assertIs(
            self.window.application_state_store.snapshot.state,
            ApplicationState.PROJECT_OPEN,
        )
        self.assertEqual(
            self.window.workspace_store.snapshot.project_id,
            project.aggregate_id,
        )
        self.assertEqual(
            self.window.workspace_store.snapshot.active_perspective,
            PerspectiveId("workspace_dashboard"),
        )
        self.assertIs(
            self.window.workspace_host.active_widget, self.explorer
        )
        self.assertEqual(self.explorer.workspace_tabs.currentIndex(), 0)

    def test_review_explorer_inspector_and_history_flow(self):
        project = self._create_project()
        evidence = self.explorer.create_evidence(title="Portaria")
        self._attach_document(
            evidence,
            document_id="portaria-documento",
            name="portaria.pdf",
        )
        filter_ = WorkspaceFilter(
            "review.category", {"value": "documents"}
        )
        self.window.navigation_controller.navigate(NavigationIntent(
            NavigationIntentType.OPEN_PERSPECTIVE,
            "review_workspace",
            project_id=project.aggregate_id,
            filters=(filter_,),
            origin="c006-test",
        ))
        review_position = self.window.navigation_controller.history_position

        self.window.navigation_controller.navigate(
            NavigationIntent.open_document(
                "portaria-documento",
                project_id=project.aggregate_id,
                origin="review_workspace",
            )
        )

        self.assertEqual(
            self.window.workspace_store.snapshot.active_perspective,
            PerspectiveId("project_explorer"),
        )
        self.assertEqual(self.explorer.workspace_tabs.currentIndex(), 1)
        self.assertIs(
            self.window.resource_inspector.data.state,
            ResourceInspectorState.READY,
        )
        self.assertEqual(
            self.window.resource_inspector.data.resource_id,
            "portaria-documento",
        )

        history_size = len(self.window.navigation_controller.history)
        dashboard_before_restore = self.explorer._dashboard_view
        review_before_restore = self.explorer._review_view
        self.window.navigation_controller.go_back()
        self.assertEqual(
            self.window.workspace_store.snapshot.active_perspective,
            PerspectiveId("review_workspace"),
        )
        self.assertEqual(
            self.window.workspace_store.snapshot.active_filters, (filter_,)
        )
        self.assertEqual(
            self.window.navigation_controller.history_position,
            review_position,
        )
        self.assertEqual(
            len(self.window.navigation_controller.history), history_size
        )
        self.assertIsNot(
            self.explorer._dashboard_view, dashboard_before_restore
        )
        self.assertIsNot(self.explorer._review_view, review_before_restore)

        self.window.navigation_controller.go_forward()
        self.assertEqual(
            self.window.resource_inspector.data.resource_id,
            "portaria-documento",
        )
        self.assertEqual(
            len(self.window.navigation_controller.history), history_size
        )

        self.window.navigation_controller.go_back()
        self.window.navigation_controller.navigate(
            NavigationIntent.open_evidence(
                evidence.aggregate_id, project_id=project.aggregate_id
            )
        )
        self.assertFalse(self.window.navigation_controller.can_go_forward)
        self.assertEqual(
            self.window.resource_inspector.data.resource_id,
            evidence.aggregate_id,
        )

    def test_supported_resources_and_execution_fact_unavailable(self):
        project, evidence, fact = self._create_evaluatable_project()
        cases = (
            (
                NavigationIntent.open_evidence(evidence.aggregate_id),
                ResourceInspectorState.READY,
            ),
            (
                NavigationIntent.open_requirement(
                    "DEC13048-ANX-II-REQ-02"
                ),
                ResourceInspectorState.READY,
            ),
            (
                NavigationIntent.open_execution_fact(fact.aggregate_id),
                ResourceInspectorState.UNAVAILABLE,
            ),
        )
        for intent, expected in cases:
            with self.subTest(intent=intent.intent_type):
                self.window.navigation_controller.navigate(NavigationIntent(
                    intent.intent_type,
                    intent.target_id,
                    project_id=project.aggregate_id,
                ))
                self.assertIs(
                    self.window.resource_inspector.data.state, expected
                )

    def test_dashboard_evaluation_results_report_and_refresh(self):
        project, _evidence, _fact = self._create_evaluatable_project()
        self.window.navigation_controller.navigate(
            NavigationIntent.open_dashboard(project_id=project.aggregate_id)
        )
        action = next(
            item.operational_action
            for item in self.explorer._dashboard_view.dashboard.priority_actions
            if item.operational_action is not None
        )

        with (
            patch("ui.project_explorer.QMessageBox.information"),
            patch("ui.project_explorer.QMessageBox.warning"),
        ):
            self.explorer._dashboard_view.operational_requested.emit(action)

        self.assertIsNotNone(self.explorer.last_execution_result)
        self.assertNotEqual(
            self.explorer._dashboard_view.dashboard.summary.last_evaluation,
            "Ainda nao executada",
        )
        self.explorer.show_results()
        self.assertEqual(
            self.window.workspace_store.snapshot.active_perspective,
            PerspectiveId("results"),
        )
        self.assertIsInstance(
            self.explorer.workspace_tabs.widget(3), ResultsView
        )
        self.explorer.show_evaluation_report()
        self.assertEqual(
            self.window.workspace_store.snapshot.active_perspective,
            PerspectiveId("evaluation_report"),
        )
        self.assertIsInstance(
            self.explorer.workspace_tabs.widget(4), EvaluationReportView
        )

        self.window.navigation_controller.navigate(
            NavigationIntent.open_dashboard(project_id=project.aggregate_id)
        )
        self.window.navigation_controller.navigate_to(
            PerspectiveId("review_workspace")
        )
        self.assertEqual(self.explorer.workspace_tabs.currentIndex(), 2)

    def test_project_close_clears_history_and_keeps_explorer_available(self):
        self._create_project()
        self.window.navigation_controller.navigate_to(
            PerspectiveId("review_workspace")
        )

        self.application.project_controller.close_project()

        self.assertIs(
            self.window.application_state_store.snapshot.state,
            ApplicationState.NO_PROJECT,
        )
        self.assertEqual(self.window.navigation_controller.history, ())
        self.assertEqual(
            self.window.workspace_store.snapshot.active_perspective,
            PerspectiveId("project_explorer"),
        )
        self.assertFalse(self.window.action_back.isEnabled())
        self.assertFalse(self.window.action_forward.isEnabled())

    def test_project_switch_clears_previous_workspace_context(self):
        first = self._create_project()
        evidence = self.explorer.create_evidence(title="Primeiro Project")
        filter_ = WorkspaceFilter(
            "review.category", {"value": "evidences"}
        )
        self.window.navigation_controller.navigate(
            NavigationIntent.open_evidence(
                evidence.aggregate_id,
                project_id=first.aggregate_id,
                filters=(filter_,),
            )
        )

        second = self._create_project("Segundo Project")
        snapshot = self.window.workspace_store.snapshot

        self.assertEqual(snapshot.project_id, second.aggregate_id)
        self.assertEqual(snapshot.active_filters, ())
        self.assertIsNone(snapshot.selection.identity.identifier)
        self.assertIsNone(snapshot.current_document)
        self.assertIsNone(snapshot.current_evidence)
        self.assertIsNone(snapshot.current_execution_fact)
        self.assertIsNone(snapshot.current_requirement)
        self.assertIsNone(snapshot.current_criterion)
        self.assertIsNone(snapshot.current_evaluation)
        self.assertIs(
            self.window.resource_inspector.data.state,
            ResourceInspectorState.EMPTY,
        )
        self.assertEqual(len(self.window.navigation_controller.history), 1)
        self.assertEqual(
            self.window.workspace_store.snapshot.active_perspective,
            PerspectiveId("workspace_dashboard"),
        )

    def test_review_filter_stays_in_review_and_restores_controls(self):
        self._create_project()
        self.window.navigation_controller.navigate_to(
            PerspectiveId("review_workspace")
        )
        review = self.explorer._review_view
        documents_index = review.category_filter.findText("documents")
        review.category_filter.setCurrentIndex(documents_index)

        review.apply_filters_button.click()
        filtered = self.explorer._review_view

        self.assertEqual(
            self.window.workspace_store.snapshot.active_perspective,
            PerspectiveId("review_workspace"),
        )
        self.assertEqual(
            self.window.workspace_store.snapshot.active_filters[0].filter_id,
            "review.category",
        )
        self.assertEqual(
            filtered.category_filter.currentText(), "documents"
        )


if __name__ == "__main__":
    unittest.main()
