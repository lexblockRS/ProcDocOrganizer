import ast
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from applications import RscApplication
from contracts import Application, ApplicationModule
from core.application_registry import (
    ApplicationNotRegisteredError,
    ApplicationRegistry,
)
from core.project_manager import ProjectManager
from core.project_session_factory import ProjectSessionFactory
from models import Project


def project(application):
    return Project(
        project_name="Projeto",
        project_path=Path("projeto.pdop"),
        created_at="2026-07-24T10:00:00",
        last_opened_at="2026-07-24T10:00:00",
        application=application,
    )


class RscApplicationTests(unittest.TestCase):
    def test_implements_application_contract_with_stable_identity(self):
        application = RscApplication()

        self.assertIsInstance(application, Application)
        self.assertIsInstance(application, ApplicationModule)
        self.assertEqual(application.application_id, "rsc")
        self.assertIs(application.descriptor, RscApplication.descriptor)

    def test_accepts_only_rsc_projects(self):
        application = RscApplication()

        self.assertTrue(application.can_open(project("rsc")))
        self.assertFalse(
            application.can_open(project("ProcDocOrganizer"))
        )
        self.assertFalse(application.can_open(project("other")))

    def test_contributions_are_empty(self):
        contributions = RscApplication().contributions()

        self.assertIsInstance(contributions, tuple)
        self.assertEqual(contributions, ())

    def test_registry_resolves_rsc_application(self):
        application = RscApplication()
        registry = ApplicationRegistry([application])

        self.assertIs(registry.resolve(project("rsc")), application)

    def test_unknown_application_remains_rejected(self):
        registry = ApplicationRegistry([RscApplication()])

        with self.assertRaises(ApplicationNotRegisteredError):
            registry.resolve(project("unknown"))

    def test_legacy_project_remains_without_application(self):
        registry = ApplicationRegistry([RscApplication()])

        self.assertIsNone(
            registry.resolve(project("ProcDocOrganizer"))
        )

    def test_rsc_implementation_has_no_qt_or_sqlite_dependency(self):
        root = Path(__file__).parents[1]
        for relative_path in (
            "contracts/application.py",
            "applications/rsc/application.py",
        ):
            with self.subTest(path=relative_path):
                tree = ast.parse(
                    (root / relative_path).read_text(encoding="utf-8")
                )
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
                self.assertFalse(
                    any(
                        forbidden in imported.lower()
                        for imported in imports
                        for forbidden in ("pyside", "sqlite", "database")
                    )
                )


class RscApplicationCompositionTests(unittest.TestCase):
    def test_factory_composes_session_with_rsc_application(self):
        with TemporaryDirectory() as temporary_directory:
            created = ProjectManager().create_project(
                "RSC", Path(temporary_directory)
            )
            created.application = "rsc"
            application = RscApplication()

            session = ProjectSessionFactory(
                ApplicationRegistry([application])
            ).create(created)

            self.assertIs(session.application, application)

    def test_factory_creates_exactly_one_rsc_session(self):
        with TemporaryDirectory() as temporary_directory:
            project = ProjectManager().create_project(
                "RSC",
                Path(temporary_directory),
                application_id="rsc",
            )
            application = RscApplication()

            with patch.object(
                application,
                "create_session",
                wraps=application.create_session,
            ) as create_session:
                session = ProjectSessionFactory(
                    ApplicationRegistry([application])
                ).create(project)

            create_session.assert_called_once()
            self.assertIs(
                session.rsc_session,
                session.platform_session
                .application_runtime.application_session,
            )

    def test_factory_does_not_import_rsc_application(self):
        source = (
            Path(__file__).parents[1]
            / "core"
            / "project_session_factory.py"
        ).read_text(encoding="utf-8")

        self.assertNotIn("RscApplication", source)
        self.assertNotIn("applications.rsc", source)
        self.assertNotIn("_create_rsc_session", source)
        self.assertNotIn("RSC_APPLICATION_ID", source)

    def test_desktop_composition_root_discovers_rsc_without_direct_import(self):
        source = (
            Path(__file__).parents[1]
            / "core"
            / "application.py"
        ).read_text(encoding="utf-8")

        self.assertIn("ApplicationCatalog.discover()", source)
        self.assertNotIn("RscApplication", source)
        self.assertNotIn("from applications", source)
        self.assertIn(
            "ProjectSessionFactory(", source
        )


if __name__ == "__main__":
    unittest.main()
