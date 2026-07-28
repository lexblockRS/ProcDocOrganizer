"""DTO imutável do estado consolidado de um processo RSC."""

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Any


@dataclass(frozen=True, slots=True)
class ProcessSummary:
    """Snapshot cujo percentual é atividades com evidência / cadastradas."""

    process_id: str
    created_at: datetime
    total_documents: int
    total_activities: int
    total_evidence: int
    total_requirements: int
    total_validation_errors: int
    total_validation_warnings: int
    validation_result: Any
    score_result: Any
    total_score: Decimal
    score_by_requirement: tuple[tuple[str, Decimal], ...]
    completion_percentage: Decimal
    generated_at: datetime
