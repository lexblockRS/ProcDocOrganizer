from dataclasses import FrozenInstanceError
import unittest

from presentation import (
    NavigationIntentType,
    PresentationAction,
    RelationshipType,
    Resource,
    ResourceDisplay,
    ResourceIdentity,
    ResourceInspectorState,
    ResourceInspectorViewModel,
    ResourceRelationship,
    ResourceType,
)


class ResourceInspectorViewModelTests(unittest.TestCase):
    def test_projects_common_information_relationships_and_actions(self):
        evidence = ResourceIdentity(ResourceType.EVIDENCE, "ev-1")
        resource = Resource(
            ResourceIdentity(ResourceType.DOCUMENT, "doc-1"),
            ResourceDisplay(
                "Portaria", "available", {"pages": 2, "reviewed": True}
            ),
            (ResourceRelationship(
                RelationshipType.USED_BY, evidence, "Comprova"
            ),),
            (PresentationAction.OPEN, PresentationAction.COPY_IDENTIFIER),
        )

        data = ResourceInspectorViewModel.from_resource(resource).data

        self.assertIs(data.state, ResourceInspectorState.READY)
        self.assertEqual(data.resource_type, "document")
        self.assertEqual(data.resource_id, "doc-1")
        self.assertEqual(data.display_name, "Portaria")
        self.assertEqual(data.status, "available")
        self.assertEqual(
            tuple(item.label for item in data.metadata),
            ("pages", "reviewed"),
        )
        self.assertIs(
            data.relationships[0].intent.intent_type,
            NavigationIntentType.OPEN_EVIDENCE,
        )
        self.assertEqual(data.relationships[0].intent.target_id, "ev-1")
        self.assertIs(
            data.actions[0].intent.intent_type,
            NavigationIntentType.OPEN_DOCUMENT,
        )
        self.assertEqual(
            data.actions[1].intent.metadata["action"], "copy_identifier"
        )

    def test_empty_unavailable_and_absent_optional_sections(self):
        empty = ResourceInspectorViewModel.empty().data
        unavailable = ResourceInspectorViewModel.unavailable(
            ResourceIdentity(ResourceType.REQUIREMENT, "req-1")
        ).data
        minimal = ResourceInspectorViewModel.from_resource(Resource(
            ResourceIdentity(ResourceType.EVIDENCE, "ev-1"),
            ResourceDisplay("Evidence"),
        )).data

        self.assertIs(empty.state, ResourceInspectorState.EMPTY)
        self.assertIn("Nenhum", empty.message)
        self.assertIs(
            unavailable.state, ResourceInspectorState.UNAVAILABLE
        )
        self.assertEqual(unavailable.resource_id, "req-1")
        self.assertEqual(minimal.metadata, ())
        self.assertEqual(minimal.relationships, ())
        self.assertEqual(minimal.actions, ())

    def test_inspector_dtos_are_immutable(self):
        data = ResourceInspectorViewModel.empty().data
        with self.assertRaises(FrozenInstanceError):
            data.message = "Alterado"


if __name__ == "__main__":
    unittest.main()
