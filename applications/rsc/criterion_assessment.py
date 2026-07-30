"""Consolidação rastreável do estágio de análise de um critério."""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass
from enum import Enum

from applications.rsc.constraint_evaluation import (
    AssistedFramingProposal,
    ConditionVerification,
    ConstraintAnalysisState,
    ConstraintEvaluatedCandidate,
    ConstraintEvaluatedCandidateCollection,
    FactUsed,
    NormativeCondition,
)
from applications.rsc.criterion_candidates import (
    FactualTraceability,
    NormativeOrigin,
    ReadOnlyNormativeModel,
)
from applications.rsc.evaluation_context import EvaluationContext
from applications.rsc.evidence_qualification import PresentedDocument


class CriterionAssessmentError(ValueError):
    """Falha estrutural durante a consolidação do Assessment."""


class CandidateStatus(str, Enum):
    IDENTIFIED = "identified"


class DocumentationStatus(str, Enum):
    COMPATIBLE = "compatible"
    PARTIAL = "partial"
    INSUFFICIENT = "insufficient"


class ConsolidatedConstraintStatus(str, Enum):
    COMPLETE = "complete"
    REVIEW_PENDING = "review_pending"
    INFORMATION_INCOMPLETE = "information_incomplete"
    NORMATIVE_GAP = "normative_gap"
    NOT_APPLICABLE = "not_applicable"
    NO_CONDITIONS = "no_conditions"


class CriterionAssessmentStatus(str, Enum):
    READY_FOR_SCORING = "ready_for_scoring"
    REVIEW_REQUIRED = "review_required"
    NORMATIVE_GAP = "normative_gap"
    INSUFFICIENT_INFORMATION = "insufficient_information"
    NOT_APPLICABLE = "not_applicable"


@dataclass(frozen=True, slots=True)
class AssessmentTraceability:
    normative_origin: NormativeOrigin
    factual_origin: FactualTraceability
    documents: tuple[PresentedDocument, ...]
    conditions: tuple[NormativeCondition, ...]
    verifications: tuple[ConditionVerification, ...]
    facts: tuple[FactUsed, ...]


@dataclass(frozen=True, slots=True)
class CriterionAssessment:
    criterion_id: str
    requirement_id: str
    candidate_status: CandidateStatus
    documentation_status: DocumentationStatus
    constraint_status: ConsolidatedConstraintStatus
    assessment_status: CriterionAssessmentStatus
    human_review_required: bool
    normative_gaps: tuple[str, ...]
    warnings: tuple[str, ...]
    assisted_proposals: tuple[AssistedFramingProposal, ...]
    traceability: AssessmentTraceability
    assessment_summary: str
    source_evaluation: ConstraintEvaluatedCandidate


@dataclass(frozen=True, slots=True)
class CriterionAssessmentCollection:
    assessments: tuple[CriterionAssessment, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.assessments, tuple):
            raise TypeError("assessments deve ser uma tupla.")
        if any(
            not isinstance(item, CriterionAssessment)
            for item in self.assessments
        ):
            raise TypeError("assessments contém objeto inválido.")
        identities = tuple(
            (
                item.criterion_id,
                item.source_evaluation.source_candidate.activity.activity_id,
                (
                    item.source_evaluation.source_candidate
                    .functional_exercise.id
                ),
            )
            for item in self.assessments
        )
        if len(identities) != len(set(identities)):
            raise ValueError(
                "assessments não pode conter duplicidades."
            )

    def __iter__(self) -> Iterator[CriterionAssessment]:
        return iter(self.assessments)

    def __len__(self) -> int:
        return len(self.assessments)


