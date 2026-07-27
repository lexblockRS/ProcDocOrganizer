"""Modelo neutro para contribuições fornecidas por Applications."""

from dataclasses import dataclass
from enum import Enum


class ContributionCategory(str, Enum):
    """Categorias reconhecidas pela infraestrutura da plataforma."""

    MENU = "menu"
    TOOLBAR = "toolbar"
    VIEW = "view"
    PAGE = "page"
    DASHBOARD = "dashboard"
    ACTION = "action"
    COMMAND = "command"
    SERVICE = "service"
    OTHER = "other"


@dataclass(frozen=True, slots=True)
class ContributionRegistration:
    """Associa uma contribuição opaca à sua origem e ordenação."""

    category: ContributionCategory
    application_id: str
    priority: int
    contribution: object

    def __post_init__(self) -> None:
        if not isinstance(self.category, ContributionCategory):
            raise TypeError(
                "category deve ser uma ContributionCategory."
            )
        if (
            not isinstance(self.application_id, str)
            or not self.application_id.strip()
        ):
            raise ValueError(
                "application_id deve ser um texto não vazio."
            )
        if isinstance(self.priority, bool) or not isinstance(
            self.priority,
            int,
        ):
            raise TypeError("priority deve ser um inteiro.")
        if self.contribution is None:
            raise ValueError("contribution não pode ser None.")

        object.__setattr__(
            self,
            "application_id",
            self.application_id.strip(),
        )
