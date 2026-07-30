"""Preparação factual tipada para futura execução normativa."""

from __future__ import annotations

from collections.abc import Iterator, Mapping, Sequence
from dataclasses import dataclass, replace
from decimal import Decimal
from enum import Enum
import json
from pathlib import Path
from types import MappingProxyType
from typing import Any
from uuid import NAMESPACE_URL, uuid5

from applications.rsc.criterion_assessment import (
    CriterionAssessment,
    CriterionAssessmentCollection,
)
from applications.rsc.criterion_candidates import (
    FactualTraceability,
    NormativeOrigin,
)
from applications.rsc.evaluation_context import (
    EvaluationActivity,
    EvaluationContext,
    EvaluationDocument,
    EvaluationFunctionalExercise,
)


class ExecutionFactError(ValueError):
    """Falha estrutural durante a preparação de fatos de execução."""


class UnknownExecutionRuleError(ExecutionFactError):
    """Um Assessment não possui regra executável correspondente."""


class InvalidExecutionReferenceError(ExecutionFactError):
    """Uma regra ou fato aponta para uma identidade inconsistente."""


class DuplicateExecutionFactError(ExecutionFactError):
    """Duas projeções de execução possuem a mesma identidade."""


class ConfidenceOrigin(str, Enum):
    """Origem estrutural da confiança, nunca probabilidade."""

    EXPLICIT = "EXPLICIT"
    DERIVED = "DERIVED"
    DECLARED = "DECLARED"


class CanonicalFactType(str, Enum):
    PERIOD_START = "period_start"
    PERIOD_END = "period_end"
    EXECUTION_ROLE = "execution_role"
    MEASUREMENT_UNIT = "measurement_unit"
    DESIGNATION_COUNT = "designation_count"
    PROJECT_COUNT = "project_count"
    PRODUCT_COUNT = "product_count"
    MANDATE_COUNT = "mandate_count"
    EVENT_COUNT = "event_count"
    TRAINING_COUNT = "training_count"
    AWARD_COUNT = "award_count"
    SYSTEM_COUNT = "system_count"
    PATENT_COUNT = "patent_count"
    COURSE_COUNT = "course_count"
    RESEARCH_GROUP_COUNT = "research_group_count"
    PUBLICATION_COUNT = "publication_count"
    CONSTRAINT_FACT = "constraint_fact"


class OverlapStatus(str, Enum):
    NONE = "NONE"
    POSSIBLE = "POSSIBLE"
    CONFIRMED = "CONFIRMED"
    UNKNOWN = "UNKNOWN"


class MeasurementValidationState(str, Enum):
    AVAILABLE = "AVAILABLE"
    MISSING = "MISSING"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"


@dataclass(frozen=True, slots=True)
class FactTraceability:
    """Origem reversível de um fato canônico."""

    source_object: str
    source_field: str
    source_identity: str
    normative_reference: str | None = None

    def __post_init__(self) -> None:
        _require_text(self.source_object, "source_object")
        _require_text(self.source_field, "source_field")
        _require_text(self.source_identity, "source_identity")
        if self.normative_reference is not None:
            _require_text(self.normative_reference, "normative_reference")


CanonicalValue = str | int | bool | Decimal


@dataclass(frozen=True, slots=True)
class CanonicalFact:
    fact_id: str
    fact_type: CanonicalFactType
    value: CanonicalValue
    unit: str | None
    source: str
    confidence_origin: ConfidenceOrigin
    traceability: FactTraceability

    def __post_init__(self) -> None:
        _require_text(self.fact_id, "fact_id")
        if not isinstance(self.fact_type, CanonicalFactType):
            raise TypeError("fact_type deve ser CanonicalFactType.")
        if not isinstance(self.value, (str, int, bool, Decimal)):
            raise TypeError("value deve ser um valor canônico imutável.")
        if self.unit is not None:
            _require_text(self.unit, "unit")
        _require_text(self.source, "source")
        if not isinstance(self.confidence_origin, ConfidenceOrigin):
            raise TypeError("confidence_origin deve ser ConfidenceOrigin.")
        if not isinstance(self.traceability, FactTraceability):
            raise TypeError("traceability deve ser FactTraceability.")


