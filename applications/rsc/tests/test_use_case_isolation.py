import ast
from pathlib import Path
import unittest


class UseCaseIsolationTests(unittest.TestCase):
    def test_use_case_package_has_no_forbidden_imports_or_execution_methods(self):
        root = Path(__file__).parents[1] / "use_cases"
        forbidden_fragments = (
            "pyside",
            "pyqt",
            "ocr",
            "openai",
            "anthropic",
            "pdf",
            "requests",
            "urllib",
            "httpx",
        )

        for path in root.glob("*.py"):
            with self.subTest(path=path):
                tree = ast.parse(path.read_text(encoding="utf-8"))
                imports = {
                    alias.name.lower()
                    for node in ast.walk(tree)
                    if isinstance(node, ast.Import)
                    for alias in node.names
                }
                imports.update(
                    (node.module or "").lower().lstrip(".")
                    for node in ast.walk(tree)
                    if isinstance(node, ast.ImportFrom)
                )
                self.assertFalse(
                    any(
                        token in imported
                        for imported in imports
                        for token in forbidden_fragments
                    ),
                    imports,
                )
                self.assertFalse(
                    any(
                        imported == "ui" or imported.startswith("ui.")
                        for imported in imports
                    ),
                    imports,
                )
                if path.name in {"commands.py", "results.py"}:
                    methods = {
                        node.name
                        for node in ast.walk(tree)
                        if isinstance(
                            node, (ast.FunctionDef, ast.AsyncFunctionDef)
                        )
                    }
                    self.assertEqual(methods, set())


if __name__ == "__main__":
    unittest.main()
