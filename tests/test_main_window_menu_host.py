import ast
import os
from pathlib import Path
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtGui import QAction
from PySide6.QtWidgets import QApplication

from ui.main_window import MainWindow


class MainWindowMenuHostTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.window = MainWindow()

    def tearDown(self):
        self.window.close()
        self.window.deleteLater()

    def test_permanent_menus_are_registered_by_stable_ids(self):
        expected_titles = {
            "file": "Arquivo",
            "edit": "Editar",
            "evidence": "Evidências",
            "classification": "Classificação",
            "tools": "Ferramentas",
            "help": "Ajuda",
        }

        for menu_id, title in expected_titles.items():
            with self.subTest(menu_id=menu_id):
                self.assertEqual(
                    self.window.get_menu(menu_id).title(), title
                )

    def test_get_menu_does_not_depend_on_visible_title(self):
        menu = self.window.get_menu("tools")
        menu.setTitle("Título alterado")

        self.assertIs(self.window.get_menu("tools"), menu)

    def test_get_unknown_menu_raises_clear_error(self):
        with self.assertRaisesRegex(KeyError, "Menu não registrado"):
            self.window.get_menu("unknown")

    def test_creates_application_menu_and_adds_it_to_menu_bar(self):
        menu = self.window.create_application_menu(
            "application.example", "Example"
        )

        self.assertIs(
            self.window.get_menu("application.example"), menu
        )
        self.assertIn(
            menu.menuAction(),
            self.window.menuBar().actions(),
        )
        self.assertEqual(menu.actions(), [])

    def test_duplicate_application_menu_id_is_rejected(self):
        self.window.create_application_menu(
            "application.example", "Example"
        )

        with self.assertRaisesRegex(ValueError, "já registrado"):
            self.window.create_application_menu(
                "application.example", "Other"
            )

    def test_permanent_menu_id_collision_is_rejected(self):
        original = self.window.get_menu("tools")

        with self.assertRaisesRegex(ValueError, "já registrado"):
            self.window.create_application_menu("tools", "Other")

        self.assertIs(self.window.get_menu("tools"), original)

    def test_rejects_empty_menu_id(self):
        for value in ("", "   "):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    self.window.create_application_menu(value, "Example")

    def test_rejects_invalid_menu_id_type(self):
        for value in (None, 1, object()):
            with self.subTest(value=value):
                with self.assertRaises(TypeError):
                    self.window.create_application_menu(value, "Example")

    def test_rejects_empty_title(self):
        for value in ("", "   "):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    self.window.create_application_menu(
                        "application.example", value
                    )

    def test_rejects_invalid_title_type(self):
        for value in (None, 1, object()):
            with self.subTest(value=value):
                with self.assertRaises(TypeError):
                    self.window.create_application_menu(
                        "application.example", value
                    )

    def test_preserves_valid_values_without_normalization(self):
        menu = self.window.create_application_menu(
            "  application.example  ",
            "  Example  ",
        )

        self.assertIs(
            self.window.get_menu("  application.example  "), menu
        )
        self.assertEqual(menu.title(), "  Example  ")

    def test_remove_application_menu_clears_and_unregisters_it(self):
        menu = self.window.create_application_menu(
            "application.example", "Example"
        )
        action = QAction("Dynamic action", menu)
        menu.addAction(action)
        menu_action = menu.menuAction()

        self.window.remove_application_menu("application.example")

        self.assertNotIn(
            menu_action,
            self.window.menuBar().actions(),
        )
        self.assertEqual(menu.actions(), [])
        with self.assertRaises(KeyError):
            self.window.get_menu("application.example")

    def test_remove_cannot_delete_permanent_menu(self):
        menu = self.window.get_menu("tools")
        menu_action = menu.menuAction()

        with self.assertRaisesRegex(ValueError, "permanente"):
            self.window.remove_application_menu("tools")

        self.assertIs(self.window.get_menu("tools"), menu)
        self.assertIn(menu_action, self.window.menuBar().actions())

    def test_remove_unknown_application_menu_is_idempotent(self):
        self.window.remove_application_menu("application.missing")
        self.window.remove_application_menu("application.missing")

        with self.assertRaises(KeyError):
            self.window.get_menu("application.missing")

    def test_removed_id_can_be_recreated_without_duplication(self):
        old_menu = self.window.create_application_menu(
            "application.example", "Old"
        )
        old_action = old_menu.menuAction()
        self.window.remove_application_menu("application.example")

        new_menu = self.window.create_application_menu(
            "application.example", "New"
        )

        self.assertIs(
            self.window.get_menu("application.example"), new_menu
        )
        self.assertNotIn(old_action, self.window.menuBar().actions())
        self.assertEqual(
            self.window.menuBar().actions().count(
                new_menu.menuAction()
            ),
            1,
        )

    def test_main_window_has_no_application_domain_dependencies(self):
        path = Path(__file__).parents[1] / "ui" / "main_window.py"
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
            "RscApplication",
            "applications",
            "ActionContribution",
            "ContributionManager",
            "ProjectSession",
        ):
            self.assertFalse(
                any(
                    forbidden.lower() in imported.lower()
                    for imported in imports
                ),
                f"Dependência proibida na MainWindow: {forbidden}",
            )


if __name__ == "__main__":
    unittest.main()
