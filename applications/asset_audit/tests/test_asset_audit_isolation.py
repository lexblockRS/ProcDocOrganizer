import ast
from pathlib import Path
import unittest


class AssetAuditIsolationTests(unittest.TestCase):
    def test_productive_files_only_import_sdk_self_or_standard_library(self):
        root = Path(__file__).parents[1]
        forbidden = (
            "core",
            "ui",
            "PySide6",
            "PyQt",
            "applications.rsc",
        )
        forbidden_names = {
            "Project" + "Session",
            "Window" + "ActionSpec",
            "Window" + "ViewSpec",
            "Window" + "ToolbarSpec",
        }

        for path in root.rglob("*.py"):
            if "tests" in path.parts:
                continue
            tree = ast.parse(path.read_text(encoding="utf-8"))
            imported_modules = {
                node.module or ""
                for node in ast.walk(tree)
                if isinstance(node, ast.ImportFrom)
            }
            imported_modules.update(
                alias.name
                for node in ast.walk(tree)
                if isinstance(node, ast.Import)
                for alias in node.names
            )
            imported_names = {
                alias.name
                for node in ast.walk(tree)
                if isinstance(node, (ast.Import, ast.ImportFrom))
                for alias in node.names
            }

            with self.subTest(path=path):
                self.assertFalse(any(
                    module == item or module.startswith(f"{item}.")
                    for module in imported_modules
                    for item in forbidden
                ))
                self.assertTrue(
                    forbidden_names.isdisjoint(imported_names)
                )


if __name__ == "__main__":
    unittest.main()
