from types import SimpleNamespace
import ast
from pathlib import Path
import unittest

from PySide6.QtWidgets import QApplication

from applications.rsc.operational_actions import ExecuteEvaluationAction
from applications.rsc.review_workspace_view_model import ReviewWorkspaceViewModel
from applications.rsc.services.project_explorer_service import ProjectExplorerApplicationService
from applications.rsc.services.review_workspace_service import ReviewWorkspaceService
from applications.rsc.services.workspace_dashboard_service import WorkspaceDashboardService
from applications.rsc.workspace_dashboard_view_model import WorkspaceDashboardViewModel
from presentation.coverage import CoverageInput
from presentation.coverage_analyzer import CoverageAnalyzer
from presentation.insights import (
    Insight, InsightAction, InsightCategory, InsightCollection,
    InsightIdentity, InsightResourceReference, InsightResourceRole,
    InsightSeverity,
)
from presentation.resources import ResourceIdentity, ResourceType
from presentation import (
    NavigationIntent,
    PerspectiveDefinition,
    PerspectiveId,
)
from ui.main_window import MainWindow
from ui.review_workspace import ReviewWorkspaceView
from ui.workspace_dashboard import WorkspaceDashboardView


class PresentationIntegrationStabilizationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.window = MainWindow()
        self.workspace = self.window.workspace_store.snapshot
        self.coverage = CoverageAnalyzer().analyze(CoverageInput("project", 1))

    def tearDown(self):
        self.window.close()
        self.window.deleteLater()

    def _evidence_insights(self):
        identity = ResourceIdentity(ResourceType.EVIDENCE, "evidence-1")
        insight = Insight(
            InsightIdentity("test", "evidence.attention", "evidence-1"),
            InsightCategory.INFORMATION, InsightSeverity.INFO,
            "Evidence", "Revisar Evidence.", "Condição de teste.",
            (InsightResourceReference(identity, InsightResourceRole.SUBJECT),),
            (InsightAction.OPEN_RESOURCE,), self.workspace.revision,
        )
        return InsightCollection((insight,), 1, self.workspace.revision)

    def test_review_navigation_updates_workspace_history_and_inspector(self):
        snapshot = ReviewWorkspaceService().compose(
            self.workspace, self.coverage, self._evidence_insights()
        )
        view = ReviewWorkspaceView(ReviewWorkspaceViewModel(snapshot).data)
        view.navigation_requested.connect(self.window.navigation_controller.navigate)
        before = self.window.workspace_store.snapshot.revision
        view.items_list.setCurrentRow(0)
        view.open_button.click()
        self.app.processEvents()

        current = self.window.workspace_store.snapshot
        self.assertGreater(current.revision, before)
        self.assertEqual(current.current_evidence, "evidence-1")
        self.assertEqual(self.window.navigation_controller.history[-1].intent.target_id, "evidence-1")
        self.assertEqual(self.window.resource_inspector.data.resource_id, "evidence-1")

    def test_dashboard_uses_same_official_navigation_flow(self):
        snapshot = WorkspaceDashboardService().summarize(
            self.workspace, self.coverage, self._evidence_insights()
        )
        view = WorkspaceDashboardView(WorkspaceDashboardViewModel(snapshot).dashboard)
        view.navigation_requested.connect(self.window.navigation_controller.navigate)
        view.priority_list.setCurrentRow(0)
        view.action_button.click()
        self.app.processEvents()
        self.assertEqual(self.window.workspace_store.snapshot.current_evidence, "evidence-1")
        self.assertEqual(self.window.resource_inspector.data.resource_id, "evidence-1")

    def test_execution_fact_navigation_is_explicitly_unavailable_in_inspector(self):
        self.window.navigation_controller.navigate(
            NavigationIntent.open_execution_fact("fact-1")
        )
        self.app.processEvents()
        self.assertEqual(self.window.resource_inspector.data.state.value, "unavailable")
        self.assertEqual(self.window.resource_inspector.data.resource_type, "execution_fact")
        self.assertEqual(self.window.resource_inspector.data.resource_id, "fact-1")

    def test_review_filters_live_in_workspace_and_are_consumed(self):
        self.window.perspective_store.register(PerspectiveDefinition(
            PerspectiveId("review_workspace"),
            "Review Workspace",
            100,
            None,
            False,
            lambda: self.window.home_view,
        ))
        snapshot = ReviewWorkspaceService().compose(
            self.workspace, self.coverage, self._evidence_insights()
        )
        view = ReviewWorkspaceView(ReviewWorkspaceViewModel(snapshot).data)
        view.navigation_requested.connect(self.window.navigation_controller.navigate)
        view.category_filter.setCurrentIndex(2)  # evidences
        before = self.window.workspace_store.snapshot.revision
        view.apply_filters_button.click()
        current = self.window.workspace_store.snapshot
        self.assertGreater(current.revision, before)
        self.assertEqual(current.active_filters[0].filter_id, "review.category")
        projected = ReviewWorkspaceService().compose(
            current, self.coverage,
            InsightCollection(self._evidence_insights().insights, 1, current.revision),
        )
        self.assertEqual(len(projected.items), 1)

    def test_execute_evaluation_is_not_navigation(self):
        insight = Insight(
            InsightIdentity("project_evaluation", "project.not_evaluated", "project"),
            InsightCategory.COMPLETENESS, InsightSeverity.WARNING,
            "Avaliação", "Projeto ainda não avaliado.", "Sem avaliação.",
            (), (InsightAction.EXECUTE_EVALUATION,), self.workspace.revision,
        )
        snapshot = WorkspaceDashboardService().summarize(
            self.workspace, self.coverage,
            InsightCollection((insight,), 1, self.workspace.revision),
        )
        view = WorkspaceDashboardView(WorkspaceDashboardViewModel(snapshot).dashboard)
        operations, navigations = [], []
        view.operational_requested.connect(operations.append)
        view.navigation_requested.connect(navigations.append)
        view.priority_list.setCurrentRow(0)
        view.action_button.click()
        self.assertEqual(operations, [ExecuteEvaluationAction("project")])
        self.assertEqual(navigations, [])

    def test_requirement_and_criterion_states_are_projected_literally(self):
        process = SimpleNamespace(
            process_id="evaluation", revision=7, result=None,
            requirement_scores=(SimpleNamespace(
                requirement_id="REQ-1",
                aggregation_trace=SimpleNamespace(operation="DECIMAL_SUM_EXECUTED_ONLY"),
            ),),
            criterion_scores=(SimpleNamespace(criterion_id="CRIT-1", scoring_state=SimpleNamespace(value="EXECUTED")),),
            execution_facts=(), validations=(), compatibilities=(),
        )
        evaluation = ProjectExplorerApplicationService._coverage_evaluation(process)
        result = CoverageAnalyzer().analyze(CoverageInput("project", 1, evaluation=evaluation))
        self.assertEqual(result.normative_coverage.requirements_total, 1)
        self.assertEqual(result.normative_coverage.criteria_total, 1)
        self.assertEqual(result.normative_coverage.requirement_states[0].state, "DECIMAL_SUM_EXECUTED_ONLY")
        self.assertEqual(result.normative_coverage.criterion_states[0].state, "EXECUTED")

    def test_project_explorer_has_no_parallel_navigation_or_filter_authority(self):
        tree = ast.parse(Path("ui/project_explorer.py").read_text(encoding="utf-8"))
        names = {node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)}
        attributes = {node.attr for node in ast.walk(tree) if isinstance(node, ast.Attribute)}
        self.assertNotIn("_handle_dashboard_action", names)
        self.assertNotIn("_review_filters", attributes)

    def test_review_does_not_call_dashboard_to_obtain_sources(self):
        tree = ast.parse(Path("applications/rsc/services/project_explorer_service.py").read_text(encoding="utf-8"))
        review = next(node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef) and node.name == "review_snapshot")
        calls = {node.attr for node in ast.walk(review) if isinstance(node, ast.Attribute)}
        self.assertNotIn("dashboard_snapshot", calls)


if __name__ == "__main__":
    unittest.main()
