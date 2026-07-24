"""Representação de saída de um Projeto RSC."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ProjectDTO:
    """Resultado do caso de uso CreateProject."""

    project_id: str
    title: str
    status: str
