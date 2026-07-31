from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from applications.rsc.normative_catalog import OFFICIAL_NORMATIVE_CATALOG
from database import (
    ExecutionBindingNotFoundError,
    SQLiteEvidenceStore,
    SQLiteExecutionBindingStore,
    SQLiteExecutionFactStore,
)
from platform_sdk import (
    BindingOrigin,
    Evidence,
    ExecutionBinding,
    ExecutionFact,
    Project,
)


class ExecutionBindingTests(unittest.TestCase):
    def setUp(self) -> None:
        self.fact_id = "f2d3d943-423d-4c3f-916b-468b7ae16bdb"
        self.first = OFFICIAL_NORMATIVE_CATALOG.criteria[0]
        self.second = OFFICIAL_NORMATIVE_CATALOG.criteria[1]
        self.created_at = datetime(2026, 7, 30, tzinfo=timezone.utc)
        self.binding = ExecutionBinding.create(
            execution_fact_id=self.fact_id,
            criterion_id=self.first.code,
            requirement_id=self.first.requirement_id,
            execution_rule_id=self.first.execution_rule_id,
            metadata=(("responsável", "usuário"),),
            now=self.created_at,
        )

    def test_create_manual_binding(self):
        self.assertEqual(self.binding.origin, BindingOrigin.MANUAL)
        self.assertEqual(self.binding.execution_fact_id, self.fact_id)
        self.assertEqual(self.binding.criterion_id, self.first.code)

    def test_rebind_preserves_identity_and_creation_time(self):
        updated = self.binding.rebind(
            criterion_id=self.second.code,
            requirement_id=self.second.requirement_id,
            execution_rule_id=self.second.execution_rule_id,
        )

        self.assertTrue(updated.same_binding(self.binding))
        self.assertEqual(updated.created_at, self.binding.created_at)
        self.assertEqual(updated.criterion_id, self.second.code)


class SQLiteExecutionBindingStoreTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = TemporaryDirectory()
        self.database_path = Path(
            self.temporary_directory.name
        ) / "projects.sqlite"
        self.project = Project.create(name="Processo", application_id="rsc")
        self.evidence = Evidence.create(
            project_id=self.project.aggregate_id,
            title="Portaria",
        )
        self.fact = ExecutionFact.create(
            project_id=self.project.aggregate_id,
            evidence_id=self.evidence.aggregate_id,
            fact_type="DESIGNACAO",
            description="Designação",
            quantity=Decimal("1"),
            unit="evento",
        )
        with SQLiteEvidenceStore(self.database_path) as store:
            store.save(self.evidence)
        with SQLiteExecutionFactStore(self.database_path) as store:
            store.save(self.fact)

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def _binding(self) -> ExecutionBinding:
        definition = OFFICIAL_NORMATIVE_CATALOG.criteria[0]
        return ExecutionBinding.create(
            execution_fact_id=self.fact.aggregate_id,
            criterion_id=definition.code,
            requirement_id=definition.requirement_id,
            execution_rule_id=definition.execution_rule_id,
            metadata=(("origem", "seleção manual"),),
        )

    def test_persist_edit_and_reopen_preserve_links(self):
        binding = self._binding()
        replacement = OFFICIAL_NORMATIVE_CATALOG.criteria[1]

        with SQLiteExecutionBindingStore(self.database_path) as store:
            store.save(binding)
            updated = binding.rebind(
                criterion_id=replacement.code,
                requirement_id=replacement.requirement_id,
                execution_rule_id=replacement.execution_rule_id,
            )
            store.save(updated)
        with SQLiteExecutionBindingStore(self.database_path) as reopened:
            restored = reopened.get_for_fact(self.fact.aggregate_id)

        self.assertIsNotNone(restored)
        self.assertTrue(restored.same_binding(binding))
        self.assertEqual(restored.execution_fact_id, self.fact.aggregate_id)
        self.assertEqual(restored.criterion_id, replacement.code)
        self.assertEqual(restored.requirement_id, replacement.requirement_id)
        self.assertEqual(
            restored.execution_rule_id,
            replacement.execution_rule_id,
        )
        self.assertEqual(restored.metadata, binding.metadata)

    def test_remove_binding_does_not_change_execution_fact(self):
        binding = self._binding()
        fact_snapshot = self.fact

        with SQLiteExecutionBindingStore(self.database_path) as store:
            store.save(binding)
            store.delete(binding.aggregate_id)
            self.assertIsNone(
                store.get_for_fact(self.fact.aggregate_id)
            )
            with self.assertRaises(ExecutionBindingNotFoundError):
                store.get(binding.aggregate_id)
        with SQLiteExecutionFactStore(self.database_path) as fact_store:
            restored_fact = fact_store.get(self.fact.aggregate_id)

        self.assertEqual(restored_fact, fact_snapshot)


if __name__ == "__main__":
    unittest.main()
