"""Núcleo aritmético oficial para contratos de execução preparados."""

from __future__ import annotations

from calendar import monthrange
from collections.abc import Iterator
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from enum import Enum
from uuid import NAMESPACE_URL, uuid5

from applications.rsc.execution_contracts import (
    CriterionExecutionContract,
    CriterionExecutionContractCollection,
    ExecutionComputability,
    NormativeValueTraceability,
)
class ScoringState(str, Enum):
    EXECUTED = "EXECUTED"
    BLOCKED = "BLOCKED"
    NOT_EXECUTED = "NOT_EXECUTED"
    TEXT_DEPENDENT = "TEXT_DEPENDENT"
    HUMAN_REVIEW_REQUIRED = "HUMAN_REVIEW_REQUIRED"


@dataclass(frozen=True, slots=True)
class TemporalDecomposition:
    start: date
    end: date
    complete_years: int
    residual_months: int
    residual_days: int
    fraction_at_least_six_months: bool


@dataclass(frozen=True, slots=True)
class ScoringExecutionTrace:
    contract_id: str
    execution_fact_id: str
    validation_id: str
    measurement_source: str
    normative_value_traceability: NormativeValueTraceability
    formula: str | None


@dataclass(frozen=True, slots=True)
class CriterionScore:
    score_id: str
    contract_id: str
    criterion_id: str
    requirement_id: str
    execution_rule_id: str
    scoring_state: ScoringState
    raw_quantity: int | Decimal | None
    normalized_quantity: Decimal | None
    normative_operand: Decimal | None
    arithmetic_operation: str | None
    calculated_score: Decimal | None
    execution_trace: ScoringExecutionTrace
    explanation: str
    source_contract: CriterionExecutionContract

    def __post_init__(self) -> None:
        if not isinstance(self.scoring_state, ScoringState):
            raise TypeError("scoring_state deve ser ScoringState.")
        for value, name in (
            (self.normalized_quantity, "normalized_quantity"),
            (self.normative_operand, "normative_operand"),
            (self.calculated_score, "calculated_score"),
        ):
            if value is not None and not isinstance(value, Decimal):
                raise TypeError(f"{name} deve ser Decimal ou None.")


@dataclass(frozen=True, slots=True)
class CriterionScoreCollection:
    scores: tuple[CriterionScore, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.scores, tuple) or any(
            not isinstance(item, CriterionScore) for item in self.scores
        ):
            raise TypeError("scores deve ser uma tupla de CriterionScore.")
        score_ids = tuple(item.score_id for item in self.scores)
        contract_ids = tuple(item.contract_id for item in self.scores)
        if len(score_ids) != len(set(score_ids)):
            raise ValueError("Scores possuem identidades duplicadas.")
        if len(contract_ids) != len(set(contract_ids)):
            raise ValueError("Existe mais de um Score por contrato.")

    def __iter__(self) -> Iterator[CriterionScore]:
        return iter(self.scores)

    def __len__(self) -> int:
        return len(self.scores)


