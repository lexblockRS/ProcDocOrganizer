import ast
import os
from pathlib import Path
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication, QWidget

from contracts import ContributionCategory, ContributionRegistration
from core.contribution_manager import ContributionManager
from ui.main_window import MainWindow
from ui.main_window_contributions import (
    WindowActionSpec,
    WindowToolbarSpec,
    WindowViewSpec,
)


class FirstView(QWidget):
    pass


class SecondView(QWidget):
    pass


class MainWindowContributionHostTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.windows = []

    def tearDown(self):
        for window in self.windows:
            window.close()
            window.deleteLater()
        self.app.processEvents()

    def _window(self, manager):
        window = MainWindow(manager)
        self.windows.append(window)
        return window

    def test_installs_multiple_applications_by_priority(self):
        manager = ContributionManager()
        manager.register_many((
            ContributionRegistration(
                ContributionCategory.ACTION,
                "second-app",
                10,
                WindowActionSpec(
                    "action_second",
                    "Second",
                    "tools",
                ),
            ),
            ContributionRegistration(
                ContributionCategory.ACTION,
                "first-app",
                20,
                WindowActionSpec(
                    "action_first",
                    "First",
                    "tools",
                ),
            ),
            ContributionRegistration(
                ContributionCategory.TOOLBAR,
                "second-app",
                10,
                WindowToolbarSpec("main", "action_second"),
            ),
            ContributionRegistration(
                ContributionCategory.TOOLBAR,
                "first-app",
                20,
                WindowToolbarSpec("main", "action_first"),
            ),
        ))

        window = self._window(manager)

        tools_actions = window.get_menu("tools").actions()
        self.assertEqual(
            [item.text() for item in tools_actions],
            ["First", "Second"],
        )
        toolbar = window.findChild(
            type(window._toolbars_by_id["main"]),
            "main",
        )
        self.assertEqual(
            [item.text() for item in toolbar.actions()][-2:],
            ["First", "Second"],
        )

    def test_installs_views_and_navigation_without_application_ids(self):
        manager = ContributionManager()
        manager.register_many((
            ContributionRegistration(
                ContributionCategory.VIEW,
                "alpha",
                20,
                WindowViewSpec(
                    "first",
                    "first_view",
                    FirstView,
                    "show_first",
                ),
            ),
            ContributionRegistration(
                ContributionCategory.VIEW,
                "beta",
                10,
                WindowViewSpec(
                    "second",
                    "second_view",
                    SecondView,
                    "show_second",
                ),
            ),
        ))

        window = self._window(manager)

        self.assertIs(window.views["first"], window.first_view)
        self.assertIs(window.views["second"], window.second_view)
        self.assertTrue(window.show_second())
        self.assertIs(window.view_manager.active_view(), window.second_view)

    def test_default_bridge_preserves_historical_visual_contract(self):
        window = self._window(None)

        for attribute in (
            "action_activities",
            "action_functional_assignments",
            "action_functional_exercises",
            "activities_view",
            "functional_assignments_view",
            "functional_exercises_view",
            "show_activities",
            "show_functional_assignments",
            "show_functional_exercises",
        ):
            with self.subTest(attribute=attribute):
                self.assertTrue(hasattr(window, attribute))

    def test_main_window_has_no_concrete_application_imports(self):
        path = Path(__file__).parents[1] / "ui" / "main_window.py"
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source)
        imported = {
            alias.name
            for node in ast.walk(tree)
            if isinstance(node, ast.Import)
            for alias in node.names
        }
        imported.update(
            node.module or ""
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom)
        )

        for forbidden in (
            "applications.rsc",
            "RscApplication",
            "ActivitiesView",
            "FunctionalAssignmentsView",
            "FunctionalExercisesView",
        ):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, source)
                self.assertFalse(any(
                    forbidden.casefold() in item.casefold()
                    for item in imported
                ))


if __name__ == "__main__":
    unittest.main()
