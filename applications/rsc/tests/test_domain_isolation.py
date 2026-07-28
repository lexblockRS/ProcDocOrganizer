import ast
from pathlib import Path
import unittest


class RscDomainIsolationTests(unittest.TestCase):
    def test_domain_catalogs_and_new_services_have_no_forbidden_imports(self):
        root = Path(__file__).parents[1]
        inspected = (
            *(root / "domain").glob("*.py"),
            *(root / "catalogs").glob("*.py"),
            root / "services" / "process_service.py",
            root / "services" / "activity_service.py",
            root / "services" / "evidence_service.py",
            root / "services" / "scoring_service.py",
            root / "services" / "validation_service.py",
        )
        forbidden_fragments = (
            "pyside",
            "pyqt",
            "applications.asset_audit",
            "ocr",
            "openai",
            "anthropic",
            "pdf",
            "requests",
            "urllib",
            "httpx",
        )
        for path in inspected:
            with self.subTest(path=path):
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
                normalized = {item.lower().lstrip(".") for item in imports}
                self.assertFalse(
                    any(
                        token in imported.lower()
                        for imported in normalized
                        for token in forbidden_fragments
                    ),
                    imports,
                )
                self.assertFalse(
                    any(
                        imported == "ui" or imported.startswith("ui.")
                        for imported in normalized
                    ),
                    imports,
                )


if __name__ == "__main__":
    unittest.main()