class CriterionAssessmentEngine:
    """Consolida resultados anteriores sem emitir decisão normativa."""

    def __init__(
        self,
        context: EvaluationContext,
        normative_model: ReadOnlyNormativeModel,
    ) -> None:
        if not isinstance(context, EvaluationContext):
            raise TypeError("context deve ser EvaluationContext.")
        self._context = context
        self._normative_model = normative_model
        self._documents = {
            item.id: item for item in context.documents
        }

    def assess(
        self,
        candidates: ConstraintEvaluatedCandidateCollection,
    ) -> CriterionAssessmentCollection:
        if not isinstance(
            candidates,
            ConstraintEvaluatedCandidateCollection,
        ):
            raise TypeError(
                "candidates deve ser "
                "ConstraintEvaluatedCandidateCollection."
            )
        return CriterionAssessmentCollection(tuple(
            self._assess_candidate(candidate)
            for candidate in candidates
        ))

    def _assess_candidate(
        self,
        evaluated: ConstraintEvaluatedCandidate,
    ) -> CriterionAssessment:
        candidate = evaluated.source_candidate
        criterion = self._normative_model.find_criterion(
            candidate.criterion_id
        )
        if criterion is None or criterion.id != candidate.criterion_id:
            raise CriterionAssessmentError(
                f"Critério desconhecido: {candidate.criterion_id}."
            )
        requirement = self._normative_model.find_requirement(
            candidate.requirement_id
        )
        if requirement is None or requirement.id != candidate.requirement_id:
            raise CriterionAssessmentError(
                f"Requisito desconhecido: {candidate.requirement_id}."
            )
        self._validate_presented_documents(evaluated)

        documentation_status = self._documentation_status(evaluated)
        constraint_status = self._constraint_status(evaluated)
        normative_gaps = self._normative_gaps(evaluated)
        warnings = self._warnings(evaluated)
        assessment_status = self._assessment_status(
            documentation_status,
            constraint_status,
        )
        human_review_required = (
            evaluated.human_review_required
            or assessment_status
            in {
                CriterionAssessmentStatus.REVIEW_REQUIRED,
                CriterionAssessmentStatus.NORMATIVE_GAP,
                CriterionAssessmentStatus.INSUFFICIENT_INFORMATION,
            }
        )
        traceability = AssessmentTraceability(
            normative_origin=candidate.normative_origin,
            factual_origin=candidate.factual_traceability,
            documents=(
                evaluated.qualified_candidate.presented_documents
            ),
            conditions=evaluated.identified_conditions,
            verifications=evaluated.verifications,
            facts=evaluated.facts_used,
        )
        return CriterionAssessment(
            criterion_id=candidate.criterion_id,
            requirement_id=candidate.requirement_id,
            candidate_status=CandidateStatus.IDENTIFIED,
            documentation_status=documentation_status,
            constraint_status=constraint_status,
            assessment_status=assessment_status,
            human_review_required=human_review_required,
            normative_gaps=normative_gaps,
            warnings=warnings,
            assisted_proposals=evaluated.framing_proposals,
            traceability=traceability,
            assessment_summary=self._summary(
                candidate.criterion_id,
                documentation_status,
                constraint_status,
                assessment_status,
                evaluated,
            ),
            source_evaluation=evaluated,
        )

    def _validate_presented_documents(
        self,
        evaluated: ConstraintEvaluatedCandidate,
    ) -> None:
        for presented in (
            evaluated.qualified_candidate.presented_documents
        ):
            document = self._documents.get(presented.document_id)
            if document is None or (
                document.document_identity.lower()
                != presented.document_identity.lower()
            ):
                raise CriterionAssessmentError(
                    "Documento apresentado não pertence ao "
                    "EvaluationContext."
                )

    @staticmethod
    def _documentation_status(
        evaluated: ConstraintEvaluatedCandidate,
    ) -> DocumentationStatus:
        qualified = evaluated.qualified_candidate
        if not qualified.accepted_documents:
            return DocumentationStatus.INSUFFICIENT
        if (
            qualified.missing_documents
            or qualified.pending_categories
        ):
            return DocumentationStatus.PARTIAL
        return DocumentationStatus.COMPATIBLE

    @staticmethod
    def _constraint_status(
        evaluated: ConstraintEvaluatedCandidate,
    ) -> ConsolidatedConstraintStatus:
        states = tuple(
            item.state for item in evaluated.verifications
        )
        if not states:
            return ConsolidatedConstraintStatus.NO_CONDITIONS
        if ConstraintAnalysisState.NORMATIVE_GAP in states:
            return ConsolidatedConstraintStatus.NORMATIVE_GAP
        if ConstraintAnalysisState.INSUFFICIENT_INFORMATION in states:
            return ConsolidatedConstraintStatus.INFORMATION_INCOMPLETE
        if all(
            state is ConstraintAnalysisState.NOT_APPLICABLE
            for state in states
        ):
            return ConsolidatedConstraintStatus.NOT_APPLICABLE
        if (
            evaluated.human_review_required
            or ConstraintAnalysisState.REVIEW_RECOMMENDED in states
            or ConstraintAnalysisState.HUMAN_DECISION_REQUIRED in states
            or ConstraintAnalysisState.NOT_VERIFIED in states
        ):
            return ConsolidatedConstraintStatus.REVIEW_PENDING
        return ConsolidatedConstraintStatus.COMPLETE

    @staticmethod
    def _assessment_status(
        documentation: DocumentationStatus,
        constraints: ConsolidatedConstraintStatus,
    ) -> CriterionAssessmentStatus:
        if constraints is ConsolidatedConstraintStatus.NORMATIVE_GAP:
            return CriterionAssessmentStatus.NORMATIVE_GAP
        if (
            documentation is not DocumentationStatus.COMPATIBLE
            or constraints
            is ConsolidatedConstraintStatus.INFORMATION_INCOMPLETE
        ):
            return CriterionAssessmentStatus.INSUFFICIENT_INFORMATION
        if constraints is ConsolidatedConstraintStatus.REVIEW_PENDING:
            return CriterionAssessmentStatus.REVIEW_REQUIRED
        if constraints is ConsolidatedConstraintStatus.NOT_APPLICABLE:
            return CriterionAssessmentStatus.NOT_APPLICABLE
        return CriterionAssessmentStatus.READY_FOR_SCORING

    @staticmethod
    def _normative_gaps(
        evaluated: ConstraintEvaluatedCandidate,
    ) -> tuple[str, ...]:
        return tuple(
            item.condition.condition_id
            for item in evaluated.verifications
            if item.state is ConstraintAnalysisState.NORMATIVE_GAP
        )

    @staticmethod
    def _warnings(
        evaluated: ConstraintEvaluatedCandidate,
    ) -> tuple[str, ...]:
        qualified = evaluated.qualified_candidate
        values = [
            *evaluated.alerts,
            *(
                f"Documento ausente: {item.document_id}."
                for item in qualified.missing_documents
            ),
            *(
                f"Categoria documental pendente: {item.category_id}."
                for item in qualified.pending_categories
            ),
        ]
        result: list[str] = []
        seen: set[str] = set()
        for value in values:
            if value not in seen:
                seen.add(value)
                result.append(value)
        return tuple(result)

    @staticmethod
    def _summary(
        criterion_id: str,
        documentation: DocumentationStatus,
        constraints: ConsolidatedConstraintStatus,
        assessment: CriterionAssessmentStatus,
        evaluated: ConstraintEvaluatedCandidate,
    ) -> str:
        return (
            f"Critério candidato {criterion_id}: documentação "
            f"{documentation.value}; condições {constraints.value}; "
            f"estágio {assessment.value}; "
            f"{len(evaluated.verifications)} verificação(ões), "
            f"{len(evaluated.facts_used)} fato(s), "
            f"{len(evaluated.pending_items)} pendência(s) e "
            f"{len(evaluated.alerts)} alerta(s). "
            "O estágio não representa aprovação nem satisfação do critério."
        )


__all__ = [
    "AssessmentTraceability",
    "CandidateStatus",
    "ConsolidatedConstraintStatus",
    "CriterionAssessment",
    "CriterionAssessmentCollection",
    "CriterionAssessmentEngine",
    "CriterionAssessmentError",
    "CriterionAssessmentStatus",
    "DocumentationStatus",
]
