import ast
from pathlib import Path
import unittest

from applications.rsc.commands import CreateActivityCommand
from applications.rsc.dto import ActivityDTO
from applications.rsc.models import Activity
from applications.rsc.ports import ActivityRepository
from applications.rsc.repositories import InMemoryActivityRepository
from applications.rsc.services import CreateActivityService


class RscApplicationLayerTests(unittest.TestCase):
    def setUp(self):
        self.repository = InMemoryActivityRepository()
        self.service = CreateActivityService(self.repository)

    def test_create_activity_returns_dto_with_generated_id_and_initial_state(self):
        result = self.service.execute(
            CreateActivityCommand(description="Fiscalização")
        )

        self.assertIsInstance(result, ActivityDTO)
        self.assertTrue(result.activity_id)
        self.assertEqual(result.description, "Fiscalização")
        self.assertEqual(result.state, "lembrada")

    def test_create_activity_normalizes_external_spaces(self):
        result = self.service.execute(
            CreateActivityCommand(description="  Fiscalização  ")
        )

        self.assertEqual(result.description, "Fiscalização")

    def test_created_activity_is_stored_and_retrievable_by_id(self):
        result = self.service.execute(
            CreateActivityCommand(description="Fiscalização")
        )

        stored = self.repository.get(result.activity_id)

        self.assertIsInstance(stored, Activity)
        self.assertEqual(stored.activity_id, result.activity_id)
        self.assertEqual(stored.description, result.description)
        self.assertEqual(stored.state, result.state)
        self.assertIsNot(stored, result)

    def test_list_all_preserves_creation_order(self):
        first = self.service.execute(
            CreateActivityCommand(description="Primeira")
        )
        second = self.service.execute(
            CreateActivityCommand(description="Segunda")
        )

        self.assertNotEqual(first.activity_id, second.activity_id)
        self.assertEqual(
            tuple(
                activity.activity_id
                for activity in self.repository.list_all()
            ),
            (first.activity_id, second.activity_id),
        )

    def test_empty_description_is_rejected(self):
        with self.assertRaises(ValueError):
            self.service.execute(
                CreateActivityCommand(description="")
            )

        self.assertEqual(self.repository.list_all(), ())

    def test_whitespace_only_description_is_rejected(self):
        with self.assertRaises(ValueError):
            self.service.execute(
                CreateActivityCommand(description="   ")
            )

        self.assertEqual(self.repository.list_all(), ())

    def test_non_string_description_is_rejected(self):
        with self.assertRaises(TypeError):
            self.service.execute(
                CreateActivityCommand(description=123)
            )

        self.assertEqual(self.repository.list_all(), ())

    def test_repository_instances_do_not_share_activities(self):
        self.service.execute(
            CreateActivityCommand(description="Fiscalização")
        )
        other_repository = InMemoryActivityRepository()

        self.assertEqual(other_repository.list_all(), ())

    def test_repository_satisfies_structural_port(self):
        repository: ActivityRepository = InMemoryActivityRepository()
        activity = Activity(
            activity_id="activity-1",
            description="Fiscalização",
            state=Activity.INITIAL_STATE,
        )

        repository.add(activity)

        self.assertIs(repository.get("activity-1"), activity)
        self.assertEqual(repository.list_all(), (activity,))

    def test_service_does_not_import_in_memory_repository(self):
        path = (
            Path(__file__).parents[1]
            / "applications"
            / "rsc"
            / "services"
            / "create_activity_service.py"
        )
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source)
        imported_names = {
            alias.name
            for node in ast.walk(tree)
            if isinstance(node, (ast.Import, ast.ImportFrom))
            for alias in node.names
        }

        self.assertNotIn("InMemoryActivityRepository", imported_names)
        self.assertNotIn("in_memory_activity_repository", source)


if __name__ == "__main__":
    unittest.main()
