"""Compatibilidade imutável entre fatos validados e regras executáveis."""

from __future__ import annotations

from collections.abc import Iterator, Mapping, Sequence
from dataclasses import dataclass
from enum import Enum
import json
from pathlib import Path
from types import MappingProxyType
from typing import Any
from uuid import NAMESPACE_URL, uuid5

from applications.rsc.execution_facts import (
    ExecutionFact,
    ExecutionFactCollection,
)
from applications.rsc.execution_validation import (
    ExecutionValidation,
    ExecutionValidationCollection,
)


class ExecutionCompatibilityError(ValueError):
    """Falha estrutural ao avaliar compatibilidade."""


class CompatibilityState(str, Enum):
    COMPATIBLE = "COMPATIBLE"
    INCOMPATIBLE = "INCOMPATIBLE"


@dataclass(frozen=True, slots=True)
class ExecutionCompatibility:
    compatibility_id: str
    execution_fact_id: str
    validation_id: str
    execution_rule_id: str
    criterion_id: str
    requirement_id: str
    compatibility_state: CompatibilityState
    counting_rule: str
    measurement_type: str
    expected_measurement_type: str
    allowed_measurement_types: tuple[str, ...]
    issues: tuple[str, ...]
    explanation: str
    source_fact: ExecutionFact
    source_validation: ExecutionValidation


@dataclass(frozen=True, slots=True)
class ExecutionCompatibilityCollection:
    compatibilities: tuple[ExecutionCompatibility, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.compatibilities, tuple) or any(
            not isinstance(item, ExecutionCompatibility)
            for item in self.compatibilities
        ):
            raise TypeError(
                "compatibilities deve ser uma tupla de "
                "ExecutionCompatibility."
            )
        fact_ids = tuple(
            item.execution_fact_id for item in self.compatibilities
        )
        validation_ids = tuple(
            item.validation_id for item in self.compatibilities
        )
        if len(fact_ids) != len(set(fact_ids)):
            raise ExecutionCompatibilityError(
                "Existe mais de uma compatibilidade para o mesmo fato."
            )
        if len(validation_ids) != len(set(validation_ids)):
            raise ExecutionCompatibilityError(
                "Existe mais de uma compatibilidade para a mesma validação."
            )

    def __iter__(self) -> Iterator[ExecutionCompatibility]:
        return iter(self.compatibilities)

    def __len__(self) -> int:
        return len(self.compatibilities)


