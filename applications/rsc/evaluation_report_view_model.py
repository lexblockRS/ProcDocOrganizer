"""Projeção imutável do relatório operacional de avaliação RSC."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from applications.rsc.execution_compatibility import CompatibilityState
from applications.rsc.execution_validation import ValidationState
from applications.rsc.rsc_process import RSCProcess
from applications.rsc.scoring_kernel import ScoringState


@dataclass(frozen=True, slots=True)
class CriterionReportView:
    criterion_id: str
    score: Decimal | None
    state: str
    attended: bool
    explanation: str


@dataclass(frozen=True, slots=True)
class RequirementReportView:
    requirement_id: str
    total_score: Decimal
    criteria: tuple[CriterionReportView, ...]


@dataclass(frozen=True, slots=True)
class PendingItemView:
    category: str
    description: str
    reference_id: str | None = None
    critical: bool = False


@dataclass(frozen=True, slots=True)
class DocumentUsageView:
    execution_fact_id: str
    execution_fact_description: str
    binding_id: str | None
    criterion_id: str | None
    requirement_id: str | None
    score: Decimal | None
    state: str


@dataclass(frozen=True, slots=True)
class EvidenceCoverageView:
    evidence_id: str
    description: str
    execution_fact_ids: tuple[str, ...]
    has_document: bool


@dataclass(frozen=True, slots=True)
class DocumentCoverageView:
    document_id: str
    name: str
    evidence: EvidenceCoverageView
    usages: tuple[DocumentUsageView, ...]
    sustained_score: Decimal
    used: bool
    notice: str | None = None


@dataclass(frozen=True, slots=True)
class StatisticsView:
    documents: int
    used_documents: int
    unused_documents: int
    evidences: int
    execution_facts: int
    proven_execution_facts: int
    pending_execution_facts: int
    bindings: int
    requirements: int
    criteria: int
    elapsed_seconds: float | None


@dataclass(frozen=True, slots=True)
class EvaluationSummary:
    process_id: str
    status: str
    total_score: Decimal
    operational_indicator: str
    requirements: tuple[RequirementReportView, ...]
    pending_items: tuple[PendingItemView, ...]
    documents: tuple[DocumentCoverageView, ...]
    evidences_without_document: tuple[EvidenceCoverageView, ...]
    statistics: StatisticsView


class EvaluationReportViewModel:
    """Transforma um snapshot de ``RSCProcess`` em DTOs de apresentação."""

    def __init__(
        self,
        process: RSCProcess,
        *,
        elapsed_seconds: float | None = None,
    ) -> None:
        if not isinstance(process, RSCProcess):
            raise TypeError("process deve ser RSCProcess.")
        if elapsed_seconds is not None and (
            isinstance(elapsed_seconds, bool)
            or not isinstance(elapsed_seconds, (int, float))
            or elapsed_seconds < 0
        ):
            raise TypeError("elapsed_seconds deve ser não negativo ou None.")
        self._report = self._project(
            process,
            None if elapsed_seconds is None else float(elapsed_seconds),
        )

    @property
    def report(self) -> EvaluationSummary:
        return self._report

    @staticmethod
    def _project(
        process: RSCProcess, elapsed_seconds: float | None
    ) -> EvaluationSummary:
        requirements = tuple(
            RequirementReportView(
                requirement_id=item.requirement_id,
                total_score=item.total_score,
                criteria=tuple(
                    CriterionReportView(
                        criterion_id=score.criterion_id,
                        score=score.calculated_score,
                        state=score.scoring_state.value,
                        attended=(
                            score.scoring_state is ScoringState.EXECUTED
                        ),
                        explanation=score.explanation,
                    )
                    for score in item.criterion_scores
                ),
            )
            for item in process.requirement_scores
        )
        score_by_fact = {
            score.source_contract.source_execution_fact.execution_fact_id: score
            for score in process.criterion_scores
        }
        evidence_index = {
            item.evidence_id: item for item in process.evidences
        }
        facts_by_evidence: dict[str, list] = {}
        for fact in process.execution_facts:
            facts_by_evidence.setdefault(
                fact.factual_traceability.evidence_id, []
            ).append(fact)
        pending_by_evidence: dict[str, list] = {}
        for fact in process.pending_execution_facts:
            pending_by_evidence.setdefault(fact.evidence_id, []).append(fact)

        pending = EvaluationReportViewModel._pending_items(
            process, score_by_fact
        )
        documents, missing_document_evidences = (
            EvaluationReportViewModel._coverage(
                evidence_index,
                facts_by_evidence,
                score_by_fact,
                pending_by_evidence,
            )
        )
        criterion_count = sum(
            len(item.criteria) for item in requirements
        )
        fact_count = (
            len(process.execution_facts)
            + len(process.pending_execution_facts)
        )
        proven_fact_ids = {
            usage.execution_fact_id
            for document in documents
            for usage in document.usages
            if usage.binding_id is not None
        }
        binding_ids = {
            score.source_contract.source_execution_fact
            .factual_traceability.functional_assignment_evidence_id
            for score in process.criterion_scores
        }
        statistics = StatisticsView(
            documents=len(documents),
            used_documents=sum(item.used for item in documents),
            unused_documents=sum(not item.used for item in documents),
            evidences=len(process.evidences),
            execution_facts=fact_count,
            proven_execution_facts=len(proven_fact_ids),
            pending_execution_facts=fact_count - len(proven_fact_ids),
            bindings=len(binding_ids),
            requirements=len(requirements),
            criteria=criterion_count,
            elapsed_seconds=elapsed_seconds,
        )
        return EvaluationSummary(
            process_id=process.aggregate_id,
            status=process.stage.value,
            total_score=process.total_score or Decimal(0),
            operational_indicator=(
                "🔴 Processo com pendências críticas"
                if any(item.critical for item in pending)
                else "🟡 Processo parcialmente completo"
                if pending or statistics.unused_documents
                else "🟢 Processo consistente"
            ),
            requirements=requirements,
            pending_items=pending,
            documents=documents,
            evidences_without_document=missing_document_evidences,
            statistics=statistics,
        )

    @staticmethod
    def _pending_items(process, score_by_fact) -> tuple[PendingItemView, ...]:
        items: list[PendingItemView] = []
        for fact in process.pending_execution_facts:
            items.append(PendingItemView(
                "ExecutionFact sem Binding",
                fact.reason,
                fact.execution_fact_id,
                False,
            ))
        for fact in process.execution_facts:
            if fact.execution_fact_id not in score_by_fact:
                items.append(PendingItemView(
                    "ExecutionFact sem Binding",
                    "ExecutionFact não participa de nenhum CriterionScore.",
                    fact.execution_fact_id,
                    True,
                ))
        for evidence in process.evidences:
            if not evidence.documents:
                items.append(PendingItemView(
                    "Evidence sem Document",
                    "Evidence não possui Document associado.",
                    evidence.evidence_id,
                    True,
                ))
        for compatibility in process.compatibilities:
            if compatibility.compatibility_state is CompatibilityState.INCOMPATIBLE:
                description = "; ".join(compatibility.issues) or compatibility.explanation
                items.append(PendingItemView(
                    "Incompatibilidade", description,
                    compatibility.execution_fact_id, True,
                ))
        for validation in process.validations:
            if validation.validation_state is not ValidationState.READY:
                details = (
                    validation.blocking_issues
                    + validation.warnings
                    + tuple(item.reason for item in validation.missing_facts)
                    + tuple(item.reason for item in validation.missing_documents)
                    + tuple(item.reason for item in validation.missing_measurements)
                )
                items.append(PendingItemView(
                    "Falha de Validation",
                    "; ".join(dict.fromkeys(details)) or validation.explanation,
                    validation.execution_fact_id,
                    validation.validation_state is ValidationState.BLOCKED,
                ))
        for score in process.criterion_scores:
            if score.scoring_state is not ScoringState.EXECUTED:
                items.append(PendingItemView(
                    "Critério não atendido", score.explanation,
                    score.criterion_id,
                    score.scoring_state is ScoringState.BLOCKED,
                ))
        if process.result is not None:
            known = {item.description for item in items}
            items.extend(
                PendingItemView("Outra pendência", description)
                for description in process.result.pending_items
                if description not in known
                and not description.startswith(
                    "ExecutionFact aguardando enquadramento:"
                )
            )
        return tuple(items)

    @staticmethod
    def _coverage(
        evidence_index,
        facts_by_evidence,
        score_by_fact,
        pending_by_evidence,
    ):
        document_records: dict[str, dict] = {}
        missing: list[EvidenceCoverageView] = []
        for evidence_id, evidence in evidence_index.items():
            facts = facts_by_evidence.get(evidence_id, [])
            pending_facts = pending_by_evidence.get(evidence_id, [])
            coverage = EvidenceCoverageView(
                evidence_id=evidence_id,
                description=evidence.description,
                execution_fact_ids=tuple(
                    fact.execution_fact_id
                    for fact in (*facts, *pending_facts)
                ),
                has_document=bool(evidence.documents),
            )
            if not coverage.has_document:
                missing.append(coverage)
                continue
            for document in evidence.documents:
                document_records[document.document_id] = {
                    "name": document.name,
                    "evidence": coverage,
                    "facts": [],
                    "pending_facts": list(pending_facts),
                }
            for fact in facts:
                for document in fact.canonical_documents:
                    record = document_records.setdefault(document.document_id, {
                        "name": document.name,
                        "evidence": coverage,
                        "facts": [],
                        "pending_facts": [],
                    })
                    record["name"] = document.name
                    record["facts"].append(fact)
        documents = []
        for document_id, record in document_records.items():
            usages = []
            for fact in dict.fromkeys(record["facts"]):
                score = score_by_fact.get(fact.execution_fact_id)
                trace = fact.factual_traceability
                usages.append(DocumentUsageView(
                    execution_fact_id=fact.execution_fact_id,
                    execution_fact_description=(
                        fact.canonical_activities[0].description
                        if fact.canonical_activities else fact.explanation
                    ),
                    binding_id=trace.functional_assignment_evidence_id,
                    criterion_id=fact.criterion_id,
                    requirement_id=fact.requirement_id,
                    score=None if score is None else score.calculated_score,
                    state="SEM BINDING" if score is None else score.scoring_state.value,
                ))
            for fact in record["pending_facts"]:
                usages.append(DocumentUsageView(
                    execution_fact_id=fact.execution_fact_id,
                    execution_fact_description=fact.description,
                    binding_id=None,
                    criterion_id=None,
                    requirement_id=None,
                    score=None,
                    state="AGUARDANDO ENQUADRAMENTO",
                ))
            usages_tuple = tuple(usages)
            sustained = sum(
                (item.score for item in usages_tuple if item.score is not None),
                Decimal(0),
            )
            documents.append(DocumentCoverageView(
                document_id=document_id,
                name=record["name"],
                evidence=record["evidence"],
                usages=usages_tuple,
                sustained_score=sustained,
                used=any(item.binding_id is not None for item in usages_tuple),
                notice=(
                    None
                    if any(item.binding_id is not None for item in usages_tuple)
                    else "ExecutionFact existente sem ExecutionBinding."
                    if usages_tuple
                    else "Nenhum ExecutionFact associado."
                ),
            ))
        return tuple(documents), tuple(missing)


__all__ = [
    "CriterionReportView", "DocumentCoverageView", "DocumentUsageView",
    "EvaluationReportViewModel", "EvaluationSummary", "EvidenceCoverageView",
    "PendingItemView", "RequirementReportView", "StatisticsView",
]
