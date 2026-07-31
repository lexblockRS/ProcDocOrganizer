"""View passiva do relatório operacional de avaliação RSC."""

from __future__ import annotations

from PySide6.QtWidgets import (
    QDialog, QFormLayout, QLabel, QListWidget, QTabWidget,
    QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget,
)

from applications.rsc.evaluation_report_view_model import EvaluationSummary


class EvaluationReportView(QDialog):
    """Renderiza exclusivamente DTOs da camada de apresentação."""

    def __init__(self, report: EvaluationSummary, parent=None) -> None:
        if not isinstance(report, EvaluationSummary):
            raise TypeError("report deve ser EvaluationSummary.")
        super().__init__(parent)
        self._report = report
        self.setWindowTitle("Evaluation Report")
        self.resize(900, 650)
        layout = QVBoxLayout(self)
        self.tabs = QTabWidget(self)
        layout.addWidget(self.tabs)
        self._add_summary()
        self._add_results()
        self._add_pending()
        self._add_evidence_map()
        self._add_statistics()

    @property
    def report(self) -> EvaluationSummary:
        return self._report

    @staticmethod
    def _page():
        page = QWidget()
        return page, QVBoxLayout(page)

    def _add_summary(self) -> None:
        page, layout = self._page()
        form = QFormLayout()
        self.status_value = QLabel(self._report.status)
        self.total_score_value = QLabel(str(self._report.total_score))
        self.indicator_value = QLabel(self._report.operational_indicator)
        stats = self._report.statistics
        for label, widget in (
            ("Status do processo:", self.status_value),
            ("Pontuação total:", self.total_score_value),
            ("Indicador operacional:", self.indicator_value),
            ("Requirements:", QLabel(str(stats.requirements))),
            ("Criteria:", QLabel(str(stats.criteria))),
            ("ExecutionFacts:", QLabel(str(stats.execution_facts))),
            ("Bindings:", QLabel(str(stats.bindings))),
            ("Documents:", QLabel(str(stats.documents))),
            ("Evidence:", QLabel(str(stats.evidences))),
            ("Tempo de execução:", QLabel(self._elapsed())),
        ):
            form.addRow(label, widget)
        layout.addLayout(form)
        layout.addStretch()
        self.tabs.addTab(page, "Resumo Executivo")

    def _add_results(self) -> None:
        page, layout = self._page()
        self.results_tree = QTreeWidget(page)
        self.results_tree.setHeaderLabels(("Requirement / Criterion", "Estado", "Pontos"))
        for requirement in self._report.requirements:
            root = QTreeWidgetItem((requirement.requirement_id, "", str(requirement.total_score)))
            self.results_tree.addTopLevelItem(root)
            for criterion in requirement.criteria:
                root.addChild(QTreeWidgetItem((
                    criterion.criterion_id,
                    "✔ Atendido" if criterion.attended else "○ Não atendido",
                    "—" if criterion.score is None else str(criterion.score),
                )))
            root.setExpanded(True)
        layout.addWidget(self.results_tree)
        self.tabs.addTab(page, "Resultado da Avaliação")

    def _add_pending(self) -> None:
        page, layout = self._page()
        self.pending_list = QListWidget(page)
        if self._report.pending_items:
            for item in self._report.pending_items:
                reference = f" [{item.reference_id}]" if item.reference_id else ""
                self.pending_list.addItem(f"{item.category}{reference}: {item.description}")
        else:
            self.pending_list.addItem("Nenhuma pendência identificada.")
        layout.addWidget(self.pending_list)
        self.tabs.addTab(page, f"Pendências ({len(self._report.pending_items)})")

    def _add_evidence_map(self) -> None:
        page, layout = self._page()
        self.evidence_tree = QTreeWidget(page)
        self.evidence_tree.setHeaderLabels(("Mapa de evidências", "Estado / Pontos"))
        for document in self._report.documents:
            root = QTreeWidgetItem((f"Documento: {document.name}", f"{document.sustained_score} pontos"))
            self.evidence_tree.addTopLevelItem(root)
            evidence = QTreeWidgetItem((f"Evidence: {document.evidence.description}", ""))
            root.addChild(evidence)
            if document.usages:
                for usage in document.usages:
                    fact = QTreeWidgetItem((f"ExecutionFact: {usage.execution_fact_description}", usage.state))
                    evidence.addChild(fact)
                    fact.addChild(QTreeWidgetItem((f"ExecutionBinding: {usage.binding_id or 'Sem Binding'}", "")))
                    fact.addChild(QTreeWidgetItem((f"Criterion: {usage.criterion_id or '—'}", "—" if usage.score is None else str(usage.score))))
                    fact.addChild(QTreeWidgetItem((f"Requirement: {usage.requirement_id or '—'}", "")))
            else:
                evidence.addChild(QTreeWidgetItem((document.notice or "Sem utilização", "Pendente")))
            root.setExpanded(True)
            evidence.setExpanded(True)
        for evidence in self._report.evidences_without_document:
            self.evidence_tree.addTopLevelItem(QTreeWidgetItem((
                f"Evidence: {evidence.description}", "Sem Document",
            )))
        layout.addWidget(self.evidence_tree)
        self.tabs.addTab(page, "Mapa de Evidências")

    def _add_statistics(self) -> None:
        page, layout = self._page()
        form = QFormLayout()
        stats = self._report.statistics
        for label, value in (
            ("Documents:", stats.documents),
            ("Documents utilizados:", stats.used_documents),
            ("Documents não utilizados:", stats.unused_documents),
            ("Evidence:", stats.evidences),
            ("ExecutionFacts:", stats.execution_facts),
            ("ExecutionFacts comprovados:", stats.proven_execution_facts),
            ("ExecutionFacts pendentes:", stats.pending_execution_facts),
            ("Bindings:", stats.bindings),
            ("Requirements:", stats.requirements),
            ("Criteria:", stats.criteria),
            ("Tempo de execução:", self._elapsed()),
        ):
            form.addRow(label, QLabel(str(value)))
        layout.addLayout(form)
        layout.addStretch()
        self.tabs.addTab(page, "Estatísticas")

    def _elapsed(self) -> str:
        value = self._report.statistics.elapsed_seconds
        return "Não disponível" if value is None else f"{value:.3f} s"


__all__ = ["EvaluationReportView"]
