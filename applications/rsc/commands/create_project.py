"""Comando para solicitar a criação de um Projeto RSC."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class CreateProjectCommand:
    """Dados de entrada do caso de uso CreateProject."""

    title: str
