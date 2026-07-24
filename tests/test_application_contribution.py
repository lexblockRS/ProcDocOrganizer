import ast
from dataclasses import FrozenInstanceError
from pathlib import Path
import unittest

from contracts import ActionContribution


def callback():
    return None


class ActionContributionTests(unittest.TestCase):
    def test_creates_valid_contribution_with_default_menu(self):
        contribution = ActionContribution(
            contribution_id="action.example",
            text="Example",
            callback=callback,
        )

        self.assertEqual(contribution.contribution_id, "action.example")
        self.assertEqual(contribution.text, "Example")
        self.assertIs(contribution.callback, callback)
        self.assertIsNone(contribution.menu_id)

    def test_accepts_valid_menu_id(self):
        contribution = ActionContribution(
            "action.example", "Example", callback, "tools"
        )

        self.assertEqual(contribution.menu_id, "tools")

    def test_is_immutable(self):
        contribution = ActionContribution(
            "action.example", "Example", callback
        )

        with self.assertRaises(FrozenInstanceError):
            contribution.text = "Changed"

    def test_uses_slots(self):
        contribution = ActionContribution(
            "action.example", "Example", callback
        )

        self.assertFalse(hasattr(contribution, "__dict__"))

    def test_rejects_empty_contribution_id(self):
        for value in ("", "   "):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    ActionContribution(value, "Example", callback)

    def test_rejects_invalid_contribution_id_type(self):
        for value in (None, 1, object()):
            with self.subTest(value=value):
                with self.assertRaises(TypeError):
                    ActionContribution(value, "Example", callback)

    def test_rejects_empty_text(self):
        for value in ("", "   "):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    ActionContribution("action.example", value, callback)

    def test_rejects_invalid_text_type(self):
        for value in (None, 1, object()):
            with self.subTest(value=value):
                with self.assertRaises(TypeError):
                    ActionContribution("action.example", value, callback)

    def test_rejects_non_callable_callback(self):
        for value in (None, "callback", object()):
            with self.subTest(value=value):
                with self.assertRaises(TypeError):
                    ActionContribution("action.example", "Example", value)

    def test_rejects_empty_menu_id(self):
        for value in ("", "   "):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    ActionContribution(
                        "action.example", "Example", callback, value
                    )

    def test_rejects_invalid_menu_id_type(self):
        for value in (1, object()):
            with self.subTest(value=value):
                with self.assertRaises(TypeError):
                    ActionContribution(
                        "action.example", "Example", callback, value
                    )

    def test_preserves_values_without_normalization(self):
        contribution = ActionContribution(
            "  action.example  ",
            "  Example  ",
            callback,
            "  tools  ",
        )

        self.assertEqual(contribution.contribution_id, "  action.example  ")
        self.assertEqual(contribution.text, "  Example  ")
        self.assertEqual(contribution.menu_id, "  tools  ")

    def test_contract_has_no_forbidden_dependencies(self):
        contracts_directory = Path(__file__).parents[1] / "contracts"
        forbidden = (
            "PySide6",
            "QAction",
            "QMenu",
            "MainWindow",
            "ui",
            "applications",
            "services",
        )

        for path in contracts_directory.glob("*.py"):
            with self.subTest(path=path.name):
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
                for name in forbidden:
                    self.assertFalse(
                        any(
                            name.lower() in imported.lower()
                            for imported in imports
                        ),
                        f"Dependência proibida em {path.name}: {name}",
                    )


if __name__ == "__main__":
    unittest.main()
