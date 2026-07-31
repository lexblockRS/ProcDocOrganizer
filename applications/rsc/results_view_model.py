"""Projeções imutáveis do resultado RSC para a apresentação."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from applications.rsc.rsc_process import RSCProcess


@dataclass(frozen=True, slots=True)
class DocumentResultView:
    document_id: str
    name: str
    available: bool


@dataclass(frozen=True, slots=True)
class EvidenceResultView:
    evidence_id: str
    description: str
    documents: tuple[DocumentResultView, ...]


@dataclass(frozen=True, slots=True)
class ExecutionFactResultView:
    execution_fact_id: str
    description: str
    measurement: str
    evidence: EvidenceResultView


@dataclass(frozen=True, slots=True)
class CriterionResultView:
    criterion_id: str
    state: str
    score: Decimal | None
    explanation: str
    execution_fact: ExecutionFactResultView


@dataclass(frozen=True, slots=True)
class RequirementResultView:
    requirement_id: str
    total_score: Decimal
    criteria: tuple[CriterionResultView, ...]


@dataclass(frozen=True, slots=True)
class ResultsSummary:
    process_id: str
    status: str
    total_score: Decimal
    requirements: tuple[RequirementResultView, ...]
    criterion_count: int
    pending_count: int
    unused_documents: tuple[DocumentResultView, ...] = ()


class ResultsViewModel:
    """Converte um snapshot do domínio em DTOs passivos de apresentação."""

    def __init__(self, process: RSCProcess) -> None:
        if not isinstance(process, RSCProcess):
            raise TypeError("process deve ser RSCProcess.")
        self._summary = self._project(process)

    @property
    def summary(self) -> ResultsSummary:
        return self._summary

    @staticmethod
    def _project(process: RSCProcess) -> ResultsSummary:
        evidence_index = {
            item.evidence_id: item for item in process.evidences
        }
        requirements = tuple(
            RequirementResultView(
                requirement_id=requirement.requirement_id,
                total_score=requirement.total_score,
                criteria=tuple(
                    ResultsViewModel._criterion(
                        score, evidence_index
                    )
                    for score in requirement.criterion_scores
                ),
            )
            for requirement in process.requirement_scores
        )
        return ResultsSummary(
            process_id=process.aggregate_id,
            status=process.stage.value,
            total_score=process.total_score or Decimal(0),
            requirements=requirements,
            criterion_count=sum(
                len(item.criteria) for item in requirements
            ),
            pending_count=(
                0
                if process.result is None
                else len(process.result.pending_items)
            ),
            unused_documents=tuple(
                DocumentResultView(
                    document_id=document.document_id,
                    name=document.name,
                    available=True,
                )
                for evidence in process.evidences
                if evidence.evidence_id not in (
                    ()
                    if process.result is None
                    else process.result.used_evidence_ids
                )
                for document in evidence.documents
            ),
        )

    @staticmethod
    def _criterion(score, evidence_index) -> CriterionResultView:
        fact = score.source_contract.source_execution_fact
        evidence_id = fact.factual_traceability.evidence_id
        process_evidence = evidence_index.get(evidence_id)
        documents = tuple(
            DocumentResultView(
                document_id=item.document_id,
                name=item.name,
                available=True,
            )
            for item in fact.canonical_documents
        )
        evidence = EvidenceResultView(
            evidence_id=evidence_id,
            description=(
                process_evidence.description
                if process_evidence is not None
                else "Evidence não localizada no processo"
            ),
            documents=documents,
        )
        description = (
            fact.canonical_activities[0].description
            if fact.canonical_activities
            else fact.explanation
        )
        measurement = (
            f"{fact.measurement.amount if fact.measurement.amount is not None else '—'} "
            f"{fact.measurement.unit}"
        )
        return CriterionResultView(
            criterion_id=score.criterion_id,
            state=score.scoring_state.value,
            score=score.calculated_score,
            explanation=score.explanation,
            execution_fact=ExecutionFactResultView(
                execution_fact_id=fact.execution_fact_id,
                description=description,
                measurement=measurement,
                evidence=evidence,
            ),
        )


__all__ = [
    "CriterionResultView",
    "DocumentResultView",
    "EvidenceResultView",
    "ExecutionFactResultView",
    "RequirementResultView",
    "ResultsSummary",
    "ResultsViewModel",
]
