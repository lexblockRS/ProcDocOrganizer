from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from database import ProjectNotFoundError, SQLiteProjectStore
from platform_sdk import Project, ProjectResource, ProjectState


class PlatformProjectPersistenceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = TemporaryDirectory()
        self.database_path = (
            Path(self.temporary_directory.name) / "projects.sqlite"
        )

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def test_saves_and_reopens_empty_project(self):
        project = Project.create(
            name="Projeto vazio",
            application_id="example",
        )
        with SQLiteProjectStore(self.database_path) as store:
            store.save(project)

        with SQLiteProjectStore(self.database_path) as reopened_store:
            reopened = reopened_store.get(project.project_id)

        self.assertEqual(reopened, project)
        self.assertEqual(reopened.aggregate_id, project.aggregate_id)
        self.assertEqual(reopened.resources, ())
        self.assertEqual(reopened.metadata, ())

    def test_saves_active_project_with_metadata_and_resources(self):
        project = (
            Project.create(
                name="Projeto ativo",
                application_id="rsc",
                metadata=(("campus", "Bagé"), ("priority", 2)),
            )
            .add_resource(ProjectResource(
                resource_id="document-1",
                resource_type="document",
                reference="opaque:document-1",
                metadata=(("available", True),),
            ))
            .change_state(ProjectState.ACTIVE)
        )

        with SQLiteProjectStore(self.database_path) as store:
            store.save(project)
            reopened = store.get(project.project_id)

        self.assertEqual(reopened.state, ProjectState.ACTIVE)
        self.assertEqual(reopened.application_id, "rsc")
        self.assertEqual(reopened.metadata, project.metadata)
        self.assertEqual(reopened.resources, project.resources)
        self.assertEqual(reopened.revision, project.revision)

    def test_open_preserves_all_persisted_identity_fields(self):
        project = Project.create(
            name="Identidade",
            application_id="asset.audit",
        ).change_state(ProjectState.ACTIVE)

        with SQLiteProjectStore(self.database_path) as store:
            store.save(project)
            reopened = store.get(project.aggregate_id)

        self.assertEqual(reopened.project_id, project.project_id)
        self.assertEqual(reopened.aggregate_id, project.aggregate_id)
        self.assertEqual(reopened.revision, project.revision)
        self.assertEqual(reopened.state, project.state)
        self.assertEqual(reopened.application_id, project.application_id)

    def test_stores_multiple_projects_independently(self):
        projects = (
            Project.create(name="Alpha", application_id="app.alpha"),
            Project.create(name="Beta", application_id="app.beta"),
            Project.create(name="Gamma", application_id="app.gamma"),
        )

        with SQLiteProjectStore(self.database_path) as store:
            for project in projects:
                store.save(project)
            reopened = store.list_all()

        self.assertEqual(
            {item.aggregate_id for item in reopened},
            {item.aggregate_id for item in projects},
        )
        self.assertEqual(len(reopened), 3)

    def test_save_updates_revision_of_existing_project(self):
        original = Project.create(
            name="Original",
            application_id="example",
        )
        revised = (
            original.rename("Revisado")
            .change_state(ProjectState.ACTIVE)
        )

        with SQLiteProjectStore(self.database_path) as store:
            store.save(original)
            store.save(revised)
            reopened = store.get(original.project_id)
            all_projects = store.list_all()

        self.assertEqual(len(all_projects), 1)
        self.assertEqual(reopened.name, "Revisado")
        self.assertEqual(reopened.revision, 2)
        self.assertEqual(reopened.aggregate_id, original.aggregate_id)

    def test_open_missing_project_raises_specific_error(self):
        with SQLiteProjectStore(self.database_path) as store:
            with self.assertRaises(ProjectNotFoundError):
                store.get("4f8c9428-7f08-4687-a5ac-0b36ee56e914")


if __name__ == "__main__":
    unittest.main()