@dataclass(frozen=True, slots=True)
class CanonicalDocument:
    document_id: str
    document_identity: str
    name: str


@dataclass(frozen=True, slots=True)
class CanonicalActivity:
    activity_id: str
    description: str


@dataclass(frozen=True, slots=True)
class CanonicalFunctionalExercise:
    functional_exercise_id: str
    exercise_type_code: str
    role: str


@dataclass(frozen=True, slots=True)
class CanonicalTimeInterval:
    start: str | None
    end: str | None
    start_source_field: str
    end_source_field: str


@dataclass(frozen=True, slots=True)
class Measurement:
    amount: int | Decimal | None
    unit: str
    measurement_type: str
    source: str
    validation_state: MeasurementValidationState

    def __post_init__(self) -> None:
        if self.amount is not None and (
            isinstance(self.amount, bool)
            or not isinstance(self.amount, (int, Decimal))
        ):
            raise TypeError("amount deve ser inteiro, Decimal ou None.")
        _require_text(self.unit, "unit")
        _require_text(self.measurement_type, "measurement_type")
        _require_text(self.source, "source")
        if not isinstance(
            self.validation_state,
            MeasurementValidationState,
        ):
            raise TypeError(
                "validation_state deve ser MeasurementValidationState."
            )


@dataclass(frozen=True, slots=True)
class ExecutionOccurrence:
    occurrence_id: str
    criterion_id: str
    origin: FactualTraceability
    quantity: int | Decimal | None
    unit: str
    period: CanonicalTimeInterval
    related_documents: tuple[CanonicalDocument, ...]
    related_activity: CanonicalActivity
    related_functional_exercise: CanonicalFunctionalExercise
    overlap_status: OverlapStatus
    explanation: str

    def __post_init__(self) -> None:
        _require_text(self.occurrence_id, "occurrence_id")
        _require_text(self.criterion_id, "criterion_id")
        if not isinstance(self.origin, FactualTraceability):
            raise TypeError("origin deve ser FactualTraceability.")
        if self.quantity is not None and (
            isinstance(self.quantity, bool)
            or not isinstance(self.quantity, (int, Decimal))
        ):
            raise TypeError("quantity deve ser inteiro, Decimal ou None.")
        _require_text(self.unit, "unit")
        if not isinstance(self.period, CanonicalTimeInterval):
            raise TypeError("period deve ser CanonicalTimeInterval.")
        _require_tuple(
            self.related_documents,
            CanonicalDocument,
            "related_documents",
        )
        if not isinstance(self.related_activity, CanonicalActivity):
            raise TypeError("related_activity deve ser CanonicalActivity.")
        if not isinstance(
            self.related_functional_exercise,
            CanonicalFunctionalExercise,
        ):
            raise TypeError(
                "related_functional_exercise deve ser "
                "CanonicalFunctionalExercise."
            )
        if not isinstance(self.overlap_status, OverlapStatus):
            raise TypeError("overlap_status deve ser OverlapStatus.")
        _require_text(self.explanation, "explanation")


@dataclass(frozen=True, slots=True)
class ExecutionNormativeTraceability:
    execution_rule_id: str
    criterion_id: str
    requirement_id: str
    article_reference: str
    annex_reference: str
    scoring_table: str
    assessment_origin: NormativeOrigin


