"""Representação interna mínima de um Projeto RSC."""

from dataclasses import dataclass
from typing import ClassVar


@dataclass(frozen=True, slots=True)
class Project:
    """Aggregate Root dos casos de uso do ProcDoc RSC."""

    INITIAL_STATUS: ClassVar[str] = "novo"

    project_id: str
    title: str
    status: str
