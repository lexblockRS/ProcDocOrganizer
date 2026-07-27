"""Comando para criar uma interpretação funcional documental."""

from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True, slots=True)
class CreateFunctionalAssignmentEvidenceCommand:
    """Dados estruturados de entrada para uma atribuição documental."""

    person_id: str
    source_evidence_reference: str
    exercise_type_code: str
    exercise_type_label: str
    role: str
    organization: str
    start_date: date | None = None
    end_date: date | None = None
    unit: str | None = None
    administrative_reference: str | None = None