@dataclass(frozen=True, slots=True)
class ExecutionFact:
    execution_fact_id: str
    criterion_id: str
    requirement_id: str
    execution_rule_id: str
    assessment_state: str
    computability_level: str
    measurement: Measurement
    quantified_occurrences: tuple[ExecutionOccurrence, ...]
    canonical_facts: tuple[CanonicalFact, ...]
    canonical_documents: tuple[CanonicalDocument, ...]
    canonical_activities: tuple[CanonicalActivity, ...]
    canonical_functional_exercises: tuple[
        CanonicalFunctionalExercise, ...
    ]
    canonical_time_interval: CanonicalTimeInterval
    selected_variant: str | None
    possible_variants: tuple[str, ...]
    variant_fact_available: bool
    variant_review_required: bool
    overlap_candidates: tuple[str, ...]
    unresolved_items: tuple[str, ...]
    human_review_required: bool
    normative_traceability: ExecutionNormativeTraceability
    factual_traceability: FactualTraceability
    explanation: str
    source_assessment: CriterionAssessment

    def __post_init__(self) -> None:
        for field_name in (
            "execution_fact_id",
            "criterion_id",
            "requirement_id",
            "execution_rule_id",
            "assessment_state",
            "computability_level",
            "explanation",
        ):
            _require_text(getattr(self, field_name), field_name)
        if not isinstance(self.measurement, Measurement):
            raise TypeError("measurement deve ser Measurement.")
        _require_tuple(
            self.quantified_occurrences,
            ExecutionOccurrence,
            "quantified_occurrences",
        )
        _require_tuple(
            self.canonical_facts,
            CanonicalFact,
            "canonical_facts",
        )
        _require_tuple(
            self.canonical_documents,
            CanonicalDocument,
            "canonical_documents",
        )
        _require_tuple(
            self.canonical_activities,
            CanonicalActivity,
            "canonical_activities",
        )
        _require_tuple(
            self.canonical_functional_exercises,
            CanonicalFunctionalExercise,
            "canonical_functional_exercises",
        )
        if self.selected_variant is not None:
            raise ValueError(
                "selected_variant deve permanecer None nesta camada."
            )
        _require_text_tuple(self.possible_variants, "possible_variants")
        _require_text_tuple(self.overlap_candidates, "overlap_candidates")
        _require_text_tuple(self.unresolved_items, "unresolved_items")
        if not isinstance(
            self.normative_traceability,
            ExecutionNormativeTraceability,
        ):
            raise TypeError(
                "normative_traceability deve ser "
                "ExecutionNormativeTraceability."
            )
        if not isinstance(self.factual_traceability, FactualTraceability):
            raise TypeError(
                "factual_traceability deve ser FactualTraceability."
            )
        if not isinstance(self.source_assessment, CriterionAssessment):
            raise TypeError(
                "source_assessment deve ser CriterionAssessment."
            )
        fact_ids = tuple(item.fact_id for item in self.canonical_facts)
        if len(fact_ids) != len(set(fact_ids)):
            raise DuplicateExecutionFactError(
                "canonical_facts contém fatos duplicados."
            )


@dataclass(frozen=True, slots=True)
class ExecutionFactCollection:
    facts: tuple[ExecutionFact, ...] = ()

    def __post_init__(self) -> None:
        _require_tuple(self.facts, ExecutionFact, "facts")
        ids = tuple(item.execution_fact_id for item in self.facts)
        if len(ids) != len(set(ids)):
            raise DuplicateExecutionFactError(
                "ExecutionFactCollection contém identidades duplicadas."
            )

    def __iter__(self) -> Iterator[ExecutionFact]:
        return iter(self.facts)

    def __len__(self) -> int:
        return len(self.facts)


