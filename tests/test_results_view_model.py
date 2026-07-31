from __future__ import annotations

from dataclasses import FrozenInstanceError
from decimal import Decimal
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from applications.rsc.normative_catalog import OFFICIAL_NORMATIVE_CATALOG
from applications.rsc.results_view_model import ResultsViewModel
from applications.rsc.services.rsc_execution_service import (
    RSCExecutionService,
)
from database import (
    SQLiteEvidenceStore,
    SQLiteExecutionBindingStore,
    SQLiteExecutionFactStore,
)
from platform_sdk import (
    Document,
    Evidence,
    ExecutionBinding,
    ExecutionFact,
    Project,
)


class ResultsViewModelTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = TemporaryDirectory()
        path = Path(self.temporary_directory.name) / "results.sqlite"
        self.project = Project.create(name="Resultado", application_id="rsc")
        self.evidence_store = SQLiteEvidenceStore(path)
        self.fact_store = SQLiteExecutionFactStore(path)
        self.binding_store = SQLiteExecutionBindingStore(path)

    def tearDown(self) -> None:
        self.binding_store.close()
        self.fact_store.close()
        self.evidence_store.close()
        self.temporary_directory.cleanup()

    def _process(self, *, with_document: bool = True):
        evidence = Evidence.create(
            project_id=self.project.aggregate_id,
            title="Portaria 231",
            description="Participação em comissão",
        )
        if with_document:
            evidence = evidence.add_document(Document(
                document_id="portaria-231",
                name="portaria231.pdf",
                relative_path="documents/portaria231.pdf",
                document_type="application/pdf",
            ))
        fact = ExecutionFact.create(
            project_id=self.project.aggregate_id,
            evidence_id=evidence.aggregate_id,
            fact_type="PARTICIPACAO",
            description="Participação em comissão",
            quantity=Decimal("3"),
            unit="Por evento",
        )
        definition = OFFICIAL_NORMATIVE_CATALOG.find(
            "DEC13048-ANX-II-ITEM-07"
        )
        binding = ExecutionBinding.create(
            execution_fact_id=fact.aggregate_id,
            criterion_id=definition.code,
            requirement_id=definition.requirement_id,
            execution_rule_id=definition.execution_rule_id,
        )
        self.evidence_store.save(evidence)
        self.fact_store.save(fact)
        self.binding_store.save(binding)
        return RSCExecutionService(
            self.evidence_store,
            self.fact_store,
            self.binding_store,
        ).execute(self.project).process

    def test_projects_complete_navigation_tree_without_mutating_process(self):
        process = self._process()
        snapshot = process

        summary = ResultsViewModel(process).summary

        requirement = summary.requirements[0]
        criterion = requirement.criteria[0]
        fact = criterion.execution_fact
        self.assertEqual(summary.status, "CONSOLIDATED")
        self.assertEqual(summary.total_score, Decimal("9"))
        self.assertEqual(requirement.total_score, Decimal("9"))
        self.assertEqual(
            criterion.criterion_id, "DEC13048-ANX-II-ITEM-07"
        )
        self.assertEqual(fact.description, "Participação em comissão")
        self.assertEqual(fact.evidence.description, "Participação em comissão")
        self.assertEqual(
            fact.evidence.documents[0].name, "portaria231.pdf"
        )
        self.assertIs(process, snapshot)

    def test_dtos_are_immutable(self):
        summary = ResultsViewModel(self._process()).summary

        with self.assertRaises(FrozenInstanceError):
            summary.status = "ALTERED"
        with self.assertRaises(FrozenInstanceError):
            summary.requirements[0].criteria[0].score = Decimal("0")

    def test_evidence_without_document_is_explicit(self):
        summary = ResultsViewModel(
            self._process(with_document=False)
        ).summary

        evidence = (
            summary.requirements[0]
            .criteria[0]
            .execution_fact.evidence
        )
        self.assertEqual(evidence.documents, ())


if __name__ == "__main__":
    unittest.main()