class ExecutionCompatibilityEvaluator:
    """Avalia somente compatibilidade sem revalidar ou calcular."""

    _POLICIES = MappingProxyType({
        "PER_YEAR": ("DURATION",),
        "PER_MONTH": ("DURATION",),
        "PER_EVENT": ("COUNT", "QUANTITY", "HOURS"),
        "PER_PUBLICATION": ("COUNT", "QUANTITY"),
        "CUSTOM_TEXT": ("COUNT", "QUANTITY", "HOURS"),
    })

    def __init__(self, execution_rules: Mapping[str, Any]) -> None:
        if not isinstance(execution_rules, Mapping):
            raise TypeError("execution_rules deve ser um mapeamento.")
        self._rules = self._index(execution_rules)

    @classmethod
    def from_file(
        cls,
        execution_rules_path: str | Path,
    ) -> "ExecutionCompatibilityEvaluator":
        path = Path(execution_rules_path)
        try:
            document = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            raise ExecutionCompatibilityError(
                f"Não foi possível ler {path}: {exc}."
            ) from exc
        if not isinstance(document, dict):
            raise ExecutionCompatibilityError(
                "O catálogo de regras deve ser um objeto JSON."
            )
        return cls(document)

    def evaluate(
        self,
        facts: ExecutionFactCollection,
        validations: ExecutionValidationCollection,
    ) -> ExecutionCompatibilityCollection:
        if not isinstance(facts, ExecutionFactCollection):
            raise TypeError("facts deve ser ExecutionFactCollection.")
        if not isinstance(
            validations,
            ExecutionValidationCollection,
        ):
            raise TypeError(
                "validations deve ser ExecutionValidationCollection."
            )
        by_fact = {
            item.execution_fact_id: item for item in validations
        }
        if len(facts) != len(validations) or {
            item.execution_fact_id for item in facts
        } != set(by_fact):
            raise ExecutionCompatibilityError(
                "Facts e Validations devem possuir correspondência exata."
            )
        return ExecutionCompatibilityCollection(tuple(
            self._evaluate_one(fact, by_fact[fact.execution_fact_id])
            for fact in facts
        ))

    def _evaluate_one(
        self,
        fact: ExecutionFact,
        validation: ExecutionValidation,
    ) -> ExecutionCompatibility:
        rule = self._rules.get(fact.criterion_id)
        if rule is None:
            raise ExecutionCompatibilityError(
                f"Regra ausente para {fact.criterion_id}."
            )
        self._require_links(fact, validation, rule)
        counting_rule = self._counting_rule(rule)
        expected = self._text(rule, "measurement_type")
        observed = fact.measurement.measurement_type
        allowed = self._POLICIES.get(counting_rule, ())
        issues: list[str] = []
        if not allowed:
            issues.append(
                f"Não existe política de compatibilidade para {counting_rule}."
            )
        if observed != expected:
            issues.append(
                f"Measurement {observed} diverge do tipo declarado {expected}."
            )
        if observed not in allowed:
            issues.append(
                f"Measurement {observed} não é aceita por {counting_rule}."
            )
        state = (
            CompatibilityState.COMPATIBLE
            if not issues
            else CompatibilityState.INCOMPATIBLE
        )
        return ExecutionCompatibility(
            compatibility_id=_stable_id(
                fact.execution_fact_id,
                validation.validation_id,
                fact.execution_rule_id,
            ),
            execution_fact_id=fact.execution_fact_id,
            validation_id=validation.validation_id,
            execution_rule_id=fact.execution_rule_id,
            criterion_id=fact.criterion_id,
            requirement_id=fact.requirement_id,
            compatibility_state=state,
            counting_rule=counting_rule,
            measurement_type=observed,
            expected_measurement_type=expected,
            allowed_measurement_types=allowed,
            issues=tuple(issues),
            explanation=(
                f"Regra {counting_rule}; Measurement {observed}; "
                f"esperada {expected}; estado {state.value}; "
                f"{len(issues)} incompatibilidade(s)."
            ),
            source_fact=fact,
            source_validation=validation,
        )

    @staticmethod
    def _require_links(
        fact: ExecutionFact,
        validation: ExecutionValidation,
        rule: Mapping[str, Any],
    ) -> None:
        checks = (
            (fact.execution_fact_id, validation.execution_fact_id),
            (fact.execution_rule_id, validation.execution_rule_id),
            (fact.execution_rule_id, str(rule.get("id"))),
            (fact.criterion_id, validation.criterion_id),
            (fact.criterion_id, str(rule.get("criterion_id"))),
            (fact.requirement_id, str(rule.get("requirement_id"))),
        )
        if any(expected != observed for expected, observed in checks):
            raise ExecutionCompatibilityError(
                "Fato, Validation e regra possuem vínculos divergentes."
            )

    @staticmethod
    def _counting_rule(rule: Mapping[str, Any]) -> str:
        value = rule.get("counting_rule")
        if not isinstance(value, Mapping):
            raise ExecutionCompatibilityError(
                "counting_rule deve ser um objeto."
            )
        return ExecutionCompatibilityEvaluator._text(value, "type")

    @staticmethod
    def _text(values: Mapping[str, Any], field: str) -> str:
        value = values.get(field)
        if not isinstance(value, str) or not value.strip():
            raise ExecutionCompatibilityError(
                f"{field} deve ser textual."
            )
        return value.strip()

    @staticmethod
    def _index(
        document: Mapping[str, Any],
    ) -> Mapping[str, Mapping[str, Any]]:
        raw = document.get("rules")
        if not isinstance(raw, Sequence) or isinstance(raw, (str, bytes)):
            raise ExecutionCompatibilityError(
                "rules deve ser uma coleção."
            )
        result: dict[str, Mapping[str, Any]] = {}
        for item in raw:
            if not isinstance(item, Mapping):
                raise ExecutionCompatibilityError(
                    "rules contém item inválido."
                )
            criterion_id = ExecutionCompatibilityEvaluator._text(
                item,
                "criterion_id",
            )
            if criterion_id in result:
                raise ExecutionCompatibilityError(
                    f"Regra duplicada para {criterion_id}."
                )
            result[criterion_id] = MappingProxyType(dict(item))
        return MappingProxyType(result)


def _stable_id(*identities: str) -> str:
    return str(uuid5(
        NAMESPACE_URL,
        "|".join(("execution-compatibility", *identities)),
    ))


__all__ = [
    "CompatibilityState",
    "ExecutionCompatibility",
    "ExecutionCompatibilityCollection",
    "ExecutionCompatibilityError",
    "ExecutionCompatibilityEvaluator",
]
