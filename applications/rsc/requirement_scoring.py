"""Agregação oficial de CriterionScore por requisito."""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass
from decimal import Decimal
from uuid import NAMESPACE_URL, uuid5

from applications.rsc.scoring_kernel import (
    CriterionScore,
    CriterionScoreCollection,
    ScoringState,
)


@dataclass(frozen=True, slots=True)
class RequirementAggregationTrace:
    requirement_id: str
    criterion_score_ids: tuple[str, ...]
    executed_score_ids: tuple[str, ...]
    blocked_score_ids: tuple[str, ...]
    ignored_score_ids: tuple[str, ...]
    participating_criterion_ids: tuple[str, ...]
    operation: str


@dataclass(frozen=True, slots=True)
class RequirementScore:
    requirement_score_id: str
    requirement_id: str
    criterion_scores: tuple[CriterionScore, ...]
    executed_scores: tuple[CriterionScore, ...]
    blocked_scores: tuple[CriterionScore, ...]
    ignored_scores: tuple[CriterionScore, ...]
    total_score: Decimal
    aggregation_trace: RequirementAggregationTrace
    explanation: str

    def __post_init__(self) -> None:
        for value, field_name in (
            (self.requirement_score_id, "requirement_score_id"),
            (self.requirement_id, "requirement_id"),
            (self.explanation, "explanation"),
        ):
            if not isinstance(value, str) or not value.strip():
                raise TypeError(f"{field_name} deve ser textual.")
        for value, field_name in (
            (self.criterion_scores, "criterion_scores"),
            (self.executed_scores, "executed_scores"),
            (self.blocked_scores, "blocked_scores"),
            (self.ignored_scores, "ignored_scores"),
        ):
            _require_scores(value, field_name)
        if not isinstance(self.total_score, Decimal):
            raise TypeError("total_score deve ser Decimal.")
        if not isinstance(
            self.aggregation_trace,
            RequirementAggregationTrace,
        ):
            raise TypeError(
                "aggregation_trace deve ser RequirementAggregationTrace."
            )
        if any(
            score.requirement_id != self.requirement_id
            for score in self.criterion_scores
        ):
            raise ValueError(
                "Todos os CriterionScore devem pertencer ao requisito."
            )
        partition = (
            self.executed_scores
            + self.blocked_scores
            + self.ignored_scores
        )
        if (
            len(partition) != len(self.criterion_scores)
            or set(map(id, partition)) != set(map(id, self.criterion_scores))
        ):
            raise ValueError(
                "As classificações devem preservar todos os CriterionScore."
            )


@dataclass(frozen=True, slots=True)
class RequirementScoreCollection:
    requirement_scores: tuple[RequirementScore, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.requirement_scores, tuple) or any(
            not isinstance(item, RequirementScore)
            for item in self.requirement_scores
        ):
            raise TypeError(
                "requirement_scores deve ser uma tupla de RequirementScore."
            )
        identities = tuple(
            item.requirement_score_id for item in self.requirement_scores
        )
        requirements = tuple(
            item.requirement_id for item in self.requirement_scores
        )
        if len(identities) != len(set(identities)):
            raise ValueError("RequirementScore possui identidade duplicada.")
        if len(requirements) != len(set(requirements)):
            raise ValueError("Existe mais de um Score para o requisito.")

    def __iter__(self) -> Iterator[RequirementScore]:
        return iter(self.requirement_scores)

    def __len__(self) -> int:
        return len(self.requirement_scores)


class RequirementScoreAggregator:
    """Agrupa Scores sem reinterpretar seus estados ou contratos."""

    def aggregate(
        self,
        scores: CriterionScoreCollection,
    ) -> RequirementScoreCollection:
        if not isinstance(scores, CriterionScoreCollection):
            raise TypeError("scores deve ser CriterionScoreCollection.")
        grouped: dict[str, list[CriterionScore]] = {}
        for score in scores:
            grouped.setdefault(score.requirement_id, []).append(score)
        return RequirementScoreCollection(tuple(
            self._aggregate_requirement(requirement_id, tuple(items))
            for requirement_id, items in grouped.items()
        ))

    @staticmethod
    def _aggregate_requirement(
        requirement_id: str,
        scores: tuple[CriterionScore, ...],
    ) -> RequirementScore:
        executed = tuple(
            score
            for score in scores
            if score.scoring_state is ScoringState.EXECUTED
        )
        blocked = tuple(
            score
            for score in scores
            if score.scoring_state is ScoringState.BLOCKED
        )
        ignored = tuple(
            score
            for score in scores
            if score.scoring_state
            not in (ScoringState.EXECUTED, ScoringState.BLOCKED)
        )
        total = sum(
            (score.calculated_score for score in executed),
            Decimal(0),
        )
        trace = RequirementAggregationTrace(
            requirement_id=requirement_id,
            criterion_score_ids=tuple(
                score.score_id for score in scores
            ),
            executed_score_ids=tuple(
                score.score_id for score in executed
            ),
            blocked_score_ids=tuple(
                score.score_id for score in blocked
            ),
            ignored_score_ids=tuple(
                score.score_id for score in ignored
            ),
            participating_criterion_ids=tuple(
                score.criterion_id for score in executed
            ),
            operation="DECIMAL_SUM_EXECUTED_ONLY",
        )
        ignored_states = ", ".join(
            f"{score.criterion_id}:{score.scoring_state.value}"
            for score in (*blocked, *ignored)
        ) or "nenhum"
        participants = ", ".join(
            score.criterion_id for score in executed
        ) or "nenhum"
        explanation = (
            f"Requisito {requirement_id}: {len(scores)} critério(s); "
            f"{len(executed)} executado(s); {len(blocked)} bloqueado(s); "
            f"ignorados na soma: {ignored_states}; participantes: "
            f"{participants}; soma Decimal = {total}."
        )
        return RequirementScore(
            requirement_score_id=_stable_id(requirement_id),
            requirement_id=requirement_id,
            criterion_scores=scores,
            executed_scores=executed,
            blocked_scores=blocked,
            ignored_scores=ignored,
            total_score=total,
            aggregation_trace=trace,
            explanation=explanation,
        )


def _require_scores(value: object, field_name: str) -> None:
    if not isinstance(value, tuple) or any(
        not isinstance(item, CriterionScore) for item in value
    ):
        raise TypeError(f"{field_name} deve ser uma tupla de CriterionScore.")


def _stable_id(requirement_id: str) -> str:
    return str(uuid5(
        NAMESPACE_URL,
        f"requirement-score|{requirement_id}",
    ))


__all__ = [
    "RequirementAggregationTrace",
    "RequirementScore",
    "RequirementScoreAggregator",
    "RequirementScoreCollection",
]
