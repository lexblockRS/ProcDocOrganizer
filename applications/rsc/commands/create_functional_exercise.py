"""Comando para solicitar a criação de um exercício funcional."""

from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True, slots=True)
class CreateFunctionalExerciseCommand:
    """Dados de entrada do caso de uso CreateFunctionalExercise."""

    person_id: str
    exercise_type_code: str
    exercise_type_label: str
    role: str
    context_organization: str
    start_date: date
    end_date: date | None = None
    context_unit: str | None = None
    context_reference: str | None = None
    functional_assignment_evidence_ids: tuple[str, ...] = ()