class ExecutionFactBuilder:
    """Normaliza Assessments sem pontuar, agregar ou selecionar variantes."""

    def __init__(
        self,
        execution_rules: Mapping[str, Any],
        execution_manifest: Mapping[str, Any],
    ) -> None:
        if not isinstance(execution_rules, Mapping):
            raise TypeError("execution_rules deve ser um mapeamento.")
        if not isinstance(execution_manifest, Mapping):
            raise TypeError("execution_manifest deve ser um mapeamento.")
        self._rules = self._index_rules(execution_rules)
        self._manifest = self._index_manifest(execution_manifest)
        self._validate_catalogs()

    @classmethod
    def from_files(
        cls,
        execution_rules_path: str | Path,
        execution_manifest_path: str | Path,
    ) -> "ExecutionFactBuilder":
        rules = _read_json_object(execution_rules_path)
        manifest = _read_json_object(execution_manifest_path)
        return cls(rules, manifest)

    def build(
        self,
        assessments: CriterionAssessmentCollection,
        context: EvaluationContext,
    ) -> ExecutionFactCollection:
        if not isinstance(assessments, CriterionAssessmentCollection):
            raise TypeError(
                "assessments deve ser CriterionAssessmentCollection."
            )
        if not isinstance(context, EvaluationContext):
            raise TypeError("context deve ser EvaluationContext.")

        indexes = _ContextIndexes(context)
        provisional = tuple(
            self._build_fact(assessment, indexes)
            for assessment in assessments
        )
        overlap_map = self._overlap_candidates(provisional)
        completed = tuple(
            self._with_overlap(fact, overlap_map[fact.execution_fact_id])
            for fact in provisional
        )
        return ExecutionFactCollection(completed)

    def _build_fact(
        self,
        assessment: CriterionAssessment,
        indexes: "_ContextIndexes",
    ) -> ExecutionFact:
        rule = self._rules.get(assessment.criterion_id)
        if rule is None:
            raise UnknownExecutionRuleError(
                f"Regra ausente para {assessment.criterion_id}."
            )
        manifest = self._manifest[assessment.criterion_id]
        self._validate_assessment_rule(assessment, rule, manifest)

        trace = assessment.traceability.factual_origin
        activity = indexes.activity(trace.activity_id)
        exercise = indexes.exercise(trace.functional_exercise_id)
        documents = indexes.documents(assessment)
        canonical_activity = CanonicalActivity(
            activity_id=activity.activity_id,
            description=activity.description,
        )
        canonical_exercise = CanonicalFunctionalExercise(
            functional_exercise_id=exercise.id,
            exercise_type_code=exercise.exercise_type_code,
            role=exercise.role,
        )
        period = CanonicalTimeInterval(
            start=exercise.start_date,
            end=exercise.end_date,
            start_source_field="start_date",
            end_source_field="end_date",
        )
        facts, missing = self._canonical_facts(
            assessment,
            exercise,
            rule,
        )
        measurement = self._measurement(rule, facts)
        variants = self._variant(rule, facts)
        unresolved = _unique_text((
            *missing,
            *assessment.normative_gaps,
            *assessment.warnings,
            *(
                ("variant_selection_requires_review",)
                if variants.review_required
                else ()
            ),
        ))
        fact_id = _stable_id(
            "execution-fact",
            rule["id"],
            trace.activity_id,
            trace.functional_exercise_id,
            trace.functional_assignment_evidence_id,
        )
        occurrence = ExecutionOccurrence(
            occurrence_id=_stable_id("occurrence", fact_id),
            criterion_id=assessment.criterion_id,
            origin=trace,
            quantity=measurement.amount,
            unit=measurement.unit,
            period=period,
            related_documents=documents,
            related_activity=canonical_activity,
            related_functional_exercise=canonical_exercise,
            overlap_status=OverlapStatus.UNKNOWN,
            explanation=(
                "Ocorrência estrutural preservada sem soma, eliminação "
                "ou resolução de sobreposição."
            ),
        )
        normative = ExecutionNormativeTraceability(
            execution_rule_id=rule["id"],
            criterion_id=assessment.criterion_id,
            requirement_id=assessment.requirement_id,
            article_reference=rule["article_reference"],
            annex_reference=rule["annex_reference"],
            scoring_table=rule["scoring_table"],
            assessment_origin=assessment.traceability.normative_origin,
        )
        return ExecutionFact(
            execution_fact_id=fact_id,
            criterion_id=assessment.criterion_id,
            requirement_id=assessment.requirement_id,
            execution_rule_id=rule["id"],
            assessment_state=assessment.assessment_status.value,
            computability_level=rule["computability_level"],
            measurement=measurement,
            quantified_occurrences=(occurrence,),
            canonical_facts=facts,
            canonical_documents=documents,
            canonical_activities=(canonical_activity,),
            canonical_functional_exercises=(canonical_exercise,),
            canonical_time_interval=period,
            selected_variant=None,
            possible_variants=variants.options,
            variant_fact_available=variants.fact_available,
            variant_review_required=variants.review_required,
            overlap_candidates=(),
            unresolved_items=unresolved,
            human_review_required=(
                assessment.human_review_required
                or bool(unresolved)
                or rule["computability_level"] != "FULLY_EXECUTABLE"
            ),
            normative_traceability=normative,
            factual_traceability=trace,
            explanation=self._explanation(
                facts,
                missing,
                documents,
                rule,
                variants,
            ),
            source_assessment=assessment,
        )

    def _canonical_facts(
        self,
        assessment: CriterionAssessment,
        exercise: EvaluationFunctionalExercise,
        rule: Mapping[str, Any],
    ) -> tuple[tuple[CanonicalFact, ...], tuple[str, ...]]:
        result: list[CanonicalFact] = []
        if exercise.start_date:
            result.append(self._domain_fact(
                assessment,
                CanonicalFactType.PERIOD_START,
                exercise.start_date,
                None,
                "start_date",
                exercise.id,
            ))
        if exercise.end_date:
            result.append(self._domain_fact(
                assessment,
                CanonicalFactType.PERIOD_END,
                exercise.end_date,
                None,
                "end_date",
                exercise.id,
            ))
        if exercise.role:
            result.append(self._domain_fact(
                assessment,
                CanonicalFactType.EXECUTION_ROLE,
                exercise.role,
                None,
                "role",
                exercise.id,
            ))
        result.append(CanonicalFact(
            fact_id=_stable_id(
                "fact",
                assessment.criterion_id,
                "measurement_unit",
            ),
            fact_type=CanonicalFactType.MEASUREMENT_UNIT,
            value=rule["measurement_unit"],
            unit=None,
            source="criterion_execution_rules",
            confidence_origin=ConfidenceOrigin.DECLARED,
            traceability=FactTraceability(
                source_object="ExecutionRule",
                source_field="measurement_unit",
                source_identity=rule["id"],
                normative_reference=rule["scoring_table"],
            ),
        ))

        facts_by_key = {
            item.key: item for item in assessment.traceability.facts
        }
        required = _text_sequence(rule, "required_facts")
        aliases = {
            "period_start": CanonicalFactType.PERIOD_START,
            "period_end": CanonicalFactType.PERIOD_END,
            "role": CanonicalFactType.EXECUTION_ROLE,
        }
        existing_types = {item.fact_type for item in result}
        missing: list[str] = []
        for key in required:
            alias = aliases.get(key)
            if alias is not None and alias in existing_types:
                continue
            source_fact = facts_by_key.get(key)
            if source_fact is None:
                missing.append(key)
                continue
            fact_type = _FACT_TYPES_BY_KEY.get(
                key,
                CanonicalFactType.CONSTRAINT_FACT,
            )
            result.append(CanonicalFact(
                fact_id=_stable_id(
                    "fact",
                    assessment.criterion_id,
                    key,
                    source_fact.source,
                ),
                fact_type=fact_type,
                value=_canonical_value(source_fact.value, key),
                unit=(
                    rule["measurement_unit"]
                    if key.endswith("_count")
                    else None
                ),
                source=source_fact.source,
                confidence_origin=ConfidenceOrigin.EXPLICIT,
                traceability=FactTraceability(
                    source_object="FactUsed",
                    source_field="value",
                    source_identity=key,
                ),
            ))
        return tuple(result), tuple(missing)

    @staticmethod
    def _domain_fact(
        assessment: CriterionAssessment,
        fact_type: CanonicalFactType,
        value: CanonicalValue,
        unit: str | None,
        source_field: str,
        source_identity: str,
    ) -> CanonicalFact:
        return CanonicalFact(
            fact_id=_stable_id(
                "fact",
                assessment.criterion_id,
                fact_type.value,
                source_identity,
            ),
            fact_type=fact_type,
            value=value,
            unit=unit,
            source="EvaluationFunctionalExercise",
            confidence_origin=ConfidenceOrigin.EXPLICIT,
            traceability=FactTraceability(
                source_object="EvaluationFunctionalExercise",
                source_field=source_field,
                source_identity=source_identity,
            ),
        )

    @staticmethod
    def _measurement(
        rule: Mapping[str, Any],
        facts: tuple[CanonicalFact, ...],
    ) -> Measurement:
        required = _text_sequence(rule, "required_facts")
        quantity_keys = tuple(
            item for item in required if item.endswith("_count")
        )
        by_type = {item.fact_type.value: item for item in facts}
        amount: int | Decimal | None = None
        source = "criterion_execution_rules"
        if quantity_keys:
            quantity = by_type.get(quantity_keys[0])
            if quantity is not None:
                if (
                    isinstance(quantity.value, bool)
                    or not isinstance(quantity.value, (int, Decimal))
                ):
                    raise ExecutionFactError(
                        f"{quantity_keys[0]} deve ser quantitativo."
                    )
                amount = quantity.value
                source = quantity.source
            validation = (
                MeasurementValidationState.AVAILABLE
                if amount is not None
                else MeasurementValidationState.MISSING
            )
        else:
            validation = MeasurementValidationState.REVIEW_REQUIRED
        return Measurement(
            amount=amount,
            unit=_text(rule, "measurement_unit"),
            measurement_type=_text(rule, "measurement_type"),
            source=source,
            validation_state=validation,
        )

    @staticmethod
    def _variant(
        rule: Mapping[str, Any],
        facts: tuple[CanonicalFact, ...],
    ) -> "_VariantState":
        raw = rule.get("variant_rule")
        if not isinstance(raw, Mapping):
            raise ExecutionFactError("variant_rule deve ser um objeto.")
        variant_type = _text(raw, "type")
        options = _text_sequence(raw, "variants")
        role_available = any(
            item.fact_type is CanonicalFactType.EXECUTION_ROLE
            for item in facts
        )
        return _VariantState(
            options=options,
            fact_available=role_available if variant_type == "ROLE_BASED" else False,
            review_required=variant_type != "NONE",
        )

    @staticmethod
    def _overlap_candidates(
        facts: tuple[ExecutionFact, ...],
    ) -> dict[str, tuple[str, ...]]:
        result: dict[str, tuple[str, ...]] = {}
        for fact in facts:
            trace = fact.factual_traceability
            related = tuple(
                other.execution_fact_id
                for other in facts
                if other.execution_fact_id != fact.execution_fact_id
                and (
                    other.factual_traceability.activity_id,
                    other.factual_traceability.functional_exercise_id,
                    (
                        other.factual_traceability
                        .functional_assignment_evidence_id
                    ),
                )
                == (
                    trace.activity_id,
                    trace.functional_exercise_id,
                    trace.functional_assignment_evidence_id,
                )
            )
            result[fact.execution_fact_id] = related
        return result

    @staticmethod
    def _with_overlap(
        fact: ExecutionFact,
        candidates: tuple[str, ...],
    ) -> ExecutionFact:
        status = OverlapStatus.POSSIBLE if candidates else OverlapStatus.NONE
        occurrences = tuple(
            replace(item, overlap_status=status)
            for item in fact.quantified_occurrences
        )
        explanation = (
            f"{fact.explanation} Sobreposição estrutural possível registrada."
            if candidates
            else f"{fact.explanation} Nenhuma sobreposição estrutural observada."
        )
        return replace(
            fact,
            quantified_occurrences=occurrences,
            overlap_candidates=candidates,
            explanation=explanation,
        )

    @staticmethod
    def _explanation(
        facts: tuple[CanonicalFact, ...],
        missing: tuple[str, ...],
        documents: tuple[CanonicalDocument, ...],
        rule: Mapping[str, Any],
        variants: "_VariantState",
    ) -> str:
        normalized = ", ".join(item.fact_type.value for item in facts)
        absent = ", ".join(missing) if missing else "nenhum"
        variant = (
            "variantes apenas transportadas, sem seleção"
            if variants.options
            else "regra sem variantes"
        )
        return (
            f"Regra futura {rule['id']}; fatos normalizados: {normalized}; "
            f"fatos ausentes: {absent}; documentos: {len(documents)}; "
            f"{variant}. Nenhuma pontuação, agregação ou decisão foi executada."
        )

    @staticmethod
    def _index_rules(
        document: Mapping[str, Any],
    ) -> Mapping[str, Mapping[str, Any]]:
        raw = document.get("rules")
        if not isinstance(raw, Sequence) or isinstance(raw, (str, bytes)):
            raise ExecutionFactError("rules deve ser uma coleção.")
        result: dict[str, Mapping[str, Any]] = {}
        for item in raw:
            if not isinstance(item, Mapping):
                raise ExecutionFactError("rules contém item inválido.")
            criterion_id = _text(item, "criterion_id")
            if criterion_id in result:
                raise DuplicateExecutionFactError(
                    f"Regra duplicada para {criterion_id}."
                )
            result[criterion_id] = MappingProxyType(dict(item))
        return MappingProxyType(result)

    @staticmethod
    def _index_manifest(
        document: Mapping[str, Any],
    ) -> Mapping[str, Mapping[str, Any]]:
        raw = document.get("entries")
        if not isinstance(raw, Sequence) or isinstance(raw, (str, bytes)):
            raise ExecutionFactError("entries deve ser uma coleção.")
        result: dict[str, Mapping[str, Any]] = {}
        for item in raw:
            if not isinstance(item, Mapping):
                raise ExecutionFactError("entries contém item inválido.")
            criterion_id = _text(item, "criterion_id")
            if criterion_id in result:
                raise DuplicateExecutionFactError(
                    f"Manifesto duplicado para {criterion_id}."
                )
            result[criterion_id] = MappingProxyType(dict(item))
        return MappingProxyType(result)

    def _validate_catalogs(self) -> None:
        if set(self._rules) != set(self._manifest):
            raise InvalidExecutionReferenceError(
                "Regras e manifesto possuem coberturas diferentes."
            )
        for criterion_id, rule in self._rules.items():
            entry = self._manifest[criterion_id]
            if (
                _text(rule, "id") != _text(entry, "rule_id")
                or _text(rule, "requirement_id")
                != _text(entry, "requirement_id")
                or _text(rule, "scoring_table")
                != _text(entry, "table_id")
            ):
                raise InvalidExecutionReferenceError(
                    f"Manifesto divergente para {criterion_id}."
                )

    @staticmethod
    def _validate_assessment_rule(
        assessment: CriterionAssessment,
        rule: Mapping[str, Any],
        manifest: Mapping[str, Any],
    ) -> None:
        if (
            assessment.criterion_id != _text(rule, "criterion_id")
            or assessment.requirement_id != _text(rule, "requirement_id")
            or assessment.criterion_id != _text(manifest, "criterion_id")
        ):
            raise InvalidExecutionReferenceError(
                "Assessment, regra e manifesto não correspondem."
            )


