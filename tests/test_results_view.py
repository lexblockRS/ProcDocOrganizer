from __future__ import annotations

import os
from decimal import Decimal
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from applications.rsc.results_view_model import (
    CriterionResultView,
    EvidenceResultView,
    ExecutionFactResultView,
    RequirementResultView,
    ResultsSummary,
)
from ui.results_view import ResultsView


class ResultsViewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self) -> None:
        evidence = EvidenceResultView(
            evidence_id="evidence-1",
            description="Evidence sem arquivo",
            documents=(),
        )
        fact = ExecutionFactResultView(
            execution_fact_id="fact-1",
            description="Participação em comissão",
            measurement="3 Por evento",
            evidence=evidence,
        )
        criterion = CriterionResultView(
            criterion_id="criterion-1",
            state="EXECUTED",
            score=Decimal("9"),
            explanation="3 × 3",
            execution_fact=fact,
        )
        self.summary = ResultsSummary(
            process_id="process-1",
            status="CONSOLIDATED",
            total_score=Decimal("9"),
            requirements=(RequirementResultView(
                requirement_id="requirement-1",
                total_score=Decimal("9"),
                criteria=(criterion,),
            ),),
            criterion_count=1,
            pending_count=0,
        )
        self.view = ResultsView(self.summary)

    def tearDown(self) -> None:
        self.view.close()
        self.view.deleteLater()
        self.app.processEvents()

    def test_renders_requirement_criterion_fact_evidence_and_missing_document(self):
        requirement_item = self.view.results_tree.topLevelItem(0)
        criterion_item = requirement_item.child(0)
        fact_item = criterion_item.child(0)
        evidence_item = fact_item.child(0)
        document_item = evidence_item.child(0)

        self.assertEqual(self.view.status_value.text(), "CONSOLIDATED")
        self.assertEqual(self.view.total_score_value.text(), "9")
        self.assertEqual(requirement_item.text(0), "requirement-1")
        self.assertEqual(criterion_item.text(0), "criterion-1")
        self.assertEqual(fact_item.text(0), "Participação em comissão")
        self.assertEqual(evidence_item.text(0), "Evidence sem arquivo")
        self.assertEqual(document_item.text(0), "Sem documento associado")

    def test_selecting_criterion_renders_complete_detail(self):
        criterion_item = self.view.results_tree.topLevelItem(0).child(0)

        self.view.results_tree.setCurrentItem(criterion_item)

        self.assertIn("criterion-1", self.view.criterion_value.text())
        self.assertEqual(
            self.view.fact_value.text(), "Participação em comissão"
        )
        self.assertEqual(
            self.view.evidence_value.text(), "Evidence sem arquivo"
        )
        self.assertEqual(
            self.view.document_value.text(), "Sem documento associado"
        )


if __name__ == "__main__":
    unittest.main()
