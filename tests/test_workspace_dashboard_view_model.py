from dataclasses import FrozenInstanceError
import unittest

from applications.rsc.services.workspace_dashboard_service import WorkspaceDashboardService
from applications.rsc.workspace_dashboard_view_model import WorkspaceDashboardViewModel
from presentation.coverage import CoverageInput, ExecutionFactCoverageReference
from presentation.coverage_analyzer import CoverageAnalyzer
from presentation.insights import InsightCollection
from presentation.coverage_insights import CoverageFindingInsightProvider
from presentation.workspace_insights import WorkspaceInsightService
from presentation.perspectives import PerspectiveId
from presentation.resources import ResourceIdentity, ResourceType
from presentation.workspace import WorkspaceSnapshot, WorkspaceState


class WorkspaceDashboardViewModelTests(unittest.TestCase):
    def test_projects_coverage_insights_actions_and_empty_states(self):
        evidence = ResourceIdentity(ResourceType.EVIDENCE, "ev")
        fact = ResourceIdentity(ResourceType.EXECUTION_FACT, "fact")
        workspace = WorkspaceSnapshot(WorkspaceState.READY, PerspectiveId("dashboard"), 1,
                                      project_id="project", metadata={"project_name": "Processo"})
        coverage = CoverageAnalyzer().analyze(CoverageInput("project", 1, execution_facts=(ExecutionFactCoverageReference(fact, evidence),)))
        insights = WorkspaceInsightService((CoverageFindingInsightProvider(coverage),)).collect(workspace)
        snapshot = WorkspaceDashboardService().summarize(workspace, coverage, insights)
        data = WorkspaceDashboardViewModel(snapshot).dashboard
        self.assertEqual(data.summary.project_name, "Processo")
        self.assertEqual(data.document_status.pending_execution_facts, 1)
        self.assertTrue(data.priority_actions)
        self.assertTrue(any(item.intent is not None for item in data.priority_actions))
        with self.assertRaises(FrozenInstanceError):
            data.empty_message = "x"  # type: ignore[misc]


if __name__ == "__main__":
    unittest.main()