@dataclass(frozen=True, slots=True)
class _VariantState:
    options: tuple[str, ...]
    fact_available: bool
    review_required: bool


class _ContextIndexes:
    def __init__(self, context: EvaluationContext) -> None:
        self._activities = {
            item.activity_id: item for item in context.activities
        }
        self._exercises = {
            item.id: item for item in context.functional_exercises
        }
        self._documents = {
            item.id: item for item in context.documents
        }

    def activity(self, identity: str) -> EvaluationActivity:
        return self._required(self._activities, identity, "Activity")

    def exercise(self, identity: str) -> EvaluationFunctionalExercise:
        return self._required(
            self._exercises,
            identity,
            "FunctionalExercise",
        )

    def documents(
        self,
        assessment: CriterionAssessment,
    ) -> tuple[CanonicalDocument, ...]:
        result: list[CanonicalDocument] = []
        seen: set[str] = set()
        factual = assessment.traceability.factual_origin
        source_document = self._required(
            self._documents,
            factual.document_id,
            "Document",
        )
        if (
            source_document.document_identity.lower()
            != factual.document_identity.lower()
        ):
            raise InvalidExecutionReferenceError(
                "Document identity divergente na rastreabilidade factual."
            )
        result.append(CanonicalDocument(
            document_id=source_document.id,
            document_identity=source_document.document_identity,
            name=source_document.name,
        ))
        seen.add(source_document.id)
        for presented in assessment.traceability.documents:
            document = self._required(
                self._documents,
                presented.document_id,
                "Document",
            )
            if (
                document.document_identity.lower()
                != presented.document_identity.lower()
            ):
                raise InvalidExecutionReferenceError(
                    "Document identity divergente no Assessment."
                )
            if document.id not in seen:
                seen.add(document.id)
                result.append(CanonicalDocument(
                    document_id=document.id,
                    document_identity=document.document_identity,
                    name=document.name,
                ))
        return tuple(result)

    @staticmethod
    def _required(
        index: Mapping[str, Any],
        identity: str,
        label: str,
    ) -> Any:
        value = index.get(identity)
        if value is None:
            raise InvalidExecutionReferenceError(
                f"{label} ausente no EvaluationContext: {identity}."
            )
        return value


