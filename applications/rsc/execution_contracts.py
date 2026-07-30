"""Montagem imutável do contrato factual, validado e normativo."""

from __future__ import annotations

from collections.abc import Iterator, Mapping, Sequence
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from enum import Enum
import json
from pathlib import Path
from types import MappingProxyType
from typing import Any
from uuid import NAMESPACE_URL, uuid5

from applications.rsc.criterion_candidates import FactualTraceability
from applications.rsc.execution_compatibility import (
    CompatibilityState,
    ExecutionCompatibility,
    ExecutionCompatibilityCollection,
)
from applications.rsc.execution_facts import (
    CanonicalDocument,
    CanonicalFact,
    ExecutionFact,
    ExecutionFactCollection,
    ExecutionNormativeTraceability,
    ExecutionOccurrence,
    Measurement,
)
from applications.rsc.execution_validation import (
    ExecutionValidation,
    ExecutionValidationCollection,
    ExecutionValidationTraceability,
    ValidationState,
    measurement_is_computable,
)


class ExecutionContractResolutionError(ValueError):
    """Falha estrutural ao unir fato, validação e regra."""


class MissingExecutionContractRuleError(ExecutionContractResolutionError):
    """Não existe regra declarativa para o fato informado."""


class InconsistentExecutionContractManifestError(
    ExecutionContractResolutionError
):
    """Regra e manifesto não representam o mesmo contrato."""


class DuplicateExecutionContractError(ExecutionContractResolutionError):
    """Dois contratos possuem a mesma identidade de origem."""


class LegalComputability(str, Enum):
    FULLY_EXECUTABLE = "FULLY_EXECUTABLE"
    PARTIALLY_EXECUTABLE = "PARTIALLY_EXECUTABLE"
    TEXT_DEPENDENT = "TEXT_DEPENDENT"
    HUMAN_ONLY = "HUMAN_ONLY"


class ExecutionComputability(str, Enum):
    EXECUTABLE = "EXECUTABLE"
    NOT_EXECUTABLE = "NOT_EXECUTABLE"
    BLOCKED = "BLOCKED"


@dataclass(frozen=True, slots=True)
class ResolvedCountingRule:
    rule_type: str
    text: str | None
    source: str | None


@dataclass(frozen=True, slots=True)
class ResolvedVariantRule:
    rule_type: str
    variants: tuple[str, ...]
    selector_fact: str | None


@dataclass(frozen=True, slots=True)
class NormativeValueTraceability:
    document_id: str
    source_file: str
    table_id: str
    criterion_id: str
    legal_reference: str
    annex: str
    item: str
    source_field: str
    original_value: str | None
    variant_values: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ResolvedNormativeValue:
    value: Decimal | None
    unit: str
    table_id: str
    criterion_id: str
    legal_basis: str
    traceability: NormativeValueTraceability

    def __post_init__(self) -> None:
        if self.value is not None and not isinstance(self.value, Decimal):
            raise TypeError("value deve ser Decimal ou None.")
        for field_name in (
            "unit",
            "table_id",
            "criterion_id",
            "legal_basis",
        ):
            _require_text(getattr(self, field_name), field_name)
        if not isinstance(
            self.traceability,
            NormativeValueTraceability,
        ):
            raise TypeError(
                "traceability deve ser NormativeValueTraceability."
            )


