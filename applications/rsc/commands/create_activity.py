"""Comando para solicitar a criação de uma atividade profissional."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class CreateActivityCommand:
    """Dados de entrada do caso de uso CreateActivity."""

    description: str
    functional_assignment_evidence_ids: tuple[str, ...] = ()
    functional_exercise_ids: tuple[str, ...] = ()
