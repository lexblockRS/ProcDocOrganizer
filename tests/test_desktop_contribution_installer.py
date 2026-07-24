import ast
import os
from pathlib import Path
import unittest
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtGui import QAction
from PySide6.QtWidgets import QApplication, QMenu

from contracts import ActionContribution
from ui.contribution_installer import (
    ContributionInstallationError,
    DesktopContributionInstaller,
)
from ui.main_window import MainWindow


def contribution(
    contribution_id="action.example",
    *,
    text=None,
    callback=lambda: None,
    menu_id="tools",
):
    return ActionContribution(
        contribution_id=contribution_id,
        text=text if text is not None else f"Action {contribution_id}",
        callback=callback,
        menu_id=menu_id,
    )


class MenuHost:
    def __init__(self, menus):
        self.menus = menus
        self.requested_ids = []

    def get_menu(self, menu_id):
        self.requested_ids.append(menu_id)
        return self.menus[menu_id]


class FailingAddMenu(QMenu):
    def __init__(self, fail_on_calls, parent=None):
        super().__init__("Failing", parent)
        self.fail_on_calls = set(fail_on_calls)
        self.add_calls = 0

    def addAction(self, action):
        self.add_calls += 1
        if self.add_calls in self.fail_on_calls:
            raise RuntimeError("addAction failed")
        return super().addAction(action)


class FailingRemoveMenu(QMenu):
    def removeAction(self, action):
        raise RuntimeError("removeAction failed")


class TrackingAction(QAction):
    instances = []

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.delete_later_called = False
        self.__class__.instances.append(self)

    def deleteLater(self):
        self.delete_later_called = True
        super().deleteLater()


class DesktopContributionInstallerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.window = MainWindow()
        self.installer = DesktopContributionInstaller(self.window)

    def tearDown(self):
        try:
            self.installer.clear()
        except ContributionInstallationError:
            pass
        self.window.close()
        self.window.deleteLater()

    def test_installs_action_in_correct_menu_with_preserved_text(self):
        action_contribution = contribution(text="  Example  ")
        menu = self.window.get_menu("tools")

        self.installer.install([action_contribution])

        actions = menu.actions()
        self.assertEqual(len(actions), 1)
        self.assertIsInstance(actions[0], QAction)
        self.assertEqual(actions[0].text(), "  Example  ")
        self.assertEqual(
            self.installer.active(), (action_contribution,)
        )

    def test_install_does_not_execute_callback(self):
        calls = []

        self.installer.install([
            contribution(callback=lambda: calls.append("called"))
        ])

        self.assertEqual(calls, [])

    def test_trigger_executes_callback_once_without_checked_argument(self):
        calls = []
        self.installer.install([
            contribution(callback=lambda: calls.append("called"))
        ])
        action = self.window.get_menu("tools").actions()[0]

        action.trigger()

        self.assertEqual(calls, ["called"])

    def test_clear_removes_action_disconnects_and_clears_active(self):
        calls = []
        menu = self.window.get_menu("tools")
        self.installer.install([
            contribution(callback=lambda: calls.append("called"))
        ])
        action = menu.actions()[0]

        self.installer.clear()
        action.trigger()

        self.assertNotIn(action, menu.actions())
        self.assertEqual(calls, [])
        self.assertEqual(self.installer.active(), ())

    def test_clear_schedules_action_destruction(self):
        TrackingAction.instances = []
        installer = DesktopContributionInstaller(self.window)

        with patch(
            "ui.contribution_installer.QAction", TrackingAction
        ):
            installer.install([contribution()])
            action = TrackingAction.instances[0]
            installer.clear()

        self.assertTrue(action.delete_later_called)

    def test_clear_is_idempotent(self):
        self.installer.clear()
        self.installer.clear()

        self.assertEqual(self.installer.active(), ())

    def test_clear_attempts_all_handles_and_empties_state_on_error(self):
        failing_menu = FailingRemoveMenu("Failing", self.window)
        normal_menu = QMenu("Normal", self.window)
        installer = DesktopContributionInstaller(
            MenuHost({"failing": failing_menu, "normal": normal_menu})
        )
        installer.install([
            contribution("failing", menu_id="failing"),
            contribution("normal", menu_id="normal"),
        ])
        normal_action = normal_menu.actions()[0]

        with self.assertRaises(ContributionInstallationError):
            installer.clear()

        self.assertNotIn(normal_action, normal_menu.actions())
        self.assertEqual(installer.active(), ())

    def test_duplicate_ids_are_rejected_without_ui_changes(self):
        menu = self.window.get_menu("tools")

        with self.assertRaisesRegex(
            ContributionInstallationError, "duplicado"
        ):
            self.installer.install([
                contribution("duplicate"),
                contribution("duplicate"),
            ])

        self.assertEqual(menu.actions(), [])
        self.assertEqual(self.installer.active(), ())

    def test_invalid_item_is_rejected(self):
        with self.assertRaisesRegex(
            ContributionInstallationError, "ActionContribution"
        ):
            self.installer.install([object()])

        self.assertEqual(self.installer.active(), ())

    def test_missing_menu_id_is_rejected(self):
        with self.assertRaisesRegex(
            ContributionInstallationError, "menu_id"
        ):
            self.installer.install([contribution(menu_id=None)])

        self.assertEqual(self.installer.active(), ())

    def test_unknown_menu_is_rejected_with_original_cause(self):
        with self.assertRaises(
            ContributionInstallationError
        ) as context:
            self.installer.install([
                contribution(menu_id="unknown")
            ])

        self.assertIsInstance(context.exception.__cause__, KeyError)
        self.assertEqual(self.installer.active(), ())

    def test_partial_installation_is_cleaned_up(self):
        first_menu = QMenu("First", self.window)
        failing_menu = FailingAddMenu({1}, self.window)
        installer = DesktopContributionInstaller(
            MenuHost({"first": first_menu, "failing": failing_menu})
        )

        with self.assertRaises(ContributionInstallationError):
            installer.install([
                contribution("first", menu_id="first"),
                contribution("second", menu_id="failing"),
            ])

        self.assertEqual(first_menu.actions(), [])
        self.assertEqual(failing_menu.actions(), [])
        self.assertEqual(installer.active(), ())

    def test_install_when_active_is_rejected(self):
        first = contribution("first")
        self.installer.install([first])

        with self.assertRaises(ContributionInstallationError):
            self.installer.install([contribution("second")])

        self.assertEqual(self.installer.active(), (first,))

    def test_valid_replace_changes_complete_set(self):
        tools = self.window.get_menu("tools")
        help_menu = self.window.get_menu("help")
        old = contribution("old")
        new = contribution("new", menu_id="help")
        self.installer.install([old])

        self.installer.replace([new])

        self.assertEqual(tools.actions(), [])
        self.assertIn(
            "Action new",
            [action.text() for action in help_menu.actions()],
        )
        self.assertEqual(self.installer.active(), (new,))

    def test_replace_with_empty_set_clears_actions(self):
        menu = self.window.get_menu("tools")
        self.installer.install([contribution()])

        self.installer.replace(())

        self.assertEqual(menu.actions(), [])
        self.assertEqual(self.installer.active(), ())

    def test_replace_validation_failure_preserves_old_action(self):
        old = contribution("old")
        menu = self.window.get_menu("tools")
        self.installer.install([old])
        old_action = menu.actions()[0]

        with self.assertRaises(ContributionInstallationError):
            self.installer.replace([contribution("new", menu_id=None)])

        self.assertEqual(self.installer.active(), (old,))
        self.assertIn(old_action, menu.actions())

    def test_material_replace_failure_restores_old_contribution(self):
        menu = FailingAddMenu({2}, self.window)
        installer = DesktopContributionInstaller(
            MenuHost({"target": menu})
        )
        old = contribution("old", menu_id="target")
        installer.install([old])

        with self.assertRaisesRegex(
            ContributionInstallationError, "restaurado"
        ):
            installer.replace([
                contribution("new", menu_id="target")
            ])

        self.assertEqual(installer.active(), (old,))
        self.assertEqual(
            [action.text() for action in menu.actions()],
            ["Action old"],
        )
        installer.clear()

    def test_replace_reports_failure_when_rollback_also_fails(self):
        menu = FailingAddMenu({2, 3}, self.window)
        installer = DesktopContributionInstaller(
            MenuHost({"target": menu})
        )
        installer.install([
            contribution("old", menu_id="target")
        ])

        with self.assertRaisesRegex(
            ContributionInstallationError,
            "restaurar o conjunto anterior",
        ):
            installer.replace([
                contribution("new", menu_id="target")
            ])

        self.assertEqual(installer.active(), ())

    def test_does_not_create_application_menu(self):
        top_level_actions = tuple(self.window.menuBar().actions())

        self.installer.install([contribution()])

        self.assertEqual(
            tuple(self.window.menuBar().actions()),
            top_level_actions,
        )

    def test_installed_handle_is_private_and_not_exposed(self):
        import ui.contribution_installer as module

        self.assertFalse(hasattr(self.installer, "installed"))
        self.assertNotIn("_InstalledAction", getattr(module, "__all__", ()))

    def test_module_has_no_forbidden_architectural_dependencies(self):
        root = Path(__file__).parents[1]
        installer_path = root / "ui" / "contribution_installer.py"
        tree = ast.parse(installer_path.read_text(encoding="utf-8"))
        imports = {
            alias.name
            for node in ast.walk(tree)
            if isinstance(node, ast.Import)
            for alias in node.names
        }
        imports.update(
            node.module or ""
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom)
        )

        for forbidden in (
            "RscApplication",
            "applications",
            "ProjectController",
            "ProjectSession",
        ):
            self.assertFalse(
                any(
                    forbidden.lower() in imported.lower()
                    for imported in imports
                )
            )

        core_source = (
            root / "core" / "contribution_manager.py"
        ).read_text(encoding="utf-8")
        self.assertNotIn("PySide6", core_source)


if __name__ == "__main__":
    unittest.main()
