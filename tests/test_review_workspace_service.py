from dataclasses import FrozenInstanceError
import ast
from pathlib import Path
import unittest

from applications.rsc.services.review_workspace_service import (
    ReviewCategory, ReviewOrigin, ReviewState,
    ReviewWorkspaceService,
)
from presentation.coverage import CoverageInput, EvidenceCoverageReference
from presentation.coverage_analyzer import CoverageAnalyzer
from presentation.insights import (
    Insight, InsightCategory, InsightCollection, InsightIdentity,
    InsightResourceReference, InsightResourceRole, InsightSeverity,
)
from presentation.perspectives import PerspectiveId
from presentation.resources import ResourceIdentity, ResourceType
from presentation.workspace import WorkspaceSnapshot, WorkspaceState
from presentation.navigation_contracts import WorkspaceFilter


def sources(filters=()):
    workspace = WorkspaceSnapshot(WorkspaceState.READY, PerspectiveId("review"), 4,
                                  project_id="project", active_filters=filters,
                                  metadata={"project_name": "Processo"})
    evidence = ResourceIdentity(ResourceType.EVIDENCE, "ev-1")
    coverage = CoverageAnalyzer().analyze(CoverageInput(
        "project", 2, evidences=(EvidenceCoverageReference(evidence),)
    ))
    insight = Insight(InsightIdentity("provider", "attention", "ev-1"), InsightCategory.INFORMATION,
                      InsightSeverity.INFO, "Informacao", "Mensagem", "Explicacao",
                      (InsightResourceReference(evidence, InsightResourceRole.SUBJECT),), (), 4)
    return workspace, coverage, InsightCollection((insight,), 1, 4)


class ReviewWorkspaceServiceTests(unittest.TestCase):
    def test_composes_both_sources_with_deterministic_priority(self):
        snapshot = ReviewWorkspaceService().compose(*sources())
        self.assertEqual(snapshot.workspace_revision, 4)
        self.assertEqual({item.origin for item in snapshot.items}, {ReviewOrigin.INSIGHT})
        self.assertEqual(snapshot.items[0].severity, InsightSeverity.INFO)
        self.assertIsNotNone(snapshot.items[0].navigation_intent)
        with self.assertRaises(FrozenInstanceError):
            snapshot.state = ReviewState.READY  # type: ignore[misc]

    def test_filters_belong_to_snapshot(self):
        filters = (
            WorkspaceFilter("review.category", {"value": ReviewCategory.EVIDENCES.value}),
            WorkspaceFilter("review.severity", {"value": InsightSeverity.INFO.value}),
            WorkspaceFilter("review.origin", {"value": ReviewOrigin.INSIGHT.value}),
        )
        snapshot = ReviewWorkspaceService().compose(*sources(filters))
        self.assertEqual(len(snapshot.items), 1)
        self.assertEqual(snapshot.active_filters, filters)

    def test_explicit_empty_and_not_evaluated_states(self):
        workspace, _, _ = sources()
        empty = CoverageAnalyzer().analyze(CoverageInput("project", 0))
        collection = InsightCollection((), 0, 4)
        self.assertEqual(ReviewWorkspaceService().compose(workspace, empty, collection).state, ReviewState.PROJECT_EMPTY)

    def test_service_has_no_qt_domain_or_sqlite_dependency(self):
        path = Path("applications/rsc/services/review_workspace_service.py")
        tree = ast.parse(path.read_text(encoding="utf-8"))
        imports = {alias.name for node in ast.walk(tree) if isinstance(node, ast.Import) for alias in node.names}
        imports |= {node.module or "" for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)}
        self.assertFalse(any(value.startswith(("PySide6", "database", "applications.rsc.domain")) for value in imports))


if __name__ == "__main__":
    unittest.main()
