"""Visualização passiva dos DTOs do Results Explorer."""

from __future__ import annotations

from PySide6.QtWidgets import (
    QDialog,
    QFormLayout,
    QLabel,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
)

from applications.rsc.results_view_model import (
    CriterionResultView,
    DocumentResultView,
    EvidenceResultView,
    ExecutionFactResultView,
    RequirementResultView,
    ResultsSummary,
)


class ResultsView(QDialog):
    """Renderiza somente projections imutáveis recebidas."""

    def __init__(self, summary: ResultsSummary, parent=None) -> None:
        if not isinstance(summary, ResultsSummary):
            raise TypeError("summary deve ser ResultsSummary.")
        super().__init__(parent)
        self._summary = summary
        self.setWindowTitle("Avaliação RSC")
        self.resize(760, 560)

        layout = QVBoxLayout(self)
        header = QFormLayout()
        self.status_value = QLabel(summary.status)
        self.total_score_value = QLabel(str(summary.total_score))
        self.pending_value = QLabel(str(summary.pending_count))
        header.addRow("Status:", self.status_value)
        header.addRow("Pontuação total:", self.total_score_value)
        header.addRow("Pendências:", self.pending_value)
        layout.addLayout(header)

        self.results_tree = QTreeWidget(self)
        self.results_tree.setHeaderLabels(("Resultado", "Estado/Pontos"))
        self.results_tree.currentItemChanged.connect(
            self._render_selection
        )
        layout.addWidget(self.results_tree)

        details = QFormLayout()
        self.criterion_value = QLabel("—")
        self.fact_value = QLabel("—")
        self.evidence_value = QLabel("—")
        self.document_value = QLabel("—")
        details.addRow("Criterion:", self.criterion_value)
        details.addRow("ExecutionFact:", self.fact_value)
        details.addRow("Evidence:", self.evidence_value)
        details.addRow("Document:", self.document_value)
        layout.addLayout(details)
        self._populate()

    @property
    def summary(self) -> ResultsSummary:
        return self._summary

    def _populate(self) -> None:
        for requirement in self._summary.requirements:
            requirement_item = self._item(
                requirement,
                requirement.requirement_id,
                str(requirement.total_score),
            )
            self.results_tree.addTopLevelItem(requirement_item)
            for criterion in requirement.criteria:
                criterion_item = self._item(
                    criterion,
                    criterion.criterion_id,
                    (
                        f"{criterion.state} · "
                        f"{criterion.score if criterion.score is not None else '—'}"
                    ),
                )
                requirement_item.addChild(criterion_item)
                fact = criterion.execution_fact
                fact_item = self._item(
                    fact, fact.description, fact.measurement
                )
                criterion_item.addChild(fact_item)
                evidence = fact.evidence
                evidence_item = self._item(
                    evidence, evidence.description, ""
                )
                fact_item.addChild(evidence_item)
                if evidence.documents:
                    for document in evidence.documents:
                        evidence_item.addChild(self._item(
                            document,
                            document.name,
                            "Disponível" if document.available else "Indisponível",
                        ))
                else:
                    evidence_item.addChild(QTreeWidgetItem(
                        ("Sem documento associado", "Indisponível")
                    ))
            requirement_item.setExpanded(True)
        if self._summary.unused_documents:
            unused_item = QTreeWidgetItem((
                "Documents sem utilização", "Pendente"
            ))
            self.results_tree.addTopLevelItem(unused_item)
            for document in self._summary.unused_documents:
                unused_item.addChild(self._item(
                    document, document.name, "Não utilizado"
                ))

    @staticmethod
    def _item(value, label: str, status: str) -> QTreeWidgetItem:
        item = QTreeWidgetItem((label, status))
        item.setData(0, 256, value)
        return item

    def _render_selection(self, current, _previous) -> None:
        if current is None:
            return
        value = current.data(0, 256)
        if isinstance(value, RequirementResultView):
            self.criterion_value.setText("—")
        elif isinstance(value, CriterionResultView):
            self._render_criterion(value)
        elif isinstance(value, ExecutionFactResultView):
            self.fact_value.setText(value.description)
            self.evidence_value.setText(value.evidence.description)
            self.document_value.setText(self._documents(value.evidence))
        elif isinstance(value, EvidenceResultView):
            self.evidence_value.setText(value.description)
            self.document_value.setText(self._documents(value))
        elif isinstance(value, DocumentResultView):
            self.document_value.setText(value.name)

    def _render_criterion(self, criterion: CriterionResultView) -> None:
        fact = criterion.execution_fact
        self.criterion_value.setText(
            f"{criterion.criterion_id} — "
            f"{criterion.score if criterion.score is not None else '—'}"
        )
        self.fact_value.setText(fact.description)
        self.evidence_value.setText(fact.evidence.description)
        self.document_value.setText(self._documents(fact.evidence))

    @staticmethod
    def _documents(evidence: EvidenceResultView) -> str:
        return (
            ", ".join(item.name for item in evidence.documents)
            if evidence.documents
            else "Sem documento associado"
        )


__all__ = ["ResultsView"]
