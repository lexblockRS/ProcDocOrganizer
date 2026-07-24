"""Comando para solicitar a criação de uma atividade profissional."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class CreateActivityCommand:
    """Dados de entrada do caso de uso CreateActivity."""

    description: str
