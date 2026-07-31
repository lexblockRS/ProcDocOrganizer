from dataclasses import FrozenInstanceError
import unittest

from presentation import (
    PresentationAction,
    RelationshipType,
    Resource,
    ResourceCollection,
    ResourceContractError,
    ResourceDisplay,
    ResourceIdentity,
    ResourceRelationship,
    ResourceType,
    serialize_resource,
    serialize_resource_collection,
)


class ResourceInfrastructureTests(unittest.TestCase):
    def setUp(self):
        self.document = ResourceIdentity(ResourceType.DOCUMENT, "doc-1")
        self.evidence = ResourceIdentity(ResourceType.EVIDENCE, "ev-1")

    def test_identity_contains_only_type_and_stable_identifier(self):
        first = ResourceIdentity(ResourceType.DOCUMENT, " doc-1 ")
        second = ResourceIdentity(ResourceType.DOCUMENT, "doc-1")

        self.assertEqual(first, second)
        self.assertEqual(first.resource_id, "doc-1")
        self.assertFalse(hasattr(first, "display_name"))
        self.assertFalse(hasattr(first, "status"))
        self.assertFalse(hasattr(first, "metadata"))
        with self.assertRaises(FrozenInstanceError):
            first.resource_id = "other"

    def test_display_metadata_is_scalar_copied_and_immutable(self):
        source = {"extension": "pdf", "pages": 3}
        display = ResourceDisplay("Portaria", "available", source)
        source["pages"] = 4

        self.assertEqual(display.metadata["pages"], 3)
        with self.assertRaises(TypeError):
            display.metadata["pages"] = 5
        with self.assertRaises(ResourceContractError):
            ResourceDisplay("Portaria", metadata={"domain": object()})

    def test_relationship_points_only_to_identity(self):
        relationship = ResourceRelationship(
            RelationshipType.USED_BY,
            self.evidence,
            "Usado pela evidência",
            {"visible": True},
        )

        self.assertIs(relationship.target_identity, self.evidence)
        with self.assertRaises(ResourceContractError):
            ResourceRelationship(
                RelationshipType.USED_BY,
                Resource(
                    self.evidence, ResourceDisplay("Evidence")
                ),
            )

    def test_resource_is_declarative_immutable_and_equal(self):
        relationship = ResourceRelationship(
            RelationshipType.USED_BY, self.evidence
        )
        first = Resource(
            self.document,
            ResourceDisplay("Documento"),
            (relationship,),
            (PresentationAction.OPEN, PresentationAction.INSPECT),
        )
        second = Resource(
            self.document,
            ResourceDisplay("Documento"),
            (relationship,),
            (PresentationAction.OPEN, PresentationAction.INSPECT),
        )

        self.assertEqual(first, second)
        self.assertFalse(hasattr(first, "__dict__"))
        with self.assertRaises(FrozenInstanceError):
            first.display = ResourceDisplay("Alterado")
        with self.assertRaises(ResourceContractError):
            Resource(
                self.document,
                ResourceDisplay("Documento"),
                available_actions=(
                    PresentationAction.OPEN,
                    PresentationAction.OPEN,
                ),
            )

    def test_actions_are_closed_declarative_values(self):
        self.assertEqual(
            tuple(PresentationAction),
            (
                PresentationAction.OPEN,
                PresentationAction.INSPECT,
                PresentationAction.REVEAL,
                PresentationAction.COPY_IDENTIFIER,
            ),
        )

    def test_collection_is_query_result_not_resource(self):
        resource = Resource(
            self.document, ResourceDisplay("Documento")
        )
        collection = ResourceCollection(
            (resource,), 5, {"page": 1, "source": "documents"}
        )

        self.assertNotIsInstance(collection, Resource)
        self.assertEqual(collection.total, 5)
        self.assertEqual(collection.resources, (resource,))
        with self.assertRaises(ResourceContractError):
            ResourceCollection((resource,), 0)

    def test_serialization_contains_only_simple_values(self):
        relationship = ResourceRelationship(
            RelationshipType.REFERENCES, self.evidence
        )
        resource = Resource(
            self.document,
            ResourceDisplay("Documento", metadata={"pages": 2}),
            (relationship,),
            (PresentationAction.OPEN,),
        )

        serialized = serialize_resource(resource)
        collection = serialize_resource_collection(
            ResourceCollection((resource,), 1)
        )

        self.assertEqual(
            serialized["identity"],
            {"resource_type": "document", "resource_id": "doc-1"},
        )
        self.assertEqual(serialized["available_actions"], ["open"])
        self.assertEqual(collection["total"], 1)


if __name__ == "__main__":
    unittest.main()
