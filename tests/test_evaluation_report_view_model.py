from __future__ import annotations

from dataclasses import FrozenInstanceError
from decimal import Decimal
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from applications.rsc.evaluation_report_view_model import EvaluationReportViewModel
from applications.rsc.normative_catalog import OFFICIAL_NORMATIVE_CATALOG
from applications.rsc.services.rsc_execution_service import RSCExecutionService
from database import SQLiteEvidenceStore, SQLiteExecutionBindingStore, SQLiteExecutionFactStore
from platform_sdk import Document, Evidence, ExecutionBinding, ExecutionFact, Project


class EvaluationReportViewModelTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = TemporaryDirectory()
        path = Path(self.temp.name) / "report.sqlite"
        self.evidences = SQLiteEvidenceStore(path)
        self.facts = SQLiteExecutionFactStore(path)
        self.bindings = SQLiteExecutionBindingStore(path)
        self.project = Project.create(name="Relatório", application_id="rsc")

    def tearDown(self) -> None:
        self.bindings.close()
        self.facts.close()
        self.evidences.close()
        self.temp.cleanup()

    def _process(self, *, bind_second: bool = True):
        document = Document("portaria", "Portaria_231.pdf", "documents/portaria.pdf", "application/pdf")
        evidence = Evidence.create(
            project_id=self.project.aggregate_id,
            title="Portaria 231",
            description="Participação e coordenação",
        ).add_document(document)
        unused = Evidence.create(
            project_id=self.project.aggregate_id,
            title="Certificado X",
            description="Documento ainda não utilizado",
        ).add_document(Document(
            "certificado", "Certificado_X.pdf", "documents/x.pdf",
            "application/pdf",
        )).add_document(Document(
            "certificado-2", "Certificado_X_verso.pdf",
            "documents/x-verso.pdf", "application/pdf",
        ))
        without_document = Evidence.create(
            project_id=self.project.aggregate_id,
            title="Evidence incompleta",
            description="Evidence sem Document",
        )
        for item in (evidence, unused, without_document):
            self.evidences.save(item)
        facts = (
            ExecutionFact.create(
                project_id=self.project.aggregate_id, evidence_id=evidence.aggregate_id,
                fact_type="PARTICIPACAO", description="Participação em comissão",
                quantity=Decimal("3"), unit="Por evento",
            ),
            ExecutionFact.create(
                project_id=self.project.aggregate_id, evidence_id=evidence.aggregate_id,
                fact_type="COORDENACAO", description="Coordenação de projeto",
                quantity=Decimal("1"), unit="Por projeto",
            ),
        )
        for fact, criterion_id in zip(
            facts, ("DEC13048-ANX-II-ITEM-07", "DEC13048-ANX-II-ITEM-08"), strict=True
        ):
            definition = OFFICIAL_NORMATIVE_CATALOG.find(criterion_id)
            self.facts.save(fact)
            if bind_second or fact is facts[0]:
                self.bindings.save(ExecutionBinding.create(
                    execution_fact_id=fact.aggregate_id,
                    criterion_id=definition.code,
                    requirement_id=definition.requirement_id,
                    execution_rule_id=definition.execution_rule_id,
                ))
        return RSCExecutionService(self.evidences, self.facts, self.bindings).execute(self.project).process

    def test_projects_complete_report_without_mutating_domain(self):
        process = self._process()
        snapshot = process
        report = EvaluationReportViewModel(process, elapsed_seconds=0.25).report

        self.assertIs(process, snapshot)
        self.assertEqual(report.status, "CONSOLIDATED")
        self.assertEqual(report.statistics.requirements, 1)
        self.assertEqual(report.statistics.criteria, 2)
        self.assertEqual(report.statistics.execution_facts, 2)
        self.assertEqual(report.statistics.bindings, 2)
        self.assertEqual(report.statistics.elapsed_seconds, 0.25)
        self.assertEqual(len(report.requirements[0].criteria), 2)

    def test_dtos_are_immutable(self):
        report = EvaluationReportViewModel(self._process()).report
        with self.assertRaises(FrozenInstanceError):
            report.status = "ALTERADO"
        with self.assertRaises(FrozenInstanceError):
            report.statistics.documents = 0

    def test_evidence_map_covers_multiple_criteria_and_unused_document(self):
        report = EvaluationReportViewModel(self._process()).report
        used = next(item for item in report.documents if item.document_id == "portaria")
        unused = tuple(
            item for item in report.documents
            if item.document_id.startswith("certificado")
        )

        self.assertEqual(len(used.usages), 2)
        self.assertEqual({item.criterion_id for item in used.usages}, {
            "DEC13048-ANX-II-ITEM-07", "DEC13048-ANX-II-ITEM-08",
        })
        self.assertTrue(used.used)
        self.assertEqual(len(unused), 2)
        self.assertTrue(all(not item.used for item in unused))
        self.assertTrue(all(
            item.notice == "Nenhum ExecutionFact associado."
            for item in unused
        ))
        self.assertEqual(report.statistics.used_documents, 1)
        self.assertEqual(report.statistics.unused_documents, 2)

    def test_evidence_without_document_and_pending_items_are_explicit(self):
        report = EvaluationReportViewModel(self._process()).report
        self.assertEqual(len(report.evidences_without_document), 1)
        self.assertTrue(any(
            item.category == "Evidence sem Document"
            for item in report.pending_items
        ))
        self.assertIn("pendências críticas", report.operational_indicator)

    def test_partial_evaluation_reports_fact_awaiting_binding(self):
        report = EvaluationReportViewModel(
            self._process(bind_second=False)
        ).report

        pending = next(
            item for item in report.pending_items
            if item.category == "ExecutionFact sem Binding"
        )
        self.assertEqual(
            pending.description,
            "ExecutionFact aguardando enquadramento.",
        )
        self.assertFalse(pending.critical)
        self.assertEqual(report.statistics.execution_facts, 2)
        self.assertEqual(report.statistics.bindings, 1)
        self.assertEqual(report.statistics.pending_execution_facts, 1)


if __name__ == "__main__":
    unittest.main()
