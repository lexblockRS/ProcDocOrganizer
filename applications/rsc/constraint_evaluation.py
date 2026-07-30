"""Verificação explicável de condições normativas estruturadas."""

from __future__ import annotations

from collections.abc import Iterator, Mapping, Sequence
from dataclasses import dataclass
from enum import Enum
from typing import Any, Protocol

from applications.rsc.criterion_candidates import NormativeOrigin
from applications.rsc.evaluation_context import EvaluationContext
from applications.rsc.evidence_qualification import (
    QualifiedCriterionCandidate,
    QualifiedCriterionCandidateCollection,
)


class ConstraintEvaluationError(ValueError):
    """Falha estrutural na entrada da verificação de condições."""


class ConditionClassification(str, Enum):
    STRUCTURED = "structured"
    ASSISTED = "assisted"
    HUMAN_ONLY = "human_only"


class ConstraintAnalysisState(str, Enum):
    VERIFIED = "verified"
    NOT_VERIFIED = "not_verified"
    NOT_APPLICABLE = "not_applicable"
    REVIEW_RECOMMENDED = "review_recommended"
    HUMAN_DECISION_REQUIRED = "human_decision_required"
    INSUFFICIENT_INFORMATION = "insufficient_information"
    NORMATIVE_GAP = "normative_gap"


class NormativeConditionRecord(Protocol):
    id: str
    criterion_id: str
    classification: str
    description: str
    operation: str | None
    fact_key: str | None
    expected_value: object
    document_id: str
    legal_reference: str
    hierarchy: Sequence[str]
    validation_questions: Sequence[str]


class ConstraintNormativeModel(Protocol):
    """Consulta somente leitura das condições já estruturadas na norma."""

    def conditions_of_criterion(
        self,
        criterion_id: str,
    ) -> Sequence[NormativeConditionRecord] | None: ...


@dataclass(frozen=True, slots=True)
class NormativeCondition:
    condition_id: str
    criterion_id: str
    classification: ConditionClassification | None
    description: str
    operation: str | None
    fact_key: str | None
    expected_value: object
    origin: NormativeOrigin


@dataclass(frozen=True, slots=True)
class FactUsed:
    key: str
    value: object
    source: str


@dataclass(frozen=True, slots=True)
class AssistedFramingProposal:
    preliminary_conclusion: str
    favorable_facts: tuple[str, ...]
    contrary_facts: tuple[str, ...]
    missing_information: tuple[str, ...]
    normative_reference: str
    validation_questions: tuple[str, ...]
    review_justification: str
    definitive: bool = False

    def __post_init__(self) -> None:
        if self.definitive:
            raise ValueError(
                "proposta de enquadramento não pode ser definitiva."
            )


@dataclass(frozen=True, slots=True)
class ConditionVerification:
    condition: NormativeCondition
    state: ConstraintAnalysisState
    facts_used: tuple[FactUsed, ...]
    operation_performed: str
    explanation: str
    pending_information: tuple[str, ...]
    alerts: tuple[str, ...]
    human_review_required: bool
    proposal: AssistedFramingProposal | None = None


@dataclass(frozen=True, slots=True)
class ConstraintEvaluatedCandidate:
    qualified_candidate: QualifiedCriterionCandidate
    identified_conditions: tuple[NormativeCondition, ...]
    verifications: tuple[ConditionVerification, ...]
    facts_used: tuple[FactUsed, ...]
    normative_devices: tuple[NormativeOrigin, ...]
    pending_items: tuple[str, ...]
    alerts: tuple[str, ...]
    human_review_required: bool
    framing_proposals: tuple[AssistedFramingProposal, ...]

    @property
    def source_candidate(self):
        return self.qualified_candidate.source_candidate


@dataclass(frozen=True, slots=True)
class ConstraintEvaluatedCandidateCollection:
    candidates: tuple[ConstraintEvaluatedCandidate, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.candidates, tuple):
            raise TypeError("candidates deve ser uma tupla.")
        if any(
            not isinstance(item, ConstraintEvaluatedCandidate)
            for item in self.candidates
        ):
            raise TypeError("candidates contém resultado inválido.")
        identities = tuple(
            (
                item.source_candidate.criterion_id,
                item.source_candidate.activity.activity_id,
                item.source_candidate.functional_exercise.id,
            )
            for item in self.candidates
        )
        if len(identities) != len(set(identities)):
            raise ValueError(
                "resultados avaliados não podem conter duplicidades."
            )

    def __iter__(self) -> Iterator[ConstraintEvaluatedCandidate]:
        return iter(self.candidates)

    def __len__(self) -> int:
        return len(self.candidates)


