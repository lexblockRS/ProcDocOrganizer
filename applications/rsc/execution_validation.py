"""Validação estrutural de fatos preparados para execução normativa."""

from __future__ import annotations

from collections.abc import Iterator, Mapping, Sequence
from dataclasses import dataclass
from datetime import date
from enum import Enum
import json
from pathlib import Path
from types import MappingProxyType
from typing import Any
from uuid import NAMESPACE_URL, uuid5

from applications.rsc.execution_facts import (
    CanonicalFact,
    CanonicalFactType,
    ExecutionFact,
    ExecutionFactCollection,
    MeasurementValidationState,
    OverlapStatus,
)


class ExecutionValidationError(ValueError):
    """Falha estrutural ao validar um contrato de execução."""


class ValidationState(str, Enum):
    READY = "READY"
    READY_WITH_WARNINGS = "READY_WITH_WARNINGS"
    BLOCKED = "BLOCKED"
    HUMAN_REVIEW_REQUIRED = "HUMAN_REVIEW_REQUIRED"
    TEXT_DEPENDENT = "TEXT_DEPENDENT"


@dataclass(frozen=True, slots=True)
class MissingFact:
    fact_name: str
    execution_rule_id: str
    reason: str


@dataclass(frozen=True, slots=True)
class MissingDocument:
    document_id: str
    reason: str


@dataclass(frozen=True, slots=True)
class MissingVariant:
    variant_rule: str
    possible_variants: tuple[str, ...]
    reason: str


@dataclass(frozen=True, slots=True)
class MissingMeasurement:
    measurement_type: str
    unit: str
    reason: str


@dataclass(frozen=True, slots=True)
class InconsistentFact:
    field: str
    expected: str
    observed: str
    reason: str


@dataclass(frozen=True, slots=True)
class ExecutionValidationTraceability:
    execution_fact_id: str
    execution_rule_id: str
    criterion_id: str
    requirement_id: str
    manifest_rule_id: str
    normative_document_id: str
    factual_document_id: str
    source_assessment_criterion_id: str


@dataclass(frozen=True, slots=True)
class ExecutionValidation:
    validation_id: str
    execution_fact_id: str
    criterion_id: str
    execution_rule_id: str
    validation_state: ValidationState
    missing_facts: tuple[MissingFact, ...]
    inconsistent_facts: tuple[InconsistentFact, ...]
    missing_documents: tuple[MissingDocument, ...]
    unresolved_variants: tuple[MissingVariant, ...]
    missing_measurements: tuple[MissingMeasurement, ...]
    overlap_status: OverlapStatus
    computability_level: str
    blocking_issues: tuple[str, ...]
    warnings: tuple[str, ...]
    traceability: ExecutionValidationTraceability
    explanation: str

    def __post_init__(self) -> None:
        for field_name in (
            "validation_id",
            "execution_fact_id",
            "criterion_id",
            "execution_rule_id",
            "computability_level",
            "explanation",
        ):
            _require_text(getattr(self, field_name), field_name)
        if not isinstance(self.validation_state, ValidationState):
            raise TypeError("validation_state deve ser ValidationState.")
        _require_tuple(self.missing_facts, MissingFact, "missing_facts")
        _require_tuple(
            self.inconsistent_facts,
            InconsistentFact,
            "inconsistent_facts",
        )
        _require_tuple(
            self.missing_documents,
            MissingDocument,
            "missing_documents",
        )
        _require_tuple(
            self.unresolved_variants,
            MissingVariant,
            "unresolved_variants",
        )
        _require_tuple(
            self.missing_measurements,
            MissingMeasurement,
            "missing_measurements",
        )
        if not isinstance(self.overlap_status, OverlapStatus):
            raise TypeError("overlap_status deve ser OverlapStatus.")
        _require_text_tuple(self.blocking_issues, "blocking_issues")
        _require_text_tuple(self.warnings, "warnings")
        if not isinstance(
            self.traceability,
            ExecutionValidationTraceability,
        ):
            raise TypeError(
                "traceability deve ser ExecutionValidationTraceability."
            )