class CriterionScoringKernel:
    """Executa apenas multiplicações previamente autorizadas."""

    _SUPPORTED_RULES = frozenset({
        "PER_EVENT",
        "PER_PUBLICATION",
        "PER_YEAR",
    })
    _COMPLETE_YEAR_RULES = frozenset({
        "NONE",
        "FULL_YEARS",
        "COMPLETE_YEARS",
        "WHOLE_YEARS",
    })
    _FRACTION_RULE = "FRACTION_ABOVE_SIX_MONTHS"

    def score(
        self,
        contracts: CriterionExecutionContractCollection,
    ) -> CriterionScoreCollection:
        if not isinstance(contracts, CriterionExecutionContractCollection):
            raise TypeError(
                "contracts deve ser CriterionExecutionContractCollection."
            )
        return CriterionScoreCollection(
            tuple(self._score_one(contract) for contract in contracts)
        )

    def _score_one(
        self,
        contract: CriterionExecutionContract,
    ) -> CriterionScore:
        raw_quantity = contract.measurement.amount
        temporal_details = ""
        temporal_block: str | None = None
        if contract.counting_rule.rule_type == "PER_YEAR":
            quantity, temporal_details, temporal_block = (
                self._complete_year_quantity(contract)
            )
        else:
            quantity = raw_quantity
        operand = contract.resolved_normative_value.value
        normalized = _normalize_quantity(quantity)
        state, reason = self._execution_state(
            contract,
            normalized,
            operand,
            temporal_block,
        )
        executed = state is ScoringState.EXECUTED
        result = normalized * operand if executed else None
        operation = "MULTIPLY" if executed else None
        formula = (
            f"{normalized} × {operand} = {result}" if executed else None
        )
        explanation = (
            f"Contrato {contract.contract_id}; regra "
            f"{contract.counting_rule.rule_type}; quantidade "
            f"{normalized if normalized is not None else 'ausente'}; "
            f"operando {operand if operand is not None else 'ausente'}; "
            f"{temporal_details}"
            f"{formula if formula is not None else reason}."
        )
        return CriterionScore(
            score_id=_stable_score_id(contract.contract_id),
            contract_id=contract.contract_id,
            criterion_id=contract.criterion_id,
            requirement_id=contract.requirement_id,
            execution_rule_id=contract.execution_rule_id,
            scoring_state=state,
            raw_quantity=raw_quantity,
            normalized_quantity=normalized,
            normative_operand=operand,
            arithmetic_operation=operation,
            calculated_score=result,
            execution_trace=ScoringExecutionTrace(
                contract_id=contract.contract_id,
                execution_fact_id=contract.execution_fact_id,
                validation_id=contract.validation_id,
                measurement_source=contract.measurement.source,
                normative_value_traceability=(
                    contract.resolved_normative_value.traceability
                ),
                formula=formula,
            ),
            explanation=explanation,
            source_contract=contract,
        )

    def _execution_state(
        self,
        contract: CriterionExecutionContract,
        quantity: Decimal | None,
        operand: Decimal | None,
        temporal_block: str | None,
    ) -> tuple[ScoringState, str]:
        if (
            contract.counting_rule.rule_type == "PER_YEAR"
            and contract.validation_state.value
            in {
                ScoringState.TEXT_DEPENDENT.value,
                ScoringState.HUMAN_REVIEW_REQUIRED.value,
            }
        ):
            return (
                ScoringState(contract.validation_state.value),
                "estado anterior preservado",
            )
        if (
            contract.execution_computability
            is not ExecutionComputability.EXECUTABLE
        ):
            return (
                ScoringState.BLOCKED,
                "contrato bloqueado: computabilidade de execução não é "
                "EXECUTABLE",
            )
        if temporal_block is not None:
            return ScoringState.BLOCKED, temporal_block
        if contract.counting_rule.rule_type not in self._SUPPORTED_RULES:
            return ScoringState.NOT_EXECUTED, "regra não suportada"
        if quantity is None:
            return ScoringState.NOT_EXECUTED, "quantidade ausente"
        if operand is None:
            return ScoringState.NOT_EXECUTED, "valor normativo ausente"
        return ScoringState.EXECUTED, "execução concluída"

    def _complete_year_quantity(
        self,
        contract: CriterionExecutionContract,
    ) -> tuple[Decimal | None, str, str | None]:
        if (
            contract.temporal_rule not in self._COMPLETE_YEAR_RULES
            and contract.temporal_rule != self._FRACTION_RULE
        ):
            return (
                None,
                f"regra temporal {contract.temporal_rule}; ",
                "regra exige fração ou tratamento temporal não suportado",
            )
        if len(contract.occurrences) != 1:
            return (
                None,
                f"ocorrências {len(contract.occurrences)}; ",
                "período único e fechado não foi determinado",
            )
        occurrence = contract.occurrences[0]
        if occurrence.overlap_status.value != "NONE":
            return (
                None,
                f"sobreposição {occurrence.overlap_status.value}; ",
                "interseção ou sobreposição impede o cálculo",
            )
        start_text = occurrence.period.start
        end_text = occurrence.period.end
        details = (
            f"início {start_text or 'ausente'}; "
            f"fim {end_text or 'ausente'}; "
        )
        if start_text is None or end_text is None:
            return None, details, "período aberto ou data ausente"
        try:
            start = date.fromisoformat(start_text)
            end = date.fromisoformat(end_text)
        except ValueError:
            return None, details, "data inicial ou final inválida"
        if end < start:
            return None, details, "datas invertidas"
        decomposition = decompose_temporal_period(start, end)
        rounded = False
        if contract.temporal_rule == self._FRACTION_RULE:
            rounded = decomposition.fraction_at_least_six_months
        applied_years = decomposition.complete_years + (1 if rounded else 0)
        quantity = Decimal(applied_years)
        fraction = (
            "igual ou superior a seis meses"
            if decomposition.fraction_at_least_six_months
            else "inferior a seis meses"
        )
        fraction_reason = (
            "fração acrescentou um ano"
            if rounded
            else "fração não alterou os anos"
        )
        return (
            quantity,
            (
                f"{details}anos completos {decomposition.complete_years}; "
                f"meses residuais {decomposition.residual_months}; "
                f"dias residuais {decomposition.residual_days}; "
                f"fração {fraction}; {fraction_reason}; "
                f"anos considerados {quantity}; "
            ),
            None,
        )


def _normalize_quantity(value: object) -> Decimal | None:
    if value is None:
        return None
    if isinstance(value, bool):
        raise TypeError("quantidade booleana não é válida.")
    if isinstance(value, Decimal):
        return value
    if isinstance(value, int):
        return Decimal(value)
    raise TypeError("quantidade deve ser int, Decimal ou None.")


def _complete_years(start: date, end: date) -> tuple[int, date]:
    years = end.year - start.year
    anniversary = _anniversary(start, end.year)
    if end < anniversary:
        years -= 1
    return years, _anniversary(start, start.year + years)


def decompose_temporal_period(
    start: date,
    end: date,
) -> TemporalDecomposition:
    years, residual_start = _complete_years(start, end)
    residual_months, residual_days = _calendar_residual(
        residual_start,
        end,
    )
    six_month_boundary = _add_months(residual_start, 6)
    return TemporalDecomposition(
        start=start,
        end=end,
        complete_years=years,
        residual_months=residual_months,
        residual_days=residual_days,
        fraction_at_least_six_months=end >= six_month_boundary,
    )


def _anniversary(start: date, year: int) -> date:
    try:
        return start.replace(year=year)
    except ValueError:
        return date(year, 2, 28)


def _calendar_residual(start: date, end: date) -> tuple[int, int]:
    months = (end.year - start.year) * 12 + end.month - start.month
    if _add_months(start, months) > end:
        months -= 1
    residual_start = _add_months(start, months)
    return months, (end - residual_start).days


def _add_months(value: date, months: int) -> date:
    month_index = value.month - 1 + months
    year = value.year + month_index // 12
    month = month_index % 12 + 1
    day = min(value.day, monthrange(year, month)[1])
    return date(year, month, day)


def _stable_score_id(contract_id: str) -> str:
    return str(uuid5(
        NAMESPACE_URL,
        f"criterion-score|{contract_id}",
    ))


__all__ = [
    "CriterionScore",
    "CriterionScoreCollection",
    "CriterionScoringKernel",
    "ScoringExecutionTrace",
    "ScoringState",
    "TemporalDecomposition",
    "decompose_temporal_period",
]
