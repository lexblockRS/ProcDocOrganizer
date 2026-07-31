from dataclasses import FrozenInstanceError
from datetime import datetime, timezone
import unittest

from presentation import (
    Insight,
    InsightAction,
    InsightCategory,
    InsightCollection,
    InsightContractError,
    InsightIdentity,
    InsightResourceReference,
    InsightResourceRole,
    InsightSeverity,
    RelationshipType,
    Resource,
    ResourceDisplay,
    ResourceIdentity,
    ResourceType,
    serialize_insight,
    serialize_insight_collection,
)


def insight(
    code="document.unused",
    *,
    severity=InsightSeverity.WARNING,
    category=InsightCategory.ORGANIZATION,
    revision=3,
):
    return Insight(
        InsightIdentity("documents", code, "doc-1"),
        category,
        severity,
        "Documento sem uso",
        "Document não utilizado.",
        "Nenhuma projeção atual referencia o Document.",
        (InsightResourceReference(
            ResourceIdentity(ResourceType.DOCUMENT, "doc-1"),
            InsightResourceRole.SUBJECT,
        ),),
        (InsightAction.OPEN_RESOURCE,),
        revision,
    )


class InsightContractTests(unittest.TestCase):
    def test_identity_is_normalized_deterministic_and_immutable(self):
        first = InsightIdentity(" documents ", " unused ", " doc-1 ")
        second = InsightIdentity("documents", "unused", "doc-1")

        self.assertEqual(first, second)
        self.assertEqual(hash(first), hash(second))
        with self.assertRaises(FrozenInstanceError):
            first.insight_code = "other"

    def test_enums_have_only_the_accepted_values(self):
        self.assertEqual(
            {item.name for item in InsightCategory},
            {"COVERAGE", "VALIDATION", "ORGANIZATION", "COMPLETENESS", "INFORMATION"},
        )
        self.assertEqual(
            {item.name for item in InsightSeverity},
            {"INFO", "WARNING", "ERROR", "SUCCESS"},
        )
        self.assertEqual(
            {item.name for item in InsightAction},
            {"OPEN_RESOURCE", "INSPECT_RESOURCE", "REVEAL_RESOURCE", "EXECUTE_EVALUATION"},
        )

    def test_resource_reference_accepts_identity_never_resource(self):
        identity = ResourceIdentity(ResourceType.EVIDENCE, "ev-1")
        reference = InsightResourceReference(
            identity, InsightResourceRole.SOURCE
        )
        self.assertIs(reference.identity, identity)

        with self.assertRaises(InsightContractError):
            InsightResourceReference(
                Resource(identity, ResourceDisplay("Evidence")),
                InsightResourceRole.SOURCE,
            )

    def test_insight_is_frozen_explainable_and_validates_references(self):
        item = insight()
        self.assertTrue(item.message)
        self.assertTrue(item.explanation)
        with self.assertRaises(FrozenInstanceError):
            item.severity = InsightSeverity.ERROR

        subject = item.related_resources[0]
        with self.assertRaises(InsightContractError):
            Insight(
                item.identity,
                item.category,
                item.severity,
                item.title,
                item.message,
                item.explanation,
                (subject, subject),
                (),
                item.source_revision,
            )

    def test_evaluation_identity_and_revision_must_coexist(self):
        item = insight()
        with self.assertRaises(InsightContractError):
            Insight(
                item.identity,
                item.category,
                item.severity,
                item.title,
                item.message,
                item.explanation,
                (),
                (),
                0,
                evaluation_id="evaluation-1",
            )

    def test_collection_orders_deterministically_and_is_immutable(self):
        info = insight(
            "project.info",
            severity=InsightSeverity.INFO,
            category=InsightCategory.INFORMATION,
        )
        error = insight(
            "project.error",
            severity=InsightSeverity.ERROR,
            category=InsightCategory.VALIDATION,
        )
        generated = datetime(2026, 7, 31, tzinfo=timezone.utc)
        collection = InsightCollection((info, error), 2, 3, generated)

        self.assertEqual(collection.insights, (error, info))
        self.assertEqual(collection.workspace_revision, 3)
        with self.assertRaises(FrozenInstanceError):
            collection.total = 3

    def test_serialization_contains_only_simple_values(self):
        item = insight()
        collection = InsightCollection((item,), 1, 3)

        serialized = serialize_insight(item)
        serialized_collection = serialize_insight_collection(collection)

        self.assertEqual(serialized["category"], "organization")
        self.assertEqual(serialized["severity"], "warning")
        self.assertEqual(
            serialized["related_resources"][0]["resource_type"],
            "document",
        )
        self.assertEqual(serialized_collection["workspace_revision"], 3)


if __name__ == "__main__":
    unittest.main()
