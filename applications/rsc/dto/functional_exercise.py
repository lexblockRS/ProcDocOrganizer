"""Representação de saída de um exercício funcional."""

from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True, slots=True)
class FunctionalExerciseDTO:
    """Resultado do caso de uso CreateFunctionalExercise."""

    id: str
    person_id: str
    exercise_type_code: str
    exercise_type_label: str
    role: str
    context_organization: str
    context_unit: str | None
    context_reference: str | None
    start_date: date
    end_date: date | None
    status: str
    functional_assignment_evidence_ids: tuple[str, ...] = ()