_FACT_TYPES_BY_KEY = {
    item.value: item
    for item in CanonicalFactType
    if item is not CanonicalFactType.CONSTRAINT_FACT
}


def _stable_id(kind: str, *parts: str) -> str:
    return str(uuid5(NAMESPACE_URL, "|".join((kind, *parts))))


def _canonical_value(value: object, name: str) -> CanonicalValue:
    if isinstance(value, bool):
        return value
    if isinstance(value, (str, int, Decimal)):
        return value
    if isinstance(value, float):
        return Decimal(str(value))
    raise ExecutionFactError(
        f"{name} possui valor não canônico: {type(value).__name__}."
    )


def _read_json_object(path: str | Path) -> Mapping[str, Any]:
    resolved = Path(path)
    try:
        value = json.loads(resolved.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ExecutionFactError(
            f"Não foi possível ler {resolved}: {exc}."
        ) from exc
    if not isinstance(value, dict):
        raise ExecutionFactError(f"{resolved} deve conter um objeto JSON.")
    return value


def _text(values: Mapping[str, Any], field: str) -> str:
    value = values.get(field)
    if not isinstance(value, str) or not value.strip():
        raise ExecutionFactError(f"{field} deve ser textual.")
    return value.strip()


def _text_sequence(
    values: Mapping[str, Any],
    field: str,
) -> tuple[str, ...]:
    raw = values.get(field, ())
    if not isinstance(raw, Sequence) or isinstance(raw, (str, bytes)):
        raise ExecutionFactError(f"{field} deve ser uma coleção.")
    result = tuple(raw)
    _require_text_tuple(result, field)
    return result


def _require_text(value: object, field: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise TypeError(f"{field} deve ser textual.")


def _require_text_tuple(value: object, field: str) -> None:
    if not isinstance(value, tuple) or any(
        not isinstance(item, str) or not item.strip()
        for item in value
    ):
        raise TypeError(f"{field} deve ser uma tupla de textos.")


def _require_tuple(value: object, item_type: type, field: str) -> None:
    if not isinstance(value, tuple) or any(
        not isinstance(item, item_type) for item in value
    ):
        raise TypeError(
            f"{field} deve ser uma tupla de {item_type.__name__}."
        )


def _unique_text(values: Sequence[str]) -> tuple[str, ...]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        if value and value not in seen:
            seen.add(value)
            result.append(value)
    return tuple(result)


__all__ = [
    "CanonicalActivity",
    "CanonicalDocument",
    "CanonicalFact",
    "CanonicalFactType",
    "CanonicalFunctionalExercise",
    "CanonicalTimeInterval",
    "ConfidenceOrigin",
    "DuplicateExecutionFactError",
    "ExecutionFact",
    "ExecutionFactBuilder",
    "ExecutionFactCollection",
    "ExecutionFactError",
    "ExecutionNormativeTraceability",
    "ExecutionOccurrence",
    "FactTraceability",
    "InvalidExecutionReferenceError",
    "Measurement",
    "MeasurementValidationState",
    "OverlapStatus",
    "UnknownExecutionRuleError",
]
