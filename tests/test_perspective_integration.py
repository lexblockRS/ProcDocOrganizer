import ast
import os
from pathlib import Path
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from presentation import (
    ApplicationState,
    PerspectiveDefinition,
    PerspectiveId,
)
from ui.main_window import MainWindow


class PerspectiveIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.window = MainWindow()

    def tearDown(self):
        self.window.close()
        self.window.deleteLater()
        self.app.processEvents()

    def _open_project(self):
        self.window.application_state_store.transition_to(
            ApplicationState.PROJECT_OPEN,
            project_id="Projeto",
        )

    def test_required_perspectives_are_registered(self):
        registered = {
            definition.id.value
            for definition in self.window.perspective_store.list_all()
        }
        self.assertTrue(
            {"home", "documents", "timeline", "evidence", "reports"}
            <= registered
        )

    def test_navigation_mounts_each_required_perspective(self):
        self._open_project()
        for value in (
            "home",
            "documents",
            "timeline",
            "evidence",
            "reports",
        ):
            perspective_id = PerspectiveId(value)
            self.window.navigation_controller.navigate_to(perspective_id)
            self.assertEqual(
                self.window.perspective_store.snapshot.active,
                perspective_id,
            )
            self.assertEqual(
                self.window.workspace_store.snapshot.active_perspective,
                perspective_id,
            )
            self.assertIs(
                self.window.workspace_host.active_widget,
                self.window.views[value],
            )

    def test_repeated_navigation_preserves_workspace_stability(self):
        self._open_project()
        widgets = dict(self.window.views)
        for _ in range(4):
            for value in ("documents", "timeline", "evidence", "reports"):
                self.window.navigation_controller.navigate_to(
                    PerspectiveId(value)
                )
                self.assertIs(
                    self.window.workspace_host.active_widget,
                    widgets[value],
                )
        self.assertEqual(
            self.window.stack.count(),
            len(self.window.views),
        )

    def test_unknown_perspective_is_rejected_without_workspace_change(self):
        before = self.window.workspace_store.snapshot
        with self.assertRaisesRegex(ValueError, "não registrada"):
            self.window.navigation_controller.navigate_to(
                PerspectiveId("unknown")
            )
        self.assertEqual(self.window.workspace_store.snapshot, before)

    def test_menu_is_generated_from_registered_perspectives(self):
        definitions = self.window.perspective_store.list_all()
        actions = self.window.perspectives_menu.actions()
        self.assertEqual(
            [action.data() for action in actions],
            [definition.id.value for definition in definitions],
        )
        self.assertEqual(
            [action.text() for action in actions],
            [definition.title for definition in definitions],
        )

    def test_late_registration_updates_menu_and_toolbar_automatically(self):
        self.window.perspective_store.register(
            PerspectiveDefinition(
                PerspectiveId("late"),
                "Adicional",
                999,
                None,
                False,
                lambda: self.window,
            )
        )
        self.assertEqual(
            self.window.perspectives_menu.actions()[-1].data(),
            "late",
        )
        self.assertEqual(
            self.window.perspective_selector.itemData(
                self.window.perspective_selector.count() - 1
            ),
            "late",
        )

    def test_menu_forwards_navigation_to_navigation_controller(self):
        self._open_project()
        action = next(
            action
            for action in self.window.perspectives_menu.actions()
            if action.data() == "timeline"
        )
        action.trigger()
        self.assertEqual(
            self.window.workspace_store.snapshot.active_perspective,
            PerspectiveId("timeline"),
        )
        self.assertTrue(action.isChecked())

    def test_toolbar_selector_uses_same_catalog_and_navigation(self):
        self._open_project()
        definitions = self.window.perspective_store.list_all()
        self.assertEqual(
            [
                self.window.perspective_selector.itemData(index)
                for index in range(self.window.perspective_selector.count())
            ],
            [definition.id.value for definition in definitions],
        )
        index = self.window.perspective_selector.findData("reports")
        self.window.perspective_selector.setCurrentIndex(index)
        self.assertEqual(
            self.window.workspace_store.snapshot.active_perspective,
            PerspectiveId("reports"),
        )

    def test_project_requirement_drives_menu_and_toolbar_availability(self):
        definitions = self.window.perspective_store.list_all()
        actions = self.window.perspectives_menu.actions()
        for definition, action in zip(definitions, actions, strict=True):
            self.assertEqual(
                action.isEnabled(),
                not definition.requires_project,
            )
        self._open_project()
        self.assertTrue(all(action.isEnabled() for action in actions))
        model = self.window.perspective_selector.model()
        self.assertTrue(
            all(
                model.item(index).isEnabled()
                for index in range(self.window.perspective_selector.count())
            )
        )


class PerspectiveIntegrationArchitectureTests(unittest.TestCase):
    def test_main_window_has_no_concrete_view_imports(self):
        tree = ast.parse(
            Path("ui/main_window.py").read_text(encoding="utf-8")
        )
        imported_modules = {
            node.module
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom)
        }
        self.assertFalse(
            any(
                module == "ui.views" or module.startswith("ui.views.")
                for module in imported_modules
            )
        )

    def test_navigation_entry_points_do_not_call_workspace_or_view_manager(self):
        tree = ast.parse(
            Path("ui/main_window.py").read_text(encoding="utf-8")
        )
        main_window = next(
            node
            for node in tree.body
            if isinstance(node, ast.ClassDef)
            and node.name == "MainWindow"
        )
        navigation_methods = {
            node.name: node
            for node in main_window.body
            if isinstance(node, ast.FunctionDef)
            and node.name
            in {"show_view", "_navigate_from_perspective_selector"}
        }
        for method in navigation_methods.values():
            attributes = {
                node.attr
                for node in ast.walk(method)
                if isinstance(node, ast.Attribute)
            }
            self.assertIn("navigation_controller", attributes)
            self.assertNotIn("workspace_store", attributes)
            self.assertNotIn("view_manager", attributes)


if __name__ == "__main__":
    unittest.main()
