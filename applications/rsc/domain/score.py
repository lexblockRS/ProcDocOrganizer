"""Resultados imutáveis de pontuação RSC."""

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal


@dataclass(frozen=True, slots=True)
class ActivityScore:
    activity_id: str
    criterion_id: str
    quantity: Decimal
    points_per_unit: Decimal
    raw_score: Decimal
    applied_score: Decimal
    warnings: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class RequirementScore:
    requirement_id: str
    activity_scores: tuple[ActivityScore, ...]
    total_score: Decimal


@dataclass(frozen=True, slots=True)
class RscScoreResult:
    process_id: str
    requirement_scores: tuple[RequirementScore, ...]
    total_score: Decimal
    warnings: tuple[str, ...]
    calculated_at: datetime