@dataclass(frozen=True, slots=True)
class ExecutionValidationCollection:
    validations: tuple[ExecutionValidation, ...] = ()

    def __post_init__(self) -> None:
        _require_tuple(
            self.validations,
            ExecutionValidation,
            "validations",
        )
        validation_ids = tuple(
            item.validation_id for item in self.validations
        )
        fact_ids = tuple(
            item.execution_fact_id for item in self.validations
        )
        if len(validation_ids) != len(set(validation_ids)):
            raise ExecutionValidationError(
                "ValidationCollection contém identidades duplicadas."
            )
        if len(fact_ids) != len(set(fact_ids)):
            raise ExecutionValidationError(
                "Cada ExecutionFact deve possuir uma única Validation."
            )

    def __iter__(self) -> Iterator[ExecutionValidation]:
        return iter(self.validations)

    def __len__(self) -> int:
        return len(self.validations)


class ExecutionValidator:
    """Valida contratos factuais sem completá-los ou executar a norma."""

    def __init__(
        self,
        execution_rules: Mapping[str, Any],
        execution_manifest: Mapping[str, Any],
    ) -> None:
        if not isinstance(execution_rules, Mapping):
            raise TypeError("execution_rules deve ser um mapeamento.")
        if not isinstance(execution_manifest, Mapping):
            raise TypeError("execution_manifest deve ser um mapeamento.")
        self._rules = self._index(
            execution_rules,
            "rules",
            "criterion_id",
        )
        self._manifest = self._index(
            execution_manifest,
            "entries",
            "criterion_id",
        )
        self._validate_catalogs()

    @classmethod
    def from_files(
        cls,
        execution_rules_path: str | Path,
        execution_manifest_path: str | Path,
    ) -> "ExecutionValidator":
        return cls(
            _read_json_object(execution_rules_path),
            _read_json_object(execution_manifest_path),
        )

    def validate(
        self,
        facts: ExecutionFactCollection,
    ) -> ExecutionValidationCollection:
        if not isinstance(facts, ExecutionFactCollection):
            raise TypeError("facts deve ser ExecutionFactCollection.")
        return ExecutionValidationCollection(tuple(
            self._validate_fact(fact) for fact in facts
        ))

    def _validate_fact(
        self,
        fact: ExecutionFact,
    ) -> ExecutionValidation:
        rule = self._rules.get(fact.criterion_id)
        manifest = self._manifest.get(fact.criterion_id)
        inconsistent: list[InconsistentFact] = []
        if rule is None or manifest is None:
            inconsistent.append(InconsistentFact(
                field="criterion_id",
                expected="criterion present in rules and manifest",
                observed=fact.criterion_id,
                reason="Critério sem regra executável ou manifesto.",
            ))
            rule = MappingProxyType({
                "id": fact.execution_rule_id,
                "criterion_id": fact.criterion_id,
                "requirement_id": fact.requirement_id,
                "measurement_unit": fact.measurement.unit,
                "measurement_type": fact.measurement.measurement_type,
                "required_facts": (),
                "temporal_rule": "NONE",
                "variant_rule": {"type": "NONE", "variants": ()},
                "computability_level": fact.computability_level,
            })
            manifest = MappingProxyType({
                "rule_id": "missing",
                "criterion_id": fact.criterion_id,
                "requirement_id": fact.requirement_id,
            })

        inconsistent.extend(self._link_inconsistencies(
            fact,
            rule,
            manifest,
        ))
        missing_facts = self._missing_facts(fact, rule)
        missing_documents, document_inconsistencies = (
            self._documents(fact)
        )
        inconsistent.extend(document_inconsistencies)
        inconsistent.extend(self._unit_inconsistencies(fact, rule))
        inconsistent.extend(self._temporal_inconsistencies(fact, rule))
        inconsistent.extend(self._fact_inconsistencies(fact))
        unresolved_variants = self._variants(fact, rule)
        missing_measurements = self._measurements(fact, rule)
        overlap = self._overlap_status(fact, inconsistent)
        traceability_inconsistencies = self._traceability(fact)
        inconsistent.extend(traceability_inconsistencies)

        blocking = _unique_text((
            *(f"Fato ausente: {item.fact_name}." for item in missing_facts),
            *(
                f"Documento ausente: {item.document_id}."
                for item in missing_documents
            ),
            *(
                f"Medição ausente: {item.measurement_type}."
                for item in missing_measurements
            ),
            *(f"Inconsistência: {item.field}." for item in inconsistent),
        ))
        warnings = _unique_text((
            *fact.unresolved_items,
            *(
                f"Variante pendente: {item.variant_rule}."
                for item in unresolved_variants
            ),
            *(
                ("Sobreposição pendente.",)
                if overlap in {
                    OverlapStatus.POSSIBLE,
                    OverlapStatus.CONFIRMED,
                    OverlapStatus.UNKNOWN,
                }
                else ()
            ),
        ))
        state = self._state(
            fact,
            blocking,
            warnings,
            unresolved_variants,
            overlap,
        )
        traceability = ExecutionValidationTraceability(
            execution_fact_id=fact.execution_fact_id,
            execution_rule_id=fact.execution_rule_id,
            criterion_id=fact.criterion_id,
            requirement_id=fact.requirement_id,
            manifest_rule_id=str(manifest.get("rule_id", "missing")),
            normative_document_id=(
                fact.normative_traceability
                .assessment_origin.document_id
            ),
            factual_document_id=fact.factual_traceability.document_id,
            source_assessment_criterion_id=(
                fact.source_assessment.criterion_id
            ),
        )
        return ExecutionValidation(
            validation_id=_stable_id(
                "execution-validation",
                fact.execution_fact_id,
            ),
            execution_fact_id=fact.execution_fact_id,
            criterion_id=fact.criterion_id,
            execution_rule_id=fact.execution_rule_id,
            validation_state=state,
            missing_facts=missing_facts,
            inconsistent_facts=tuple(inconsistent),
            missing_documents=missing_documents,
            unresolved_variants=unresolved_variants,
            missing_measurements=missing_measurements,
            overlap_status=overlap,
            computability_level=fact.computability_level,
            blocking_issues=blocking,
            warnings=warnings,
            traceability=traceability,
            explanation=self._explanation(
                state,
                missing_facts,
                inconsistent,
                missing_documents,
                unresolved_variants,
                missing_measurements,
                overlap,
            ),
        )

    @staticmethod
    def _link_inconsistencies(
        fact: ExecutionFact,
        rule: Mapping[str, Any],
        manifest: Mapping[str, Any],
    ) -> list[InconsistentFact]:
        checks = (
            ("execution_rule_id", _text(rule, "id"), fact.execution_rule_id),
            (
                "manifest.rule_id",
                _text(rule, "id"),
                str(manifest.get("rule_id")),
            ),
            ("criterion_id", _text(rule, "criterion_id"), fact.criterion_id),
            (
                "requirement_id",
                _text(rule, "requirement_id"),
                fact.requirement_id,
            ),
            (
                "computability_level",
                _text(rule, "computability_level"),
                fact.computability_level,
            ),
        )
        return [
            InconsistentFact(
                field=field,
                expected=expected,
                observed=observed,
                reason="ExecutionFact diverge da regra ou manifesto.",
            )
            for field, expected, observed in checks
            if expected != observed
        ]

    @staticmethod
    def _missing_facts(
        fact: ExecutionFact,
        rule: Mapping[str, Any],
    ) -> tuple[MissingFact, ...]:
        present = {item.fact_type for item in fact.canonical_facts}
        required = _text_sequence(rule, "required_facts")
        result: list[MissingFact] = []
        for name in required:
            fact_type = _FACT_TYPES.get(name)
            if fact_type is None or fact_type not in present:
                result.append(MissingFact(
                    fact_name=name,
                    execution_rule_id=fact.execution_rule_id,
                    reason="Fato exigido pela regra não está disponível.",
                ))
        return tuple(result)

    @staticmethod
    def _documents(
        fact: ExecutionFact,
    ) -> tuple[
        tuple[MissingDocument, ...],
        list[InconsistentFact],
    ]:
        if not fact.canonical_documents:
            return (
                (MissingDocument(
                    document_id=fact.factual_traceability.document_id,
                    reason="ExecutionFact não contém documento canônico.",
                ),),
                [],
            )
        inconsistencies: list[InconsistentFact] = []
        by_id = {
            item.document_id: item for item in fact.canonical_documents
        }
        source = by_id.get(fact.factual_traceability.document_id)
        if source is None:
            return (
                (MissingDocument(
                    document_id=fact.factual_traceability.document_id,
                    reason="Documento da origem factual não foi preservado.",
                ),),
                inconsistencies,
            )
        if (
            source.document_identity.lower()
            != fact.factual_traceability.document_identity.lower()
        ):
            inconsistencies.append(InconsistentFact(
                field="canonical_documents.document_identity",
                expected=fact.factual_traceability.document_identity,
                observed=source.document_identity,
                reason="Documento canônico possui identidade divergente.",
            ))
        for occurrence in fact.quantified_occurrences:
            occurrence_ids = {
                item.document_id for item in occurrence.related_documents
            }
            if source.document_id not in occurrence_ids:
                inconsistencies.append(InconsistentFact(
                    field="occurrence.related_documents",
                    expected=source.document_id,
                    observed=",".join(sorted(occurrence_ids)),
                    reason="Ocorrência não preserva o documento de origem.",
                ))
        return (), inconsistencies

    @staticmethod
    def _unit_inconsistencies(
        fact: ExecutionFact,
        rule: Mapping[str, Any],
    ) -> list[InconsistentFact]:
        expected = _text(rule, "measurement_unit")
        values = [("measurement.unit", fact.measurement.unit)]
        values.extend(
            ("occurrence.unit", item.unit)
            for item in fact.quantified_occurrences
        )
        values.extend(
            ("canonical_fact.unit", item.unit)
            for item in fact.canonical_facts
            if item.fact_type.value.endswith("_count")
            and item.unit is not None
        )
        return [
            InconsistentFact(
                field=field,
                expected=expected,
                observed=str(observed),
                reason="Unidade diverge da regra executável.",
            )
            for field, observed in values
            if observed != expected
        ]

    @staticmethod
    def _temporal_inconsistencies(
        fact: ExecutionFact,
        rule: Mapping[str, Any],
    ) -> list[InconsistentFact]:
        period = fact.canonical_time_interval
        temporal_rule = _text(rule, "temporal_rule")
        result: list[InconsistentFact] = []
        start = _parse_date(period.start, "period.start", result)
        end = _parse_date(period.end, "period.end", result)
        if start is not None and end is not None and end < start:
            result.append(InconsistentFact(
                field="canonical_time_interval",
                expected="end >= start",
                observed=f"{period.start}..{period.end}",
                reason="Período termina antes de começar.",
            ))
        if temporal_rule != "NONE" and period.start is None:
            result.append(InconsistentFact(
                field="canonical_time_interval.start",
                expected="date",
                observed="None",
                reason="Regra temporal exige início do período.",
            ))
        return result

    @staticmethod
    def _fact_inconsistencies(
        fact: ExecutionFact,
    ) -> list[InconsistentFact]:
        result: list[InconsistentFact] = []
        seen_types: set[CanonicalFactType] = set()
        for item in fact.canonical_facts:
            if item.fact_type in seen_types:
                result.append(InconsistentFact(
                    field="canonical_facts.fact_type",
                    expected="unique fact type",
                    observed=item.fact_type.value,
                    reason="Tipo de fato canônico duplicado.",
                ))
            seen_types.add(item.fact_type)
            if not item.traceability.source_identity:
                result.append(InconsistentFact(
                    field=f"fact:{item.fact_id}.traceability",
                    expected="source identity",
                    observed="empty",
                    reason="Fato sem origem rastreável.",
                ))
        return result

    @staticmethod
    def _variants(
        fact: ExecutionFact,
        rule: Mapping[str, Any],
    ) -> tuple[MissingVariant, ...]:
        raw = rule.get("variant_rule")
        if not isinstance(raw, Mapping):
            raise ExecutionValidationError(
                "variant_rule deve ser um objeto."
            )
        variant_type = _text(raw, "type")
        expected = _text_sequence(raw, "variants")
        if variant_type == "NONE":
            return ()
        reasons: list[str] = []
        if fact.possible_variants != expected:
            reasons.append("Opções transportadas divergem da regra.")
        if not fact.variant_fact_available:
            reasons.append("Fato seletor não está disponível.")
        if fact.selected_variant is None:
            reasons.append("Variante permanece deliberadamente não selecionada.")
        if not reasons:
            return ()
        return (MissingVariant(
            variant_rule=variant_type,
            possible_variants=expected,
            reason=" ".join(reasons),
        ),)

    @staticmethod
    def _measurements(
        fact: ExecutionFact,
        rule: Mapping[str, Any],
    ) -> tuple[MissingMeasurement, ...]:
        if measurement_is_computable(fact):
            return ()
        return (MissingMeasurement(
            measurement_type=_text(rule, "measurement_type"),
            unit=_text(rule, "measurement_unit"),
            reason=(
                "Elementos mínimos da medição não estão disponíveis."
            ),
        ),)

    @staticmethod
    def _overlap_status(
        fact: ExecutionFact,
        inconsistent: list[InconsistentFact],
    ) -> OverlapStatus:
        statuses = {
            item.overlap_status for item in fact.quantified_occurrences
        }
        if not statuses:
            return OverlapStatus.UNKNOWN
        if len(statuses) > 1:
            inconsistent.append(InconsistentFact(
                field="occurrences.overlap_status",
                expected="single consistent status",
                observed=",".join(sorted(item.value for item in statuses)),
                reason="Ocorrências possuem estados de sobreposição distintos.",
            ))
            return OverlapStatus.UNKNOWN
        status = next(iter(statuses))
        expects_candidates = status in {
            OverlapStatus.POSSIBLE,
            OverlapStatus.CONFIRMED,
        }
        if (
            status is not OverlapStatus.UNKNOWN
            and bool(fact.overlap_candidates) != expects_candidates
        ):
            inconsistent.append(InconsistentFact(
                field="overlap_candidates",
                expected=(
                    "non-empty for POSSIBLE; empty for NONE"
                ),
                observed=f"{status.value}:{len(fact.overlap_candidates)}",
                reason="Candidatos e estado de sobreposição divergem.",
            ))
        return status

    @staticmethod
    def _traceability(
        fact: ExecutionFact,
    ) -> list[InconsistentFact]:
        normative = fact.normative_traceability
        factual = fact.factual_traceability
        checks = (
            (
                "normative.execution_rule_id",
                fact.execution_rule_id,
                normative.execution_rule_id,
            ),
            (
                "normative.criterion_id",
                fact.criterion_id,
                normative.criterion_id,
            ),
            (
                "normative.requirement_id",
                fact.requirement_id,
                normative.requirement_id,
            ),
            (
                "source_assessment.criterion_id",
                fact.criterion_id,
                fact.source_assessment.criterion_id,
            ),
            (
                "source_assessment.requirement_id",
                fact.requirement_id,
                fact.source_assessment.requirement_id,
            ),
        )
        result = [
            InconsistentFact(
                field=field,
                expected=expected,
                observed=observed,
                reason="Rastreabilidade possui identidade divergente.",
            )
            for field, expected, observed in checks
            if expected != observed
        ]
        for occurrence in fact.quantified_occurrences:
            if occurrence.origin != factual:
                result.append(InconsistentFact(
                    field="occurrence.origin",
                    expected=str(factual),
                    observed=str(occurrence.origin),
                    reason="Ocorrência perdeu a origem factual.",
                ))
            if occurrence.criterion_id != fact.criterion_id:
                result.append(InconsistentFact(
                    field="occurrence.criterion_id",
                    expected=fact.criterion_id,
                    observed=occurrence.criterion_id,
                    reason="Ocorrência pertence a outro critério.",
                ))
        return result

    @staticmethod
    def _state(
        fact: ExecutionFact,
        blocking: tuple[str, ...],
        warnings: tuple[str, ...],
        variants: tuple[MissingVariant, ...],
        overlap: OverlapStatus,
    ) -> ValidationState:
        if blocking:
            return ValidationState.BLOCKED
        if (
            variants
            or overlap in {
                OverlapStatus.POSSIBLE,
                OverlapStatus.CONFIRMED,
                OverlapStatus.UNKNOWN,
            }
            or fact.source_assessment.human_review_required
        ):
            return ValidationState.HUMAN_REVIEW_REQUIRED
        if fact.computability_level == "TEXT_DEPENDENT":
            return ValidationState.TEXT_DEPENDENT
        if warnings:
            return ValidationState.READY_WITH_WARNINGS
        return ValidationState.READY

    @staticmethod
    def _explanation(
        state: ValidationState,
        missing_facts: tuple[MissingFact, ...],
        inconsistent: list[InconsistentFact],
        missing_documents: tuple[MissingDocument, ...],
        variants: tuple[MissingVariant, ...],
        measurements: tuple[MissingMeasurement, ...],
        overlap: OverlapStatus,
    ) -> str:
        return (
            f"Estado {state.value}: {len(missing_facts)} fato(s) ausente(s), "
            f"{len(inconsistent)} inconsistência(s), "
            f"{len(missing_documents)} documento(s) ausente(s), "
            f"{len(measurements)} medição(ões) ausente(s), "
            f"{len(variants)} variante(s) pendente(s), "
            f"sobreposição {overlap.value}. "
            "Nenhum dado foi completado, corrigido, agregado ou pontuado."
        )

    @staticmethod
    def _index(
        document: Mapping[str, Any],
        collection_name: str,
        identity_field: str,
    ) -> Mapping[str, Mapping[str, Any]]:
        raw = document.get(collection_name)
        if not isinstance(raw, Sequence) or isinstance(raw, (str, bytes)):
            raise ExecutionValidationError(
                f"{collection_name} deve ser uma coleção."
            )
        result: dict[str, Mapping[str, Any]] = {}
        for item in raw:
            if not isinstance(item, Mapping):
                raise ExecutionValidationError(
                    f"{collection_name} contém item inválido."
                )
            identity = _text(item, identity_field)
            if identity in result:
                raise ExecutionValidationError(
                    f"{collection_name} possui identidade duplicada: "
                    f"{identity}."
                )
            result[identity] = MappingProxyType(dict(item))
        return MappingProxyType(result)

    def _validate_catalogs(self) -> None:
        if set(self._rules) != set(self._manifest):
            raise ExecutionValidationError(
                "Regras e manifesto possuem coberturas diferentes."
            )
        for criterion_id, rule in self._rules.items():
            manifest = self._manifest[criterion_id]
            if (
                _text(rule, "id") != _text(manifest, "rule_id")
                or _text(rule, "requirement_id")
                != _text(manifest, "requirement_id")
                or _text(rule, "scoring_table")
                != _text(manifest, "table_id")
            ):
                raise ExecutionValidationError(
                    f"Manifesto divergente para {criterion_id}."
                )


