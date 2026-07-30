"""Alertas temporais informativos, sem efeito normativo."""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass
from datetime import date
from enum import Enum

from applications.rsc.scoring_kernel import (
    CriterionScore,
    CriterionScoreCollection,
    decompose_temporal_period,
)


class TemporalAttentionSeverity(str, Enum):
    INFO = "INFO"
    WARNING = "WARNING"


class TemporalAttentionCode(str, Enum):
    EXACT_SIX_MONTH_LIMIT = "EXACT_SIX_MONTH_LIMIT"
    JUST_BELOW_SIX_MONTH_LIMIT = "JUST_BELOW_SIX_MONTH_LIMIT"
    JUST_ABOVE_SIX_MONTH_LIMIT = "JUST_ABOVE_SIX_MONTH_LIMIT"
    LEAP_DAY_INVOLVED = "LEAP_DAY_INVOLVED"
    EXACT_TEMPORAL_LANDMARK = "EXACT_TEMPORAL_LANDMARK"


@dataclass(frozen=True, slots=True)
class TemporalAttention:
    code: TemporalAttentionCode
    severity: TemporalAttentionSeverity
    message: str
    explanation: str
    score_id: str
    contract_id: str
    criterion_id: str


@dataclass(frozen=True, slots=True)
class TemporalAttentionCollection:
    attentions: tuple[TemporalAttention, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.attentions, tuple) or any(
            not isinstance(item, TemporalAttention)
            for item in self.attentions
        ):
            raise TypeError(
                "attentions deve ser uma tupla de TemporalAttention."
            )
        identities = tuple(
            (item.score_id, item.code) for item in self.attentions
        )
        if len(identities) != len(set(identities)):
            raise ValueError("Attention Flags duplicadas para o Score.")

    def __iter__(self) -> Iterator[TemporalAttention]:
        return iter(self.attentions)

    def __len__(self) -> int:
        return len(self.attentions)

    def for_score(self, score_id: str) -> tuple[TemporalAttention, ...]:
        return tuple(
            item for item in self.attentions if item.score_id == score_id
        )


class TemporalAttentionAnalyzer:
    """Produz orientações de UI sem modificar o resultado normativo."""

    def analyze(
        self,
        scores: CriterionScoreCollection,
    ) -> TemporalAttentionCollection:
        if not isinstance(scores, CriterionScoreCollection):
            raise TypeError("scores deve ser CriterionScoreCollection.")
        return TemporalAttentionCollection(tuple(
            attention
            for score in scores
            for attention in self._analyze_score(score)
        ))

    def _analyze_score(
        self,
        score: CriterionScore,
    ) -> tuple[TemporalAttention, ...]:
        contract = score.source_contract
        if (
            contract.counting_rule.rule_type != "PER_YEAR"
            or len(contract.occurrences) != 1
        ):
            return ()
        period = contract.occurrences[0].period
        if period.start is None or period.end is None:
            return ()
        try:
            start = date.fromisoformat(period.start)
            end = date.fromisoformat(period.end)
        except ValueError:
            return ()
        if end < start:
            return ()
        decomposition = decompose_temporal_period(start, end)
        result: list[TemporalAttention] = []
        if (
            decomposition.residual_months == 6
            and decomposition.residual_days == 0
        ):
            result.append(self._attention(
                score,
                TemporalAttentionCode.EXACT_SIX_MONTH_LIMIT,
                TemporalAttentionSeverity.WARNING,
                "Atenção: este período encontra-se exatamente no "
                "limite da regra de conversão temporal (6 meses).",
                "A fração residual possui seis meses-calendário "
                "completos e zero dias residuais.",
            ))
        elif (
            decomposition.residual_months == 5
            and decomposition.residual_days > 0
        ):
            result.append(self._attention(
                score,
                TemporalAttentionCode.JUST_BELOW_SIX_MONTH_LIMIT,
                TemporalAttentionSeverity.WARNING,
                "Atenção: pequena diferença documental poderá alterar "
                "a quantidade de anos considerados.",
                "A fração residual está entre cinco e seis meses.",
            ))
        elif (
            decomposition.residual_months == 6
            and decomposition.residual_days > 0
        ):
            result.append(self._attention(
                score,
                TemporalAttentionCode.JUST_ABOVE_SIX_MONTH_LIMIT,
                TemporalAttentionSeverity.WARNING,
                "O período ultrapassa por pequena margem o limite de "
                "conversão temporal. Recomenda-se conferência das datas "
                "dos documentos.",
                "A fração residual está acima de seis e abaixo de sete "
                "meses-calendário.",
            ))
        if (start.month, start.day) == (2, 29) or (
            end.month,
            end.day,
        ) == (2, 29):
            result.append(self._attention(
                score,
                TemporalAttentionCode.LEAP_DAY_INVOLVED,
                TemporalAttentionSeverity.INFO,
                "O cálculo envolve ano bissexto. Recomenda-se "
                "conferência das datas.",
                "A data inicial ou final coincide com 29 de fevereiro.",
            ))
        if (
            decomposition.residual_days == 0
            and decomposition.residual_months in (0, 6)
        ):
            result.append(self._attention(
                score,
                TemporalAttentionCode.EXACT_TEMPORAL_LANDMARK,
                TemporalAttentionSeverity.INFO,
                "Período localizado exatamente em marco temporal "
                "normativo.",
                "A data final coincide com aniversário completo ou com "
                "o marco de seis meses-calendário.",
            ))
        return tuple(result)

    @staticmethod
    def _attention(
        score: CriterionScore,
        code: TemporalAttentionCode,
        severity: TemporalAttentionSeverity,
        message: str,
        explanation: str,
    ) -> TemporalAttention:
        return TemporalAttention(
            code=code,
            severity=severity,
            message=message,
            explanation=explanation,
            score_id=score.score_id,
            contract_id=score.contract_id,
            criterion_id=score.criterion_id,
        )


__all__ = [
    "TemporalAttention",
    "TemporalAttentionAnalyzer",
    "TemporalAttentionCode",
    "TemporalAttentionCollection",
    "TemporalAttentionSeverity",
]