@dataclass(frozen=True, slots=True)
class CriterionExecutionContract:
    contract_id: str
    execution_fact_id: str
    validation_id: str
    compatibility_id: str
    execution_rule_id: str
    criterion_id: str
    requirement_id: str
    validation_state: ValidationState
    legal_computability: LegalComputability
    execution_computability: ExecutionComputability
    resolved_normative_value: ResolvedNormativeValue
    counting_rule: ResolvedCountingRule
    temporal_rule: str
    measurement: Measurement
    occurrences: tuple[ExecutionOccurrence, ...]
    canonical_facts: tuple[CanonicalFact, ...]
    canonical_documents: tuple[CanonicalDocument, ...]
    accepted_documents: tuple[str, ...]
    required_facts: tuple[str, ...]
    aggregation_rule: str
    overlap_rule: str
    variant_rule: ResolvedVariantRule
    applicable_table: str
    article_reference: str
    annex_reference: str
    unresolved_items: tuple[str, ...]
    normative_traceability: ExecutionNormativeTraceability
    factual_traceability: FactualTraceability
    validation_traceability: ExecutionValidationTraceability
    explanation: str
    source_execution_fact: ExecutionFact
    source_validation: ExecutionValidation
    source_compatibility: ExecutionCompatibility

    def __post_init__(self) -> None:
        for field_name in (
            "contract_id",
            "execution_fact_id",
            "validation_id",
            "compatibility_id",
            "execution_rule_id",
            "criterion_id",
            "requirement_id",
            "temporal_rule",
            "aggregation_rule",
            "overlap_rule",
            "applicable_table",
            "article_reference",
            "annex_reference",
            "explanation",
        ):
            _require_text(getattr(self, field_name), field_name)
        if not isinstance(self.validation_state, ValidationState):
            raise TypeError("validation_state deve ser ValidationState.")
        if not isinstance(self.legal_computability, LegalComputability):
            raise TypeError(
                "legal_computability deve ser LegalComputability."
            )
        if not isinstance(
            self.execution_computability,
            ExecutionComputability,
        ):
            raise TypeError(
                "execution_computability deve ser ExecutionComputability."
            )
        if not isinstance(
            self.resolved_normative_value,
            ResolvedNormativeValue,
        ):
            raise TypeError(
                "resolved_normative_value deve ser "
                "ResolvedNormativeValue."
            )
        if not isinstance(self.counting_rule, ResolvedCountingRule):
            raise TypeError(
                "counting_rule deve ser ResolvedCountingRule."
            )
        if not isinstance(self.variant_rule, ResolvedVariantRule):
            raise TypeError("variant_rule deve ser ResolvedVariantRule.")
        if not isinstance(self.measurement, Measurement):
            raise TypeError("measurement deve ser Measurement.")
        _require_tuple(
            self.occurrences,
            ExecutionOccurrence,
            "occurrences",
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
        _require_text_tuple(
            self.accepted_documents,
            "accepted_documents",
        )
        _require_text_tuple(self.required_facts, "required_facts")
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
        if not isinstance(
            self.validation_traceability,
            ExecutionValidationTraceability,
        ):
            raise TypeError(
                "validation_traceability deve ser "
                "ExecutionValidationTraceability."
            )
        if not isinstance(self.source_execution_fact, ExecutionFact):
            raise TypeError(
                "source_execution_fact deve ser ExecutionFact."
            )
        if not isinstance(self.source_validation, ExecutionValidation):
            raise TypeError(
                "source_validation deve ser ExecutionValidation."
            )
        if not isinstance(
            self.source_compatibility,
            ExecutionCompatibility,
        ):
            raise TypeError(
                "source_compatibility deve ser ExecutionCompatibility."
            )


@dataclass(frozen=True, slots=True)
class CriterionExecutionContractCollection:
    contracts: tuple[CriterionExecutionContract, ...] = ()

    def __post_init__(self) -> None:
        _require_tuple(
            self.contracts,
            CriterionExecutionContract,
            "contracts",
        )
        contract_ids = tuple(item.contract_id for item in self.contracts)
        fact_ids = tuple(
            item.execution_fact_id for item in self.contracts
        )
        validation_ids = tuple(
            item.validation_id for item in self.contracts
        )
        if len(contract_ids) != len(set(contract_ids)):
            raise DuplicateExecutionContractError(
                "Contratos possuem identidades duplicadas."
            )
        if len(fact_ids) != len(set(fact_ids)):
            raise DuplicateExecutionContractError(
                "Existe mais de um contrato para o mesmo ExecutionFact."
            )
        if len(validation_ids) != len(set(validation_ids)):
            raise DuplicateExecutionContractError(
                "Existe mais de um contrato para a mesma Validation."
            )

    def __iter__(self) -> Iterator[CriterionExecutionContract]:
        return iter(self.contracts)

    def __len__(self) -> int:
        return len(self.contracts)


class ExecutionContractResolver:
    """Une contratos somente leitura sem executar ou revalidar regras."""

    def __init__(
        self,
        execution_rules: Mapping[str, Any],
        execution_manifest: Mapping[str, Any],
        decree_criteria: Mapping[str, Any],
    ) -> None:
        if not isinstance(execution_rules, Mapping):
            raise TypeError("execution_rules deve ser um mapeamento.")
        if not isinstance(execution_manifest, Mapping):
            raise TypeError("execution_manifest deve ser um mapeamento.")
        if not isinstance(decree_criteria, Mapping):
            raise TypeError("decree_criteria deve ser um mapeamento.")
        self._rules_document = MappingProxyType(dict(execution_rules))
        self._manifest_document = MappingProxyType(
            dict(execution_manifest)
        )
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
        self._criteria = self._index(
            decree_criteria,
            "criteria",
            "id",
        )
        self._accepted_profiles = self._accepted_document_profiles(
            execution_rules,
            execution_manifest,
        )
        self._validate_catalogs()

    @classmethod
    def from_files(
        cls,
        execution_rules_path: str | Path,
        execution_manifest_path: str | Path,
        decree_criteria_path: str | Path,
    ) -> "ExecutionContractResolver":
        return cls(
            _read_json_object(execution_rules_path),
            _read_json_object(execution_manifest_path),
            _read_json_object(decree_criteria_path),
        )

    def resolve(
        self,
        facts: ExecutionFactCollection,
        validations: ExecutionValidationCollection,
        compatibilities: ExecutionCompatibilityCollection,
    ) -> CriterionExecutionContractCollection:
        if not isinstance(facts, ExecutionFactCollection):
            raise TypeError("facts deve ser ExecutionFactCollection.")
        if not isinstance(
            validations,
            ExecutionValidationCollection,
        ):
            raise TypeError(
                "validations deve ser ExecutionValidationCollection."
            )
        if not isinstance(
            compatibilities,
            ExecutionCompatibilityCollection,
        ):
            raise TypeError(
                "compatibilities deve ser "
                "ExecutionCompatibilityCollection."
            )
        validation_index = {
            item.execution_fact_id: item for item in validations
        }
        compatibility_index = {
            item.execution_fact_id: item for item in compatibilities
        }
        fact_ids = tuple(item.execution_fact_id for item in facts)
        if (
            len(fact_ids) != len(validation_index)
            or set(fact_ids) != set(validation_index)
            or len(fact_ids) != len(compatibility_index)
            or set(fact_ids) != set(compatibility_index)
        ):
            raise ExecutionContractResolutionError(
                "Facts, Validations e Compatibilities devem possuir "
                "correspondência exata."
            )
        contracts = tuple(
            self._resolve_one(
                fact,
                validation_index[fact.execution_fact_id],
                compatibility_index[fact.execution_fact_id],
            )
            for fact in facts
        )
        return CriterionExecutionContractCollection(contracts)

    def _resolve_one(
        self,
        fact: ExecutionFact,
        validation: ExecutionValidation,
        compatibility: ExecutionCompatibility,
    ) -> CriterionExecutionContract:
        rule = self._rules.get(fact.criterion_id)
        manifest = self._manifest.get(fact.criterion_id)
        if rule is None:
            raise MissingExecutionContractRuleError(
                f"Regra ausente para {fact.criterion_id}."
            )
        if manifest is None:
            raise InconsistentExecutionContractManifestError(
                f"Manifesto ausente para {fact.criterion_id}."
            )
        self._require_links(
            fact,
            validation,
            compatibility,
            rule,
            manifest,
        )
        criterion = self._criteria.get(fact.criterion_id)
        if criterion is None:
            raise MissingExecutionContractRuleError(
                f"Critério normativo ausente: {fact.criterion_id}."
            )
        normative_value = self._normative_value(
            fact,
            rule,
            criterion,
        )

        accepted_profile = _text(rule, "accepted_documents")
        accepted_documents = self._accepted_profiles.get(
            accepted_profile
        )
        if accepted_documents is None:
            raise InconsistentExecutionContractManifestError(
                f"Perfil documental ausente: {accepted_profile}."
            )
        counting = self._counting_rule(rule)
        variant = self._variant_rule(rule)
        required_facts = _text_sequence(rule, "required_facts")
        unresolved = self._unresolved(
            fact,
            validation,
            compatibility,
        )
        table = _text(rule, "scoring_table")
        legal_computability = self._legal_computability(rule)
        execution_computability = self._execution_computability(
            fact,
            validation,
            compatibility,
            normative_value,
        )
        return CriterionExecutionContract(
            contract_id=_stable_id(
                "criterion-execution-contract",
                fact.execution_fact_id,
                validation.validation_id,
                fact.execution_rule_id,
            ),
            execution_fact_id=fact.execution_fact_id,
            validation_id=validation.validation_id,
            compatibility_id=compatibility.compatibility_id,
            execution_rule_id=fact.execution_rule_id,
            criterion_id=fact.criterion_id,
            requirement_id=fact.requirement_id,
            validation_state=validation.validation_state,
            legal_computability=legal_computability,
            execution_computability=execution_computability,
            resolved_normative_value=normative_value,
            counting_rule=counting,
            temporal_rule=_text(rule, "temporal_rule"),
            measurement=fact.measurement,
            occurrences=fact.quantified_occurrences,
            canonical_facts=fact.canonical_facts,
            canonical_documents=fact.canonical_documents,
            accepted_documents=accepted_documents,
            required_facts=required_facts,
            aggregation_rule=_text(rule, "aggregation_rule"),
            overlap_rule=_text(rule, "overlap_rule"),
            variant_rule=variant,
            applicable_table=table,
            article_reference=_text(rule, "article_reference"),
            annex_reference=_text(rule, "annex_reference"),
            unresolved_items=unresolved,
            normative_traceability=fact.normative_traceability,
            factual_traceability=fact.factual_traceability,
            validation_traceability=validation.traceability,
            explanation=self._explanation(
                fact,
                validation,
                rule,
                required_facts,
                unresolved,
                table,
                legal_computability,
                execution_computability,
                normative_value,
            ),
            source_execution_fact=fact,
            source_validation=validation,
            source_compatibility=compatibility,
        )

    @staticmethod
    def _require_links(
        fact: ExecutionFact,
        validation: ExecutionValidation,
        compatibility: ExecutionCompatibility,
        rule: Mapping[str, Any],
        manifest: Mapping[str, Any],
    ) -> None:
        expected = (
            ("validation.execution_fact_id", fact.execution_fact_id,
             validation.execution_fact_id),
            ("validation.execution_rule_id", fact.execution_rule_id,
             validation.execution_rule_id),
            ("validation.criterion_id", fact.criterion_id,
             validation.criterion_id),
            ("compatibility.execution_fact_id", fact.execution_fact_id,
             compatibility.execution_fact_id),
            ("compatibility.validation_id", validation.validation_id,
             compatibility.validation_id),
            ("compatibility.execution_rule_id", fact.execution_rule_id,
             compatibility.execution_rule_id),
            ("rule.id", fact.execution_rule_id, _text(rule, "id")),
            ("rule.criterion_id", fact.criterion_id,
             _text(rule, "criterion_id")),
            ("rule.requirement_id", fact.requirement_id,
             _text(rule, "requirement_id")),
            ("manifest.rule_id", fact.execution_rule_id,
             _text(manifest, "rule_id")),
            ("manifest.criterion_id", fact.criterion_id,
             _text(manifest, "criterion_id")),
            ("manifest.requirement_id", fact.requirement_id,
             _text(manifest, "requirement_id")),
            ("manifest.table_id", _text(rule, "scoring_table"),
             _text(manifest, "table_id")),
        )
        divergences = tuple(
            name for name, wanted, observed in expected
            if wanted != observed
        )
        if divergences:
            raise InconsistentExecutionContractManifestError(
                "Vínculos divergentes: " + ", ".join(divergences) + "."
            )

    @staticmethod
    def _counting_rule(
        rule: Mapping[str, Any],
    ) -> ResolvedCountingRule:
        raw = rule.get("counting_rule")
        if not isinstance(raw, Mapping):
            raise ExecutionContractResolutionError(
                "counting_rule deve ser um objeto."
            )
        return ResolvedCountingRule(
            rule_type=_text(raw, "type"),
            text=_optional_text(raw, "text"),
            source=_optional_text(raw, "source"),
        )

    @staticmethod
    def _variant_rule(
        rule: Mapping[str, Any],
    ) -> ResolvedVariantRule:
        raw = rule.get("variant_rule")
        if not isinstance(raw, Mapping):
            raise ExecutionContractResolutionError(
                "variant_rule deve ser um objeto."
            )
        return ResolvedVariantRule(
            rule_type=_text(raw, "type"),
            variants=_text_sequence(raw, "variants"),
            selector_fact=_optional_text(raw, "selector_fact"),
        )

    @staticmethod
    def _normative_value(
        fact: ExecutionFact,
        rule: Mapping[str, Any],
        criterion: Mapping[str, Any],
    ) -> ResolvedNormativeValue:
        table_id = _text(rule, "scoring_table")
        criterion_table = _text(criterion, "table")
        expected_table_name = table_id.removeprefix(
            "DEC13048-TABLE-"
        )
        if criterion_table != expected_table_name:
            raise InconsistentExecutionContractManifestError(
                f"Tabela ausente ou divergente para {fact.criterion_id}."
            )
        if _text(criterion, "id") != fact.criterion_id:
            raise InconsistentExecutionContractManifestError(
                "Critério normativo divergente."
            )
        raw_value = criterion.get("points")
        value = _decimal_value(raw_value, fact.criterion_id)
        variants_raw = criterion.get("variants")
        variant_values: tuple[str, ...] = ()
        if variants_raw is not None:
            if not isinstance(variants_raw, Sequence) or isinstance(
                variants_raw,
                (str, bytes),
            ):
                raise ExecutionContractResolutionError(
                    "variants normativas deve ser uma coleção."
                )
            variant_values = tuple(
                _text(item, "points")
                for item in variants_raw
                if isinstance(item, Mapping)
            )
            if len(variant_values) != len(variants_raw):
                raise ExecutionContractResolutionError(
                    "variants normativas contém item inválido."
                )
        return ResolvedNormativeValue(
            value=value,
            unit=_text(criterion, "unit"),
            table_id=table_id,
            criterion_id=fact.criterion_id,
            legal_basis=_text(criterion, "legal_reference"),
            traceability=NormativeValueTraceability(
                document_id=_text(criterion, "document_id"),
                source_file="decree_criteria.json",
                table_id=table_id,
                criterion_id=fact.criterion_id,
                legal_reference=_text(criterion, "legal_reference"),
                annex=_text(criterion, "annex"),
                item=_text(criterion, "item"),
                source_field=(
                    "points" if raw_value is not None else "variants"
                ),
                original_value=(
                    raw_value if isinstance(raw_value, str) else None
                ),
                variant_values=variant_values,
            ),
        )

    @staticmethod
    def _legal_computability(
        rule: Mapping[str, Any],
    ) -> LegalComputability:
        try:
            return LegalComputability(_text(rule, "computability_level"))
        except ValueError as exc:
            raise ExecutionContractResolutionError(
                "computability_level normativo desconhecido."
            ) from exc

    @staticmethod
    def _execution_computability(
        fact: ExecutionFact,
        validation: ExecutionValidation,
        compatibility: ExecutionCompatibility,
        normative_value: ResolvedNormativeValue,
    ) -> ExecutionComputability:
        if (
            validation.validation_state is ValidationState.BLOCKED
            or compatibility.compatibility_state
            is CompatibilityState.INCOMPATIBLE
        ):
            return ExecutionComputability.BLOCKED
        if (
            validation.validation_state
            is ValidationState.HUMAN_REVIEW_REQUIRED
            or normative_value.value is None
            or not measurement_is_computable(fact)
        ):
            return ExecutionComputability.NOT_EXECUTABLE
        return ExecutionComputability.EXECUTABLE

    @staticmethod
    def _unresolved(
        fact: ExecutionFact,
        validation: ExecutionValidation,
        compatibility: ExecutionCompatibility,
    ) -> tuple[str, ...]:
        return _unique_text((
            *fact.unresolved_items,
            *validation.blocking_issues,
            *validation.warnings,
            *(
                f"incompatible_measurement:{issue}"
                for issue in compatibility.issues
            ),
            *(
                f"missing_fact:{item.fact_name}"
                for item in validation.missing_facts
            ),
            *(
                f"missing_document:{item.document_id}"
                for item in validation.missing_documents
            ),
            *(
                f"missing_measurement:{item.measurement_type}"
                for item in validation.missing_measurements
            ),
            *(
                f"unresolved_variant:{item.variant_rule}"
                for item in validation.unresolved_variants
            ),
            *(
                f"inconsistent:{item.field}"
                for item in validation.inconsistent_facts
            ),
        ))

    @staticmethod
    def _explanation(
        fact: ExecutionFact,
        validation: ExecutionValidation,
        rule: Mapping[str, Any],
        required_facts: tuple[str, ...],
        unresolved: tuple[str, ...],
        table: str,
        legal_computability: LegalComputability,
        execution_computability: ExecutionComputability,
        normative_value: ResolvedNormativeValue,
    ) -> str:
        textual = (
            " A regra permanece dependente de texto."
            if fact.computability_level == "TEXT_DEPENDENT"
            else ""
        )
        review = (
            " Revisão humana permanece necessária."
            if validation.validation_state
            is ValidationState.HUMAN_REVIEW_REQUIRED
            else ""
        )
        blocked = (
            " Campos pendentes impedem futura aplicação."
            if validation.validation_state is ValidationState.BLOCKED
            else ""
        )
        return (
            f"ExecutionFact {fact.execution_fact_id}; Validation "
            f"{validation.validation_id} ({validation.validation_state.value}); "
            f"regra {_text(rule, 'id')}; tabela {table}; "
            f"valor normativo "
            f"{normative_value.value if normative_value.value is not None else 'não singular'}; "
            f"computabilidade legal {legal_computability.value}; "
            f"computabilidade de execução {execution_computability.value}; "
            f"{len(required_facts)} fato(s) requerido(s); "
            f"{len(unresolved)} item(ns) não resolvido(s)."
            f"{textual}{review}{blocked} Nenhuma pontuação foi calculada."
        )

    @staticmethod
    def _index(
        document: Mapping[str, Any],
        collection_name: str,
        identity_field: str,
    ) -> Mapping[str, Mapping[str, Any]]:
        raw = document.get(collection_name)
        if not isinstance(raw, Sequence) or isinstance(raw, (str, bytes)):
            raise ExecutionContractResolutionError(
                f"{collection_name} deve ser uma coleção."
            )
        result: dict[str, Mapping[str, Any]] = {}
        for item in raw:
            if not isinstance(item, Mapping):
                raise ExecutionContractResolutionError(
                    f"{collection_name} contém item inválido."
                )
            identity = _text(item, identity_field)
            if identity in result:
                raise DuplicateExecutionContractError(
                    f"{collection_name} possui duplicidade: {identity}."
                )
            result[identity] = MappingProxyType(dict(item))
        return MappingProxyType(result)

    @staticmethod
    def _accepted_document_profiles(
        rules: Mapping[str, Any],
        manifest: Mapping[str, Any],
    ) -> Mapping[str, tuple[str, ...]]:
        shared = rules.get("shared_rules")
        if not isinstance(shared, Mapping):
            raise ExecutionContractResolutionError(
                "shared_rules deve ser um objeto."
            )
        documents = shared.get("accepted_documents")
        if not isinstance(documents, Mapping):
            raise ExecutionContractResolutionError(
                "accepted_documents deve ser um objeto."
            )
        profile_id = _text(documents, "profile_id")
        document_ids = _text_sequence(documents, "document_type_ids")
        manifest_profile = manifest.get("accepted_documents_profile")
        if not isinstance(manifest_profile, Mapping):
            raise InconsistentExecutionContractManifestError(
                "Manifesto não contém perfil documental."
            )
        if (
            _text(manifest_profile, "id") != profile_id
            or _text_sequence(manifest_profile, "document_type_ids")
            != document_ids
        ):
            raise InconsistentExecutionContractManifestError(
                "Perfis documentais de regra e manifesto divergem."
            )
        return MappingProxyType({profile_id: document_ids})

    def _validate_catalogs(self) -> None:
        if set(self._rules) != set(self._manifest):
            raise InconsistentExecutionContractManifestError(
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
                raise InconsistentExecutionContractManifestError(
                    f"Manifesto divergente para {criterion_id}."
                )
            if criterion_id not in self._criteria:
                raise InconsistentExecutionContractManifestError(
                    f"Critério ausente em decree_criteria: {criterion_id}."
                )


def _stable_id(kind: str, *identities: str) -> str:
    return str(uuid5(
        NAMESPACE_URL,
        "|".join((kind, *identities)),
    ))


def _decimal_value(
    raw_value: object,
    criterion_id: str,
) -> Decimal | None:
    if raw_value is None:
        return None
    if not isinstance(raw_value, str) or not raw_value.strip():
        raise ExecutionContractResolutionError(
            f"Valor normativo ausente para {criterion_id}."
        )
    try:
        return Decimal(raw_value.strip().replace(",", "."))
    except InvalidOperation as exc:
        raise ExecutionContractResolutionError(
            f"Valor normativo inválido para {criterion_id}."
        ) from exc


def _read_json_object(path: str | Path) -> Mapping[str, Any]:
    resolved = Path(path)
    try:
        value = json.loads(resolved.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ExecutionContractResolutionError(
            f"Não foi possível ler {resolved}: {exc}."
        ) from exc
    if not isinstance(value, dict):
        raise ExecutionContractResolutionError(
            f"{resolved} deve conter um objeto JSON."
        )
    return value


def _text(values: Mapping[str, Any], field: str) -> str:
    value = values.get(field)
    if not isinstance(value, str) or not value.strip():
        raise ExecutionContractResolutionError(
            f"{field} deve ser textual."
        )
    return value.strip()


def _optional_text(
    values: Mapping[str, Any],
    field: str,
) -> str | None:
    value = values.get(field)
    if value is None:
        return None
    if not isinstance(value, str) or not value.strip():
        raise ExecutionContractResolutionError(
            f"{field} deve ser textual ou None."
        )
    return value.strip()


def _text_sequence(
    values: Mapping[str, Any],
    field: str,
) -> tuple[str, ...]:
    raw = values.get(field, ())
    if not isinstance(raw, Sequence) or isinstance(raw, (str, bytes)):
        raise ExecutionContractResolutionError(
            f"{field} deve ser uma coleção."
        )
    result = tuple(raw)
    if any(not isinstance(item, str) or not item.strip() for item in result):
        raise ExecutionContractResolutionError(
            f"{field} deve conter somente textos."
        )
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
    "CriterionExecutionContract",
    "CriterionExecutionContractCollection",
    "DuplicateExecutionContractError",
    "ExecutionComputability",
    "ExecutionContractResolutionError",
    "ExecutionContractResolver",
    "InconsistentExecutionContractManifestError",
    "LegalComputability",
    "MissingExecutionContractRuleError",
    "NormativeValueTraceability",
    "ResolvedCountingRule",
    "ResolvedNormativeValue",
    "ResolvedVariantRule",
]
