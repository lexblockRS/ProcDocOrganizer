import ast
from pathlib import Path
import unittest

from applications.rsc.commands import CreateProjectCommand
from applications.rsc.dto import ProjectDTO
from applications.rsc.models import Project
from applications.rsc.ports import ProjectRepository
from applications.rsc.repositories import InMemoryProjectRepository
from applications.rsc.services import CreateProjectService


class RscProjectApplicationLayerTests(unittest.TestCase):
    def setUp(self):
        self.repository = InMemoryProjectRepository()
        self.service = CreateProjectService(self.repository)

    def test_create_project_returns_dto_with_generated_id_and_initial_status(self):
        result = self.service.execute(
            CreateProjectCommand(title="Meu Projeto RSC")
        )

        self.assertIsInstance(result, ProjectDTO)
        self.assertTrue(result.project_id)
        self.assertEqual(result.title, "Meu Projeto RSC")
        self.assertEqual(result.status, "novo")

    def test_create_project_normalizes_external_spaces(self):
        result = self.service.execute(
            CreateProjectCommand(title="  Meu Projeto RSC  ")
        )

        self.assertEqual(result.title, "Meu Projeto RSC")

    def test_created_project_is_stored_and_retrievable_by_id(self):
        result = self.service.execute(
            CreateProjectCommand(title="Meu Projeto RSC")
        )

        stored = self.repository.get(result.project_id)

        self.assertIsInstance(stored, Project)
        self.assertEqual(stored.project_id, result.project_id)
        self.assertEqual(stored.title, result.title)
        self.assertEqual(stored.status, result.status)
        self.assertIsNot(stored, result)

    def test_list_all_preserves_creation_order(self):
        first = self.service.execute(
            CreateProjectCommand(title="Primeiro")
        )
        second = self.service.execute(
            CreateProjectCommand(title="Segundo")
        )

        self.assertNotEqual(first.project_id, second.project_id)
        self.assertEqual(
            tuple(
                project.project_id
                for project in self.repository.list_all()
            ),
            (first.project_id, second.project_id),
        )

    def test_empty_title_is_rejected(self):
        with self.assertRaises(ValueError):
            self.service.execute(CreateProjectCommand(title=""))

        self.assertEqual(self.repository.list_all(), ())

    def test_whitespace_only_title_is_rejected(self):
        with self.assertRaises(ValueError):
            self.service.execute(CreateProjectCommand(title="   "))

        self.assertEqual(self.repository.list_all(), ())

    def test_non_string_title_is_rejected(self):
        with self.assertRaises(TypeError):
            self.service.execute(CreateProjectCommand(title=123))

        self.assertEqual(self.repository.list_all(), ())

    def test_repository_instances_do_not_share_projects(self):
        self.service.execute(
            CreateProjectCommand(title="Meu Projeto RSC")
        )
        other_repository = InMemoryProjectRepository()

        self.assertEqual(other_repository.list_all(), ())

    def test_repository_satisfies_structural_port(self):
        repository: ProjectRepository = InMemoryProjectRepository()
        project = Project(
            project_id="project-1",
            title="Meu Projeto RSC",
            status=Project.INITIAL_STATUS,
        )

        repository.add(project)

        self.assertIs(repository.get("project-1"), project)
        self.assertEqual(repository.list_all(), (project,))

    def test_service_does_not_import_in_memory_repository(self):
        path = (
            Path(__file__).parents[1]
            / "applications"
            / "rsc"
            / "services"
            / "create_project_service.py"
        )
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source)
        imported_names = {
            alias.name
            for node in ast.walk(tree)
            if isinstance(node, (ast.Import, ast.ImportFrom))
            for alias in node.names
        }

        self.assertNotIn("InMemoryProjectRepository", imported_names)
        self.assertNotIn("in_memory_project_repository", source)

    def test_project_does_not_contain_activities_yet(self):
        project = Project(
            project_id="project-1",
            title="Meu Projeto RSC",
            status=Project.INITIAL_STATUS,
        )

        self.assertFalse(hasattr(project, "activities"))


if __name__ == "__main__":
    unittest.main()
