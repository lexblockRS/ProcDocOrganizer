import ast
from pathlib import Path
import unittest

from contracts import Application
from models import Project


class ExampleApplication:
    application_id = "example"
    display_name = "Example"

    def can_open(self, project):
        return project.application == self.application_id

    def contributions(self):
        return ()


class ApplicationContractTests(unittest.TestCase):
    def test_contract_is_structural_and_exposes_minimum_boundary(self):
        application = ExampleApplication()

        self.assertIsInstance(application, Application)
        self.assertEqual(application.application_id, "example")
        self.assertEqual(application.contributions(), ())

    def test_contract_uses_existing_project_application_identity(self):
        project = Project.create("Projeto", Path("projeto.pdop"))
        project.application = "example"

        self.assertTrue(ExampleApplication().can_open(project))

    def test_contract_has_no_forbidden_dependencies(self):
        path = (
            Path(__file__).parents[1]
            / "contracts"
            / "application.py"
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
        forbidden = (
            "PySide6",
            "sqlite3",
            "database",
            "services",
            "controllers",
            "ui",
            "widgets",
            "workspaces",
            "rsc",
        )

        for name in forbidden:
            self.assertFalse(
                any(name.lower() in imported.lower() for imported in imports),
                f"Dependência proibida no contrato Application: {name}",
            )


if __name__ == "__main__":
    unittest.main()