_FACT_TYPES = {
    "period_start": CanonicalFactType.PERIOD_START,
    "period_end": CanonicalFactType.PERIOD_END,
    "role": CanonicalFactType.EXECUTION_ROLE,
    **{
        item.value: item
        for item in CanonicalFactType
        if item.value.endswith("_count")
    },
}


def _parse_date(
    value: str | None,
    field: str,
    inconsistencies: list[InconsistentFact],
) -> date | None:
    if value is None:
        return None
    try:
        return date.fromisoformat(value)
    except (TypeError, ValueError):
        inconsistencies.append(InconsistentFact(
            field=field,
            expected="ISO date",
            observed=str(value),
            reason="Data possui formato inválido.",
        ))
        return None


def _stable_id(kind: str, identity: str) -> str:
    return str(uuid5(NAMESPACE_URL, f"{kind}|{identity}"))


def _read_json_object(path: str | Path) -> Mapping[str, Any]:
    resolved = Path(path)
    try:
        value = json.loads(resolved.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ExecutionValidationError(
            f"Não foi possível ler {resolved}: {exc}."
        ) from exc
    if not isinstance(value, dict):
        raise ExecutionValidationError(
            f"{resolved} deve conter um objeto JSON."
        )
    return value


def _text(values: Mapping[str, Any], field: str) -> str:
    value = values.get(field)
    if not isinstance(value, str) or not value.strip():
        raise ExecutionValidationError(f"{field} deve ser textual.")
    return value.strip()


def _text_sequence(
    values: Mapping[str, Any],
    field: str,
) -> tuple[str, ...]:
    raw = values.get(field, ())
    if not isinstance(raw, Sequence) or isinstance(raw, (str, bytes)):
        raise ExecutionValidationError(f"{field} deve ser uma coleção.")
    result = tuple(raw)
    if any(not isinstance(item, str) or not item.strip() for item in result):
        raise ExecutionValidationError(
            f"{field} deve conter somente textos."
        )
    return result


def measurement_is_computable(fact: ExecutionFact) -> bool:
    """Valida os elementos mínimos definidos pelo tipo da medição."""
    measurement = fact.measurement
    if measurement.measurement_type == "DURATION":
        period = fact.canonical_time_interval
        if period.start is None or period.end is None:
            return False
        try:
            start = date.fromisoformat(period.start)
            end = date.fromisoformat(period.end)
        except ValueError:
            return False
        return end >= start
    if measurement.measurement_type in {"QUANTITY", "HOURS", "COUNT"}:
        return (
            measurement.amount is not None
            and measurement.validation_state
            is MeasurementValidationState.AVAILABLE
        )
    return False


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
    "ExecutionValidation",
    "ExecutionValidationCollection",
    "ExecutionValidationError",
    "ExecutionValidationTraceability",
    "ExecutionValidator",
    "InconsistentFact",
    "MissingDocument",
    "MissingFact",
    "MissingMeasurement",
    "MissingVariant",
    "ValidationState",
    "measurement_is_computable",
]
