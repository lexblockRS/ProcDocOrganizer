from __future__ import annotations

import os
from decimal import Decimal
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from applications.rsc.evaluation_report_view_model import (
    CriterionReportView, DocumentCoverageView, DocumentUsageView,
    EvaluationSummary, EvidenceCoverageView, PendingItemView,
    RequirementReportView, StatisticsView,
)
from ui.evaluation_report_view import EvaluationReportView


class EvaluationReportViewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self) -> None:
        evidence = EvidenceCoverageView("e-1", "Portaria", ("f-1",), True)
        usage = DocumentUsageView("f-1", "Comissão", "b-1", "c-1", "r-1", Decimal("9"), "EXECUTED")
        stats = StatisticsView(1, 1, 0, 1, 1, 1, 0, 1, 1, 1, 0.125)
        report = EvaluationSummary(
            "p-1", "CONSOLIDATED", Decimal("9"), "🟡 Processo parcialmente completo",
            (RequirementReportView("r-1", Decimal("9"), (
                CriterionReportView("c-1", Decimal("9"), "EXECUTED", True, "ok"),
            )),),
            (PendingItemView("Outra pendência", "Revisar", "c-1"),),
            (DocumentCoverageView("d-1", "Portaria.pdf", evidence, (usage,), Decimal("9"), True),),
            (), stats,
        )
        self.view = EvaluationReportView(report)

    def tearDown(self) -> None:
        self.view.close()
        self.view.deleteLater()
        self.app.processEvents()

    def test_renders_all_required_sections(self):
        self.assertEqual(self.view.tabs.count(), 5)
        self.assertEqual(
            [self.view.tabs.tabText(index) for index in range(5)],
            ["Resumo Executivo", "Resultado da Avaliação", "Pendências (1)", "Mapa de Evidências", "Estatísticas"],
        )
        self.assertEqual(self.view.status_value.text(), "CONSOLIDATED")
        self.assertEqual(self.view.total_score_value.text(), "9")

    def test_renders_result_pending_and_evidence_trace(self):
        criterion = self.view.results_tree.topLevelItem(0).child(0)
        document = self.view.evidence_tree.topLevelItem(0)
        fact = document.child(0).child(0)
        self.assertEqual(criterion.text(1), "✔ Atendido")
        self.assertIn("Revisar", self.view.pending_list.item(0).text())
        self.assertIn("Portaria.pdf", document.text(0))
        self.assertIn("Comissão", fact.text(0))


if __name__ == "__main__":
    unittest.main()