class ConstraintEvaluationEngine:
    """Verifica condições sem produzir decisão final sobre critérios."""

    FACTS_METADATA_KEY = "constraint_facts"
    STRUCTURED_OPERATIONS = {
        "equals",
        "not_equals",
        "contains",
        "is_true",
        "is_false",
    }

    def __init__(
        self,
        context: EvaluationContext,
        normative_model: ConstraintNormativeModel,
    ) -> None:
        if not isinstance(context, EvaluationContext):
            raise TypeError("context deve ser EvaluationContext.")
        self._context = context
        self._normative_model = normative_model

    def evaluate(
        self,
        candidates: QualifiedCriterionCandidateCollection,
    ) -> ConstraintEvaluatedCandidateCollection:
        if not isinstance(
            candidates,
            QualifiedCriterionCandidateCollection,
        ):
            raise TypeError(
                "candidates deve ser "
                "QualifiedCriterionCandidateCollection."
            )
        return ConstraintEvaluatedCandidateCollection(tuple(
            self._evaluate_candidate(candidate)
            for candidate in candidates
        ))

    def _evaluate_candidate(
        self,
        candidate: QualifiedCriterionCandidate,
    ) -> ConstraintEvaluatedCandidate:
        criterion_id = candidate.source_candidate.criterion_id
        records = self._normative_model.conditions_of_criterion(
            criterion_id
        )
        if records is None:
            verifications = (self._normative_gap(criterion_id),)
            conditions = tuple(
                item.condition for item in verifications
            )
        else:
            conditions = tuple(
                self._condition(record, criterion_id)
                for record in records
            )
            self._require_unique_conditions(conditions)
            verifications = tuple(
                self._verify(
                    condition,
                    record,
                    candidate,
                )
                for condition, record in zip(
                    conditions,
                    records,
                    strict=True,
                )
            )

        facts = self._unique_facts(verifications)
        devices = self._unique_devices(conditions)
        pending = self._unique_text(
            item
            for verification in verifications
            for item in verification.pending_information
        )
        alerts = self._unique_text(
            item
            for verification in verifications
            for item in verification.alerts
        )
        proposals = tuple(
            verification.proposal
            for verification in verifications
            if verification.proposal is not None
        )
        return ConstraintEvaluatedCandidate(
            qualified_candidate=candidate,
            identified_conditions=conditions,
            verifications=verifications,
            facts_used=facts,
            normative_devices=devices,
            pending_items=pending,
            alerts=alerts,
            human_review_required=any(
                item.human_review_required
                for item in verifications
            ),
            framing_proposals=proposals,
        )

    def _verify(
        self,
        condition: NormativeCondition,
        record: NormativeConditionRecord,
        candidate: QualifiedCriterionCandidate,
    ) -> ConditionVerification:
        if condition.classification is None:
            return self._gap_for_condition(
                condition,
                "Classificação normativa desconhecida.",
            )
        fact = self._fact(condition.condition_id, candidate)
        if fact is not None and fact.get("applicable") is False:
            return ConditionVerification(
                condition=condition,
                state=ConstraintAnalysisState.NOT_APPLICABLE,
                facts_used=(),
                operation_performed="applicability_explicitly_false",
                explanation=(
                    "O metadata factual marcou expressamente a condição "
                    "como não aplicável."
                ),
                pending_information=(),
                alerts=(),
                human_review_required=False,
            )
        if condition.classification is ConditionClassification.STRUCTURED:
            return self._verify_structured(condition, fact)
        if condition.classification is ConditionClassification.ASSISTED:
            return self._verify_assisted(condition, record, fact)
        return ConditionVerification(
            condition=condition,
            state=ConstraintAnalysisState.HUMAN_DECISION_REQUIRED,
            facts_used=self._facts_from_record(fact),
            operation_performed="human_only_reservation",
            explanation=(
                "A condição está classificada como exclusivamente humana; "
                "nenhuma conclusão automatizada foi produzida."
            ),
            pending_information=self._missing_from_record(fact),
            alerts=("Decisão humana obrigatória.",),
            human_review_required=True,
        )

    def _verify_structured(
        self,
        condition: NormativeCondition,
        fact: Mapping[str, object] | None,
    ) -> ConditionVerification:
        operation = condition.operation
        if operation not in self.STRUCTURED_OPERATIONS:
            return self._gap_for_condition(
                condition,
                f"Operação estruturada desconhecida: {operation}.",
            )
        if fact is None or "value" not in fact or fact["value"] is None:
            return ConditionVerification(
                condition=condition,
                state=ConstraintAnalysisState.INSUFFICIENT_INFORMATION,
                facts_used=(),
                operation_performed=operation,
                explanation=(
                    "Não existe valor factual explícito para executar "
                    "a verificação estruturada."
                ),
                pending_information=(
                    condition.fact_key or condition.condition_id,
                ),
                alerts=("Informação factual insuficiente.",),
                human_review_required=True,
            )
        value = fact["value"]
        source = self._fact_source(fact)
        verified = self._apply(
            operation,
            value,
            condition.expected_value,
        )
        return ConditionVerification(
            condition=condition,
            state=(
                ConstraintAnalysisState.VERIFIED
                if verified
                else ConstraintAnalysisState.NOT_VERIFIED
            ),
            facts_used=(FactUsed(
                key=condition.fact_key or condition.condition_id,
                value=value,
                source=source,
            ),),
            operation_performed=operation,
            explanation=(
                "A operação determinística foi executada sobre o fato "
                "explícito; o estado descreve somente esta condição."
            ),
            pending_information=(),
            alerts=(),
            human_review_required=False,
        )

    def _verify_assisted(
        self,
        condition: NormativeCondition,
        record: NormativeConditionRecord,
        fact: Mapping[str, object] | None,
    ) -> ConditionVerification:
        proposal_text = (
            fact.get("preliminary_conclusion")
            if fact is not None
            else None
        )
        if not isinstance(proposal_text, str) or not proposal_text.strip():
            return ConditionVerification(
                condition=condition,
                state=ConstraintAnalysisState.INSUFFICIENT_INFORMATION,
                facts_used=self._facts_from_record(fact),
                operation_performed="assisted_review_preparation",
                explanation=(
                    "A condição assistida não possui elementos explícitos "
                    "suficientes para formular proposta."
                ),
                pending_information=self._missing_from_record(fact) or (
                    condition.fact_key or condition.condition_id,
                ),
                alerts=("Revisão humana permanece necessária.",),
                human_review_required=True,
            )
        proposal = AssistedFramingProposal(
            preliminary_conclusion=proposal_text.strip(),
            favorable_facts=self._text_tuple(fact, "favorable_facts"),
            contrary_facts=self._text_tuple(fact, "contrary_facts"),
            missing_information=self._text_tuple(
                fact,
                "missing_information",
            ),
            normative_reference=condition.origin.legal_reference,
            validation_questions=tuple(record.validation_questions),
            review_justification=(
                "A condição é qualitativa e a proposta usa somente "
                "elementos factuais explicitamente registrados."
            ),
        )
        return ConditionVerification(
            condition=condition,
            state=ConstraintAnalysisState.REVIEW_RECOMMENDED,
            facts_used=self._facts_from_record(fact),
            operation_performed="assisted_review_preparation",
            explanation=(
                "Foi organizada uma proposta preliminar não definitiva "
                "para validação humana."
            ),
            pending_information=proposal.missing_information,
            alerts=("Proposta não definitiva; revisão humana obrigatória.",),
            human_review_required=True,
            proposal=proposal,
        )

    def _fact(
        self,
        condition_id: str,
        candidate: QualifiedCriterionCandidate,
    ) -> Mapping[str, object] | None:
        raw = self._context.metadata.get(self.FACTS_METADATA_KEY, ())
        if not isinstance(raw, tuple) or any(
            not isinstance(item, Mapping) for item in raw
        ):
            raise ConstraintEvaluationError(
                f"{self.FACTS_METADATA_KEY} deve ser uma coleção imutável."
            )
        matches = tuple(
            item
            for item in raw
            if item.get("condition_id") == condition_id
            and item.get("criterion_id")
            == candidate.source_candidate.criterion_id
            and item.get("activity_id")
            == candidate.source_candidate.activity.activity_id
            and item.get("functional_exercise_id")
            == candidate.source_candidate.functional_exercise.id
        )
        if len(matches) > 1:
            raise ConstraintEvaluationError(
                f"Fato duplicado para a condição {condition_id}."
            )
        return matches[0] if matches else None

    @staticmethod
    def _condition(
        record: NormativeConditionRecord,
        criterion_id: str,
    ) -> NormativeCondition:
        if record.criterion_id != criterion_id:
            raise ConstraintEvaluationError(
                "Condição pertence a critério diferente do candidato."
            )
        try:
            classification = ConditionClassification(
                record.classification
            )
        except (TypeError, ValueError):
            classification = None
        return NormativeCondition(
            condition_id=record.id,
            criterion_id=record.criterion_id,
            classification=classification,
            description=record.description,
            operation=record.operation,
            fact_key=record.fact_key,
            expected_value=record.expected_value,
            origin=NormativeOrigin(
                document_id=record.document_id,
                legal_reference=record.legal_reference,
                hierarchy=tuple(record.hierarchy),
            ),
        )

    @staticmethod
    def _apply(
        operation: str,
        value: object,
        expected: object,
    ) -> bool:
        if operation == "equals":
            return value == expected
        if operation == "not_equals":
            return value != expected
        if operation == "contains":
            return (
                isinstance(value, (tuple, list, set, frozenset))
                and expected in value
            )
        if operation == "is_true":
            return value is True
        if operation == "is_false":
            return value is False
        raise AssertionError("operação deveria ter sido validada.")

    @classmethod
    def _normative_gap(
        cls,
        criterion_id: str,
    ) -> ConditionVerification:
        condition = NormativeCondition(
            condition_id=f"gap:{criterion_id}",
            criterion_id=criterion_id,
            classification=None,
            description="Condições normativas não estruturadas.",
            operation=None,
            fact_key=None,
            expected_value=None,
            origin=NormativeOrigin(
                document_id="unknown",
                legal_reference="não estruturada",
                hierarchy=(),
            ),
        )
        return cls._gap_for_condition(
            condition,
            "O Modelo Normativo não forneceu condições estruturadas.",
        )

    @staticmethod
    def _gap_for_condition(
        condition: NormativeCondition,
        message: str,
    ) -> ConditionVerification:
        return ConditionVerification(
            condition=condition,
            state=ConstraintAnalysisState.NORMATIVE_GAP,
            facts_used=(),
            operation_performed="none",
            explanation=message,
            pending_information=(condition.condition_id,),
            alerts=("Lacuna normativa explícita.",),
            human_review_required=True,
        )

    @staticmethod
    def _facts_from_record(
        fact: Mapping[str, object] | None,
    ) -> tuple[FactUsed, ...]:
        if fact is None or "value" not in fact or fact["value"] is None:
            return ()
        return (FactUsed(
            key=str(fact.get("fact_key") or fact["condition_id"]),
            value=fact["value"],
            source=ConstraintEvaluationEngine._fact_source(fact),
        ),)

    @staticmethod
    def _fact_source(fact: Mapping[str, object]) -> str:
        source = fact.get("source")
        if not isinstance(source, str) or not source.strip():
            raise ConstraintEvaluationError(
                "Fato utilizado exige source textual."
            )
        return source.strip()

    @staticmethod
    def _missing_from_record(
        fact: Mapping[str, object] | None,
    ) -> tuple[str, ...]:
        if fact is None:
            return ()
        return ConstraintEvaluationEngine._text_tuple(
            fact,
            "missing_information",
        )

    @staticmethod
    def _text_tuple(
        values: Mapping[str, object],
        field: str,
    ) -> tuple[str, ...]:
        raw = values.get(field, ())
        if not isinstance(raw, tuple) or any(
            not isinstance(item, str) or not item.strip()
            for item in raw
        ):
            raise ConstraintEvaluationError(
                f"{field} deve ser uma tupla de textos."
            )
        return tuple(item.strip() for item in raw)

    @staticmethod
    def _require_unique_conditions(
        conditions: tuple[NormativeCondition, ...],
    ) -> None:
        ids = tuple(item.condition_id for item in conditions)
        if len(ids) != len(set(ids)):
            raise ConstraintEvaluationError(
                "Condições normativas duplicadas."
            )

    @staticmethod
    def _unique_facts(
        verifications: tuple[ConditionVerification, ...],
    ) -> tuple[FactUsed, ...]:
        result: list[FactUsed] = []
        seen: set[tuple[str, str]] = set()
        for verification in verifications:
            for fact in verification.facts_used:
                key = (fact.key, fact.source)
                if key not in seen:
                    seen.add(key)
                    result.append(fact)
        return tuple(result)

    @staticmethod
    def _unique_devices(
        conditions: tuple[NormativeCondition, ...],
    ) -> tuple[NormativeOrigin, ...]:
        result: list[NormativeOrigin] = []
        seen: set[tuple[str, str]] = set()
        for condition in conditions:
            key = (
                condition.origin.document_id,
                condition.origin.legal_reference,
            )
            if key not in seen:
                seen.add(key)
                result.append(condition.origin)
        return tuple(result)

    @staticmethod
    def _unique_text(values) -> tuple[str, ...]:
        result: list[str] = []
        seen: set[str] = set()
        for value in values:
            if value not in seen:
                seen.add(value)
                result.append(value)
        return tuple(result)


__all__ = [
    "AssistedFramingProposal",
    "ConditionClassification",
    "ConditionVerification",
    "ConstraintAnalysisState",
    "ConstraintEvaluatedCandidate",
    "ConstraintEvaluatedCandidateCollection",
    "ConstraintEvaluationEngine",
    "ConstraintEvaluationError",
    "ConstraintNormativeModel",
    "FactUsed",
    "NormativeCondition",
]
