import ast
from pathlib import Path
from types import SimpleNamespace
from tempfile import TemporaryDirectory
import unittest

from core.project_controller import ProjectController
from core.project_manager import ProjectManager
from core.project_session import ProjectSession
from core.project_session_factory import ProjectSessionFactory


class ServiceControllerSpy:
    def __init__(self, *, can_leave=True):
        self.service = None
        self.services = []
        self._can_leave = can_leave

    def set_service(self, service):
        self.service = service
        self.services.append(service)

    def set_search_service(self, service):
        self.set_service(service)

    def load(self):
        return True

    def can_leave(self):
        return self._can_leave


class StateSpy:
    def __init__(self, project=None):
        self.current_project = project

    @property
    def has_project(self):
        return self.current_project is not None

    def open_project(self, project):
        self.current_project = project

    def close_project(self):
        self.current_project = None


class WindowSpy:
    def __init__(self):
        self.projects = []
        self.clear_count = 0

    def set_project(self, project, documents):
        self.projects.append((project, tuple(documents)))

    def clear_project(self):
        self.clear_count += 1


class ContributionInstallerSpy:
    def __init__(self):
        self.calls = []

    def install(self, contributions):
        self.calls.append(("install", tuple(contributions)))

    def replace(self, contributions):
        self.calls.append(("replace", tuple(contributions)))

    def clear(self):
        self.calls.append(("clear",))


def session(project, marker, application=None):
    return SimpleNamespace(
        project=project,
        document_repository=SimpleNamespace(
            list_documents=lambda: (f"document-{marker}",)
        ),
        document_service=object(),
        search_service=object(),
        evidence_service=object(),
        application=application,
    )


def controller_for_session_tests(factory, active_session=None):
    controller = ProjectController.__new__(ProjectController)
    controller.session_factory = factory
    controller.session = active_session
    controller.state = StateSpy(
        active_session.project if active_session is not None else None
    )
    controller.window = WindowSpy()
    controller.selected_document = object()
    controller.search_controller = ServiceControllerSpy()
    controller.documents_controller = ServiceControllerSpy()
    controller.evidence_controller = ServiceControllerSpy()
    controller.contribution_installer = ContributionInstallerSpy()
    return controller


class ProjectSessionFactoryTests(unittest.TestCase):
    def test_factory_creates_complete_session(self):
        with TemporaryDirectory() as temporary_directory:
            project = ProjectManager().create_project(
                "Projeto", Path(temporary_directory)
            )

            created = ProjectSessionFactory().create(project)

            self.assertIsInstance(created, ProjectSession)
            self.assertIs(created.project, project)
            self.assertIs(
                created.document_service.document_repository,
                created.document_repository,
            )
            self.assertIsNotNone(created.search_service)
            self.assertIsNotNone(created.evidence_service)

    def test_projects_receive_distinct_session_dependencies(self):
        with TemporaryDirectory() as temporary_directory:
            manager = ProjectManager()
            first_project = manager.create_project(
                "Primeiro", Path(temporary_directory)
            )
            second_project = manager.create_project(
                "Segundo", Path(temporary_directory)
            )
            factory = ProjectSessionFactory()

            first = factory.create(first_project)
            second = factory.create(second_project)

            for attribute in (
                "document_repository",
                "document_service",
                "search_service",
                "evidence_service",
            ):
                self.assertIsNot(
                    getattr(first, attribute),
                    getattr(second, attribute),
                )

    def test_session_and_factory_do_not_depend_on_pyside(self):
        root = Path(__file__).parents[1]
        for relative_path in (
            "core/project_session.py",
            "core/project_session_factory.py",
        ):
            with self.subTest(path=relative_path):
                source = (root / relative_path).read_text(encoding="utf-8")
                self.assertNotIn("PySide6", source)

    def test_project_controller_does_not_compose_concrete_session_dependencies(self):
        source = (
            Path(__file__).parents[1] / "core" / "project_controller.py"
        ).read_text(encoding="utf-8")
        tree = ast.parse(source)
        imported_names = {
            alias.name
            for node in ast.walk(tree)
            if isinstance(node, (ast.Import, ast.ImportFrom))
            for alias in node.names
        }
        forbidden = {
            "DocumentRepository",
            "DocumentService",
            "EvidenceService",
            "SearchDocumentSourceResolver",
            "SQLiteEvidenceRepository",
            "SearchService",
            "SqliteFtsSearchIndex",
            "ProcessingRepository",
        }
        self.assertTrue(forbidden.isdisjoint(imported_names))


class ProjectSessionLifecycleTests(unittest.TestCase):
    def test_factory_failure_does_not_partially_replace_active_session(self):
        old_project = object()
        old_session = session(old_project, "old")

        class FailingFactory:
            def create(self, _project):
                raise RuntimeError("falha de composição")

        controller = controller_for_session_tests(FailingFactory(), old_session)

        with self.assertRaises(RuntimeError):
            controller._load_project(object())

        self.assertIs(controller.session, old_session)
        self.assertIs(controller.state.current_project, old_project)
        self.assertEqual(controller.search_controller.services, [])
        self.assertEqual(controller.documents_controller.services, [])
        self.assertEqual(controller.evidence_controller.services, [])
        self.assertEqual(controller.window.projects, [])

    def test_switch_activates_only_dependencies_from_new_session(self):
        old_project, new_project = object(), object()
        old_session = session(old_project, "old")
        new_session = session(new_project, "new")
        factory = SimpleNamespace(create=lambda project: new_session)
        controller = controller_for_session_tests(factory, old_session)

        controller._load_project(new_project)

        self.assertIs(controller.session, new_session)
        self.assertIs(controller.state.current_project, new_project)
        self.assertEqual(
            controller.search_controller.services,
            [new_session.search_service],
        )
        self.assertEqual(
            controller.documents_controller.services,
            [new_session.document_service],
        )
        self.assertEqual(
            controller.evidence_controller.services,
            [new_session.evidence_service],
        )
        self.assertIsNone(controller.selected_document)

    def test_close_clears_controller_references_and_active_session(self):
        project = object()
        active = session(project, "active")
        controller = controller_for_session_tests(
            SimpleNamespace(create=lambda project: active),
            active,
        )

        controller.close_project()

        self.assertIsNone(controller.session)
        self.assertIsNone(controller.state.current_project)
        self.assertIsNone(controller.selected_document)
        self.assertIsNone(controller.search_controller.service)
        self.assertIsNone(controller.documents_controller.service)
        self.assertIsNone(controller.evidence_controller.service)
        self.assertEqual(controller.window.clear_count, 1)

    def test_close_cancel_preserves_session_and_dependencies(self):
        project = object()
        active = session(project, "active")
        controller = controller_for_session_tests(
            SimpleNamespace(create=lambda project: active),
            active,
        )
        controller.evidence_controller._can_leave = False

        controller.close_project()

        self.assertIs(controller.session, active)
        self.assertIs(controller.state.current_project, project)
        self.assertEqual(controller.window.clear_count, 0)


if __name__ == "__main__":
    unittest.main()
