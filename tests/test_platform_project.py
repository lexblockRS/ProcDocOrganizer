from __future__ import annotations

from dataclasses import FrozenInstanceError
from uuid import uuid4
import unittest

from platform_sdk import (
    Project,
    ProjectError,
    ProjectResource,
    ProjectState,
)


class PlatformProjectTests(unittest.TestCase):
    def test_creation_preserves_owner_metadata_and_initial_state(self):
        project = Project.create(
            name="Projeto Geral",
            application_id="example.application",
            metadata=(("department", "Acadêmico"), ("priority", 1)),
        )

        self.assertEqual(project.name, "Projeto Geral")
        self.assertEqual(project.application_id, "example.application")
        self.assertEqual(project.state, ProjectState.DRAFT)
        self.assertEqual(project.resources, ())
        self.assertEqual(project.revision, 0)
        self.assertEqual(project.aggregate_id, project.project_id)
        with self.assertRaises(FrozenInstanceError):
            project.name = "Alterado"

    def test_rename_creates_revision_of_same_project(self):
        project = Project.create(
            name="Original",
            application_id="example",
        )

        renamed = project.rename("Novo nome")

        self.assertEqual(project.name, "Original")
        self.assertEqual(renamed.name, "Novo nome")
        self.assertEqual(renamed.revision, 1)
        self.assertTrue(project.same_project(renamed))

    def test_state_change_obeys_lifecycle(self):
        project = Project.create(name="Projeto", application_id="example")

        active = project.change_state(ProjectState.ACTIVE)
        suspended = active.change_state(ProjectState.SUSPENDED)
        resumed = suspended.change_state(ProjectState.ACTIVE)
        archived = resumed.change_state(ProjectState.ARCHIVED)

        self.assertEqual(archived.state, ProjectState.ARCHIVED)
        self.assertEqual(archived.revision, 4)
        with self.assertRaises(ProjectError):
            archived.change_state(ProjectState.ACTIVE)
        with self.assertRaises(ProjectError):
            project.change_state(ProjectState.SUSPENDED)

    def test_application_association_is_required_and_stable(self):
        project = Project.create(name="Projeto", application_id="app.one")

        renamed = project.rename("Renomeado")

        self.assertEqual(renamed.application_id, "app.one")
        with self.assertRaises(ValueError):
            Project.create(name="Projeto", application_id=" ")

    def test_resources_are_owned_without_infrastructure_knowledge(self):
        project = Project.create(name="Projeto", application_id="example")
        resource = ProjectResource(
            resource_id="document-1",
            resource_type="document",
            reference="opaque:document-1",
        )

        associated = project.add_resource(resource)
        removed = associated.remove_resource("document-1")

        self.assertEqual(associated.resources, (resource,))
        self.assertEqual(removed.resources, ())
        self.assertEqual(removed.revision, 2)

    def test_equality_and_hash_use_identity_not_snapshot_state(self):
        project_id = str(uuid4())
        first = Project.create(
            project_id=project_id,
            name="Primeiro snapshot",
            application_id="example",
        )
        second = Project(
            project_id=project_id,
            name="Outro snapshot",
            application_id="example",
            revision=7,
        )
        different = Project.create(
            name="Primeiro snapshot",
            application_id="example",
        )

        self.assertEqual(first, second)
        self.assertEqual(hash(first), hash(second))
        self.assertNotEqual(first, different)
        self.assertTrue(first.same_project(second))


if __name__ == "__main__":
    unittest.main()
