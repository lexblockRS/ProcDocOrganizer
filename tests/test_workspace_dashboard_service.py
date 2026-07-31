from dataclasses import FrozenInstanceError
import unittest

from applications.rsc.services.workspace_dashboard_service import WorkspaceDashboardService
from presentation.coverage import CoverageInput, EvidenceCoverageReference
from presentation.coverage_analyzer import CoverageAnalyzer
from presentation.insights import InsightCollection
from presentation.workspace_insights import ProjectEvaluationInsightProvider, WorkspaceInsightService
from presentation.perspectives import PerspectiveId
from presentation.resources import ResourceIdentity, ResourceType
from presentation.workspace import WorkspaceSnapshot, WorkspaceState


def workspace(evaluation=None):
    return WorkspaceSnapshot(WorkspaceState.READY, PerspectiveId("dashboard"), 3,
                             project_id="project-1", current_evaluation=evaluation,
                             metadata={"project_name": "Processo"})


class WorkspaceDashboardServiceTests(unittest.TestCase):
    def test_composes_official_coverage_and_insights(self):
        evidence = ResourceIdentity(ResourceType.EVIDENCE, "ev-1")
        coverage = CoverageAnalyzer().analyze(CoverageInput("project-1", 2, evidences=(EvidenceCoverageReference(evidence),)))
        current = workspace()
        insights = WorkspaceInsightService((ProjectEvaluationInsightProvider(),)).collect(current)
        result = WorkspaceDashboardService().summarize(current, coverage, insights)
        self.assertEqual(result.coverage.evidence_coverage.without_documents, 1)
        self.assertEqual(result.insights.workspace_revision, 3)
        self.assertTrue(any(item.message == "Projeto ainda não avaliado." for item in result.insights.insights))
        with self.assertRaises(FrozenInstanceError):
            result.workspace = workspace()  # type: ignore[misc]

    def test_rejects_non_contract_inputs(self):
        with self.assertRaises(TypeError):
            WorkspaceDashboardService().summarize(object(), object(), object())


if __name__ == "__main__":
    unittest.main()
