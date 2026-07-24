import ast
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from core.application_registry import (
    ApplicationNotRegisteredError,
    ApplicationRegistry,
    DuplicateApplicationError,
    IncompatibleApplicationError,
)
from core.project_manager import ProjectManager
from core.project_session_factory import ProjectSessionFactory
from models import Project


class FakeApplication:
    def __init__(self, application_id="example", compatible=True):
        self.application_id = application_id
        self.compatible = compatible
        self.checked_projects = []
        self.contribution_calls = 0

    def can_open(self, project):
        self.checked_projects.append(project)
        return self.compatible

    def contributions(self):
        self.contribution_calls += 1
        return ()


def project(application="example"):
    return Project(
        project_name="Projeto",
        project_path=Path("projeto.pdop"),
        created_at="2026-07-24T10:00:00",
        last_opened_at="2026-07-24T10:00:00",
        application=application,
    )


class ApplicationRegistryTests(unittest.TestCase):
    def test_empty_registry(self):
        registry = ApplicationRegistry()

        self.assertEqual(registry.applications, ())
        self.assertIsNone(registry.get("missing"))

    def test_register_and_find_application_by_id(self):
        application = FakeApplication()
        registry = ApplicationRegistry()

        registry.register(application)

        self.assertEqual(registry.applications, (application,))
        self.assertIs(registry.get("example"), application)

    def test_duplicate_application_id_is_rejected(self):
        with self.assertRaises(DuplicateApplicationError):
            ApplicationRegistry(
                [FakeApplication(), FakeApplication()]
            )

    def test_compatible_project_resolves_registered_application(self):
        application = FakeApplication()
        registry = ApplicationRegistry([application])
        candidate = project()

        self.assertIs(registry.resolve(candidate), application)
        self.assertEqual(application.checked_projects, [candidate])

    def test_incompatible_project_is_rejected(self):
        registry = ApplicationRegistry(
            [FakeApplication(compatible=False)]
        )

        with self.assertRaises(IncompatibleApplicationError):
            registry.resolve(project())

    def test_unknown_application_id_is_rejected(self):
        with self.assertRaises(ApplicationNotRegisteredError):
            ApplicationRegistry().resolve(project("unknown"))

    def test_missing_and_legacy_application_preserve_current_mode(self):
        registry = ApplicationRegistry()

        for application_id in (None, "", "   ", "ProcDocOrganizer"):
            with self.subTest(application_id=application_id):
                self.assertIsNone(
                    registry.resolve(project(application_id))
                )

    def test_registered_legacy_id_is_resolved_normally(self):
        application = FakeApplication("ProcDocOrganizer")

        self.assertIs(
            ApplicationRegistry([application]).resolve(
                project("ProcDocOrganizer")
            ),
            application,
        )

    def test_registry_has_no_ui_or_infrastructure_dependencies(self):
        path = (
            Path(__file__).parents[1]
            / "core"
            / "application_registry.py"
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
            "PySide6", "sqlite3", "database", "services",
            "controllers", "ui",
        ):
            self.assertFalse(
                any(
                    forbidden.lower() in imported.lower()
                    for imported in imports
                ),
                f"Dependência proibida no ApplicationRegistry: {forbidden}",
            )


class ApplicationRegistryCompositionTests(unittest.TestCase):
    def test_factory_preserves_legacy_flow_with_empty_registry(self):
        with TemporaryDirectory() as temporary_directory:
            created = ProjectManager().create_project(
                "Legado", Path(temporary_directory)
            )

            session = ProjectSessionFactory(
                ApplicationRegistry()
            ).create(created)

            self.assertIsNone(session.application)
            self.assertIs(session.project, created)

    def test_factory_resolves_application_without_consuming_contributions(self):
        with TemporaryDirectory() as temporary_directory:
            created = ProjectManager().create_project(
                "Registrado", Path(temporary_directory)
            )
            created.application = "example"
            application = FakeApplication()

            session = ProjectSessionFactory(
                ApplicationRegistry([application])
            ).create(created)

            self.assertIs(session.application, application)
            self.assertEqual(application.checked_projects, [created])
            self.assertEqual(application.contribution_calls, 0)


if __name__ == "__main__":
    unittest.main()
