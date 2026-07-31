from dataclasses import replace
import unittest

from presentation.coverage import CoverageFinding, CoverageInput, CoverageScope, CoverageState
from presentation.coverage_analyzer import CoverageAnalyzer
from presentation.coverage_insights import CoverageFindingInsightProvider
from presentation.perspectives import PerspectiveId
from presentation.resources import ResourceIdentity, ResourceType
from presentation.workspace import WorkspaceSnapshot, WorkspaceState
from presentation.workspace_insights import WorkspaceInsightService
from applications.rsc.services.review_workspace_service import ReviewOrigin, ReviewWorkspaceService


class CoverageFindingInsightProviderTests(unittest.TestCase):
    def test_projects_only_visual_attention_findings_with_stable_identity(self):
        result = CoverageAnalyzer().analyze(CoverageInput("project", 1))
        informational = CoverageFinding(
            CoverageScope.EVIDENCE,
            ResourceIdentity(ResourceType.EVIDENCE, "evidence-ok"),
            CoverageState.PARTIAL, 1, 2, "Observação estrutural.",
            ("EVIDENCE_PARTIAL_INFORMATION",),
        )
        result = replace(result, findings=(informational,))
        workspace = WorkspaceSnapshot(
            WorkspaceState.READY, PerspectiveId("review"), 3,
            project_id="project",
        )
        provider = CoverageFindingInsightProvider(result)
        self.assertEqual(provider.provide(workspace), ())

    def test_identity_is_deterministic_for_attention_finding(self):
        finding = CoverageFinding(
            CoverageScope.DOCUMENT,
            ResourceIdentity(ResourceType.DOCUMENT, "document-1"),
            CoverageState.ABSENT, 0, 1, "Sem Evidence.",
            ("DOCUMENT_WITHOUT_EVIDENCE",),
        )
        result = replace(
            CoverageAnalyzer().analyze(CoverageInput("project", 1)),
            findings=(finding,),
        )
        workspace = WorkspaceSnapshot(
            WorkspaceState.READY, PerspectiveId("review"), 3,
            project_id="project",
        )
        provider = CoverageFindingInsightProvider(result)
        self.assertEqual(
            provider.provide(workspace)[0].identity,
            provider.provide(workspace)[0].identity,
        )
        insights = WorkspaceInsightService((provider,)).collect(workspace)
        review = ReviewWorkspaceService().compose(workspace, result, insights)
        self.assertEqual(len(review.items), 1)
        self.assertEqual(review.items[0].origin, ReviewOrigin.COVERAGE)


if __name__ == "__main__":
    unittest.main()
