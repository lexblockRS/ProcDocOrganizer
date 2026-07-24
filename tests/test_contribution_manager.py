import ast
from pathlib import Path
import unittest

from contracts import ActionContribution
from core.contribution_manager import ContributionManager
from core.exceptions import ContributionError


def contribution(contribution_id):
    return ActionContribution(
        contribution_id=contribution_id,
        text=f"Action {contribution_id}",
        callback=lambda: None,
    )


class ContributionManagerTests(unittest.TestCase):
    def test_activate_empty(self):
        manager = ContributionManager()

        manager.activate(())

        self.assertEqual(manager.active(), ())

    def test_activate_normal_set(self):
        manager = ContributionManager()
        first = contribution("first")
        second = contribution("second")

        manager.activate([first, second])

        self.assertEqual(manager.active(), (first, second))

    def test_clear_removes_all_contributions(self):
        manager = ContributionManager()
        manager.activate([contribution("first")])

        manager.clear()

        self.assertEqual(manager.active(), ())

    def test_replace_changes_complete_set(self):
        manager = ContributionManager()
        old = contribution("old")
        first = contribution("first")
        second = contribution("second")
        manager.activate([old])

        manager.replace([first, second])

        self.assertEqual(manager.active(), (first, second))

    def test_replace_preserves_old_state_when_iteration_fails(self):
        manager = ContributionManager()
        old = contribution("old")
        manager.activate([old])

        def failing_contributions():
            yield contribution("new")
            raise RuntimeError("preparation failed")

        with self.assertRaises(ContributionError) as context:
            manager.replace(failing_contributions())

        self.assertEqual(manager.active(), (old,))
        self.assertIsInstance(context.exception.__cause__, RuntimeError)

    def test_duplicate_ids_are_rejected_atomically(self):
        manager = ContributionManager()

        with self.assertRaisesRegex(
            ContributionError, "ID de contribuição duplicado"
        ):
            manager.activate(
                [contribution("duplicate"), contribution("duplicate")]
            )

        self.assertEqual(manager.active(), ())

    def test_activate_twice_is_rejected(self):
        manager = ContributionManager()
        first = contribution("first")
        manager.activate([first])

        with self.assertRaises(ContributionError):
            manager.activate([contribution("second")])

        self.assertEqual(manager.active(), (first,))

    def test_replace_with_empty_set_clears_state(self):
        manager = ContributionManager()
        manager.activate([contribution("first")])

        manager.replace(())

        self.assertEqual(manager.active(), ())

    def test_active_returns_immutable_snapshot(self):
        manager = ContributionManager()
        first = contribution("first")
        manager.activate([first])

        snapshot = manager.active()
        manager.replace([contribution("second")])

        self.assertIsInstance(snapshot, tuple)
        self.assertEqual(snapshot, (first,))

    def test_invalid_contribution_is_rejected_atomically(self):
        manager = ContributionManager()
        old = contribution("old")
        manager.activate([old])

        with self.assertRaises(ContributionError):
            manager.replace([contribution("new"), object()])

        self.assertEqual(manager.active(), (old,))

    def test_does_not_execute_callbacks(self):
        calls = []
        action = ActionContribution(
            contribution_id="action",
            text="Action",
            callback=lambda: calls.append("called"),
        )
        manager = ContributionManager()

        manager.activate([action])
        manager.replace([action])
        manager.clear()

        self.assertEqual(calls, [])

    def test_manager_has_no_qt_or_ui_dependencies(self):
        path = (
            Path(__file__).parents[1]
            / "core"
            / "contribution_manager.py"
        )
        tree = ast.parse(path.read_text(encoding="utf-8"))
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
            "PySide6",
            "QAction",
            "QMenu",
            "MainWindow",
            "ui",
            "applications",
        ):
            self.assertFalse(
                any(
                    forbidden.lower() in imported.lower()
                    for imported in imports
                ),
                f"Dependência proibida no ContributionManager: {forbidden}",
            )


if __name__ == "__main__":
    unittest.main()
