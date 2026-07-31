from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from platform_infrastructure import (
    WorkspaceDirectory,
    WorkspaceError,
    WorkspaceFactory,
    WorkspaceLocator,
)
from platform_sdk import Project


class PlatformWorkspaceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = TemporaryDirectory()
        self.base = Path(self.temporary_directory.name)
        self.project = Project.create(
            name="Workspace Project",
            application_id="example",
        )

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def test_create_workspace_without_optional_directories(self):
        workspace = WorkspaceFactory(self.base).create(self.project)

        self.assertTrue(workspace.exists)
        self.assertIs(workspace.project, self.project)
        self.assertEqual(workspace.aggregate_id, self.project.aggregate_id)
        self.assertEqual(workspace.existing_directories(), ())
        for directory in WorkspaceDirectory:
            self.assertFalse(workspace.path(directory).exists())

    def test_create_directories_on_demand(self):
        workspace = WorkspaceFactory(self.base).create(self.project)

        created = tuple(
            workspace.ensure(directory)
            for directory in WorkspaceDirectory
        )

        self.assertEqual(
            created,
            (
                workspace.documents,
                workspace.exports,
                workspace.cache,
                workspace.temp,
                workspace.settings,
                workspace.logs,
                workspace.thumbnails,
                workspace.attachments,
            ),
        )
        self.assertTrue(all(path.is_dir() for path in created))
        self.assertEqual(
            workspace.existing_directories(),
            tuple(WorkspaceDirectory),
        )

    def test_locate_existing_workspace_without_creating_children(self):
        created = WorkspaceFactory(self.base).create(self.project)
        created.ensure(WorkspaceDirectory.DOCUMENTS)

        located = WorkspaceLocator(self.base).locate(self.project)

        self.assertIsNotNone(located)
        self.assertEqual(located.root, created.root)
        self.assertIs(located.project, self.project)
        self.assertEqual(
            located.existing_directories(),
            (WorkspaceDirectory.DOCUMENTS,),
        )

    def test_reopen_workspace_with_new_snapshot_of_same_project(self):
        created = WorkspaceFactory(self.base).create(self.project)
        revised = self.project.rename("Workspace reaberto")

        reopened = WorkspaceLocator(self.base).locate(revised)

        self.assertEqual(reopened.root, created.root)
        self.assertIs(reopened.project, revised)
        self.assertEqual(reopened.aggregate_id, created.aggregate_id)

    def test_missing_workspace_is_not_created_by_locator(self):
        locator = WorkspaceLocator(self.base)

        self.assertIsNone(locator.locate(self.project))
        self.assertFalse(locator.path_for(self.project).exists())

    def test_delete_temporary_workspace(self):
        workspace = WorkspaceFactory(self.base).create_temporary(
            self.project
        )
        workspace.ensure(WorkspaceDirectory.TEMP)
        root = workspace.root

        workspace.delete_temporary()

        self.assertFalse(root.exists())
        self.assertFalse(workspace.exists)

    def test_permanent_workspace_cannot_be_deleted_by_api(self):
        workspace = WorkspaceFactory(self.base).create(self.project)

        with self.assertRaises(WorkspaceError):
            workspace.delete_temporary()

        self.assertTrue(workspace.exists)


if __name__ == "__main__":
    unittest.main()
