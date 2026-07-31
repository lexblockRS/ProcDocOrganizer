import unittest

from PySide6.QtWidgets import QApplication
from applications.rsc.services.workspace_dashboard_service import WorkspaceDashboardService
from applications.rsc.workspace_dashboard_view_model import WorkspaceDashboardViewModel
from presentation.coverage import CoverageInput
from presentation.coverage_analyzer import CoverageAnalyzer
from presentation.insights import InsightCollection
from presentation.perspectives import PerspectiveId
from presentation.workspace import WorkspaceSnapshot, WorkspaceState
from ui.workspace_dashboard import WorkspaceDashboardView


class WorkspaceDashboardViewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_renders_passive_empty_dashboard(self):
        workspace = WorkspaceSnapshot(WorkspaceState.READY, PerspectiveId("dashboard"), 0, project_id="p")
        snapshot = WorkspaceDashboardService().summarize(workspace, CoverageAnalyzer().analyze(CoverageInput("p", 0)), InsightCollection((), 0, 0))
        view = WorkspaceDashboardView(WorkspaceDashboardViewModel(snapshot).dashboard)
        self.assertEqual(view.dashboard.coverage.ratio, "0/0")
        self.assertGreaterEqual(view.priority_list.count(), 1)


if __name__ == "__main__":
    unittest.main()
