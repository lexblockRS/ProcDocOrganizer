from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from database import (
    ExecutionFactNotFoundError,
    SQLiteEvidenceStore,
    SQLiteExecutionFactStore,
)
from platform_sdk import Evidence, ExecutionFact, Project


class ExecutionFactAggregateTests(unittest.TestCase):
    def setUp(self) -> None:
        self.project = Project.create(name="Processo", application_id="rsc")
        self.evidence = Evidence.create(
            project_id=self.project.aggregate_id,
            title="Portaria",
        )
        self.timestamp = datetime(2026, 7, 30, tzinfo=timezone.utc)
        self.fact = ExecutionFact.create(
            project_id=self.project.aggregate_id,
            evidence_id=self.evidence.aggregate_id,
            fact_type="DESIGNACAO",
            description="Designação para função",
            quantity=Decimal("1.5"),
            unit="ocorrência",
            period_start=date(2024, 1, 1),
            period_end=date(2025, 1, 1),
            metadata=(("fonte", "manual"),),
            now=self.timestamp,
        )

    def test_create_and_edit_preserve_identity(self):
        updated = self.fact.edit(
            description="Designação atualizada",
            quantity=Decimal("2"),
            now=self.timestamp + timedelta(minutes=1),
        )

        self.assertTrue(updated.same_execution_fact(self.fact))
        self.assertEqual(updated.aggregate_id, self.fact.aggregate_id)
        self.assertEqual(updated.created_at, self.fact.created_at)
        self.assertEqual(updated.quantity, Decimal("2"))
        self.assertGreater(updated.updated_at, self.fact.updated_at)

    def test_fact_references_evidence_and_not_document(self):
        self.assertEqual(
            self.fact.evidence_id, self.evidence.aggregate_id
        )
        self.assertEqual(self.fact.project_id, self.project.aggregate_id)
        self.assertFalse(hasattr(self.fact, "document_id"))
        self.assertFalse(hasattr(self.fact, "score"))
        self.assertFalse(hasattr(self.fact, "criterion_id"))

    def test_period_cannot_be_inverted(self):
        with self.assertRaises(ValueError):
            ExecutionFact.create(
                project_id=self.project.aggregate_id,
                evidence_id=self.evidence.aggregate_id,
                fact_type="PERIODO",
                description="Período inválido",
                unit="ano",
                period_start=date(2025, 1, 1),
                period_end=date(2024, 1, 1),
            )


class SQLiteExecutionFactStoreTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = TemporaryDirectory()
        self.database_path = Path(
            self.temporary_directory.name
        ) / "projects.sqlite"
        self.project = Project.create(name="Processo", application_id="rsc")
        self.evidence = Evidence.create(
            project_id=self.project.aggregate_id,
            title="Certidão",
        )
        with SQLiteEvidenceStore(self.database_path) as evidence_store:
            evidence_store.save(self.evidence)

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def _fact(self, description: str) -> ExecutionFact:
        return ExecutionFact.create(
            project_id=self.project.aggregate_id,
            evidence_id=self.evidence.aggregate_id,
            fact_type="ATIVIDADE",
            description=description,
            quantity=Decimal("2.75"),
            unit="atividade",
            period_start=date(2023, 2, 1),
            period_end=date(2024, 8, 1),
            metadata=(("revisado", False),),
        )

    def test_persist_and_reopen_restores_exact_state(self):
        fact = self._fact("Atividade registrada")

        with SQLiteExecutionFactStore(self.database_path) as store:
            store.save(fact)
        with SQLiteExecutionFactStore(self.database_path) as reopened_store:
            reopened = reopened_store.get(fact.aggregate_id)

        self.assertTrue(reopened.same_execution_fact(fact))
        self.assertEqual(reopened.project_id, fact.project_id)
        self.assertEqual(reopened.evidence_id, fact.evidence_id)
        self.assertEqual(reopened.quantity, Decimal("2.75"))
        self.assertEqual(reopened.period_start, fact.period_start)
        self.assertEqual(reopened.period_end, fact.period_end)
        self.assertEqual(reopened.metadata, fact.metadata)
        self.assertEqual(reopened.created_at, fact.created_at)
        self.assertEqual(reopened.updated_at, fact.updated_at)

    def test_multiple_facts_for_same_evidence_and_delete(self):
        first = self._fact("Primeira")
        second = self._fact("Segunda")

        with SQLiteExecutionFactStore(self.database_path) as store:
            store.save(first)
            store.save(second)
            self.assertEqual(
                set(store.list_for_evidence(self.evidence.aggregate_id)),
                {first, second},
            )
            store.delete(first.aggregate_id)
            with self.assertRaises(ExecutionFactNotFoundError):
                store.get(first.aggregate_id)
            self.assertEqual(
                store.list_for_evidence(self.evidence.aggregate_id),
                (second,),
            )


if __name__ == "__main__":
    unittest.main()
