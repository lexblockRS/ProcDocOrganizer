"""Representação de saída de uma atividade profissional."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ActivityDTO:
    """Resultado do caso de uso CreateActivity."""

    activity_id: str
    description: str
    state: str
