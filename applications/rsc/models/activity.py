"""Representação interna mínima de uma atividade profissional."""

from dataclasses import dataclass
from typing import ClassVar


@dataclass(frozen=True, slots=True)
class Activity:
    """Atividade mantida pelos casos de uso do ProcDoc RSC."""

    INITIAL_STATE: ClassVar[str] = "lembrada"

    activity_id: str
    description: str
    state: str
