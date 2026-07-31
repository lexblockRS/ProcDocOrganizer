from __future__ import annotations

from decimal import Decimal
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from applications.rsc.normative_catalog import OFFICIAL_NORMATIVE_CATALOG
from applications.rsc.rsc_process import RSCProcessStage
from applications.rsc.services.rsc_execution_service import (
    RSCExecutionError,
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


CRITERION_ID = "DEC13048-ANX-II-ITEM-07"


class RSCExecutionServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = TemporaryDirectory()
        self.database_path = Path(
            self.temporary_directory.name
        ) / "projects.sqlite"
        self.project = Project.create(
            name="Processo executável", application_id="rsc"
        )
        self.evidence = Evidence.create(
            project_id=self.project.aggregate_id,
            title="Ata de participação",
            description="Participação em banca.",
        ).add_document(Document(
            document_id="documento-ata",
            name="ata.pdf",
            relative_path="documents/ata.pdf",
            document_type="application/pdf",
        ))
        self.fact = ExecutionFact.create(
            project_id=self.project.aggregate_id,
            evidence_id=self.evidence.aggregate_id,
            fact_type="PARTICIPACAO_EVENTO",
            description="Três participações",
            quantity=Decimal("3"),
            unit="Por evento",
        )
        definition = OFFICIAL_NORMATIVE_CATALOG.find(CRITERION_ID)
        self.binding = ExecutionBinding.create(
            execution_fact_id=self.fact.aggregate_id,
            criterion_id=definition.code,
            requirement_id=definition.requirement_id,
            execution_rule_id=definition.execution_rule_id,
        )
        self.evidence_store = SQLiteEvidenceStore(self.database_path)
        self.fact_store = SQLiteExecutionFactStore(self.database_path)
        self.binding_store = SQLiteExecutionBindingStore(self.database_path)
        self.evidence_store.save(self.evidence)
        self.fact_store.save(self.fact)

    def tearDown(self) -> None:
        self.binding_store.close()
        self.fact_store.close()
        self.evidence_store.close()
        self.temporary_directory.cleanup()

    def _service(self) -> RSCExecutionService:
        return RSCExecutionService(
            self.evidence_store,
            self.fact_store,
            self.binding_store,
        )

    def test_complete_pipeline_produces_traceable_process(self):
        self.binding_store.save(self.binding)

        result = self._service().execute(self.project)

        self.assertEqual(result.execution_fact_count, 1)
        self.assertEqual(result.valid_binding_count, 1)
        self.assertEqual(result.criterion_score_count, 1)
        self.assertEqual(result.requirement_score_count, 1)
        self.assertEqual(result.incompatibility_count, 0)
        self.assertEqual(result.total_score, Decimal("9"))
        self.assertEqual(
            result.process.stage, RSCProcessStage.CONSOLIDATED
        )
        score = result.process.criterion_score(CRITERION_ID)
        self.assertEqual(score.calculated_score, Decimal("9"))
        self.assertEqual(
            score.source_contract.source_execution_fact
            .factual_traceability.evidence_id,
            self.evidence.aggregate_id,
        )
        self.assertEqual(
            score.source_contract.source_execution_fact.execution_fact_id,
            self.fact.aggregate_id,
        )
        self.assertEqual(
            result.process.result.used_evidence_ids,
            (self.evidence.aggregate_id,),
        )

    def test_missing_binding_produces_partial_evaluation(self):
        result = self._service().execute(self.project)

        self.assertEqual(result.execution_fact_count, 1)
        self.assertEqual(result.valid_binding_count, 0)
        self.assertEqual(result.criterion_score_count, 0)
        self.assertEqual(result.total_score, Decimal("0"))
        self.assertEqual(
            result.process.pending_execution_facts[0].execution_fact_id,
            self.fact.aggregate_id,
        )
        self.assertIn(
            "ExecutionFact aguardando enquadramento",
            result.process.result.pending_items[0],
        )


if __name__ == "__main__":
    unittest.main()
