"""Componentes declarativos de apresentação sem dependência de Qt."""

from collections.abc import Callable
from dataclasses import dataclass
from typing import Protocol, runtime_checkable


def _text(value: object, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} deve ser um texto não vazio.")
    return value.strip()


@runtime_checkable
class ApplicationController(Protocol):
    def execute(
        self,
        command_id: str,
        context: object | None = None,
    ) -> object:
        """Executa um comando público da Application."""


@dataclass(frozen=True, slots=True)
class ApplicationView:
    """Descrição neutra de uma View textual materializável pelo Host."""

    title: str
    content: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "title", _text(self.title, "title"))
        content = tuple(self.content)
        if any(not isinstance(item, str) for item in content):
            raise TypeError("content deve conter apenas strings.")
        object.__setattr__(self, "content", content)


@dataclass(frozen=True, slots=True)
class DashboardCard:
    """Card declarativo com valor estático ou calculado."""

    title: str
    value: object | Callable[[object | None], object]
    key: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "title", _text(self.title, "title"))
        if self.key is not None:
            object.__setattr__(self, "key", _text(self.key, "key"))


@dataclass(frozen=True, slots=True)
class DashboardPanel:
    """Seção declarativa composta por cards."""

    title: str
    cards: tuple[DashboardCard, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "title", _text(self.title, "title"))
        cards = tuple(self.cards)
        if any(not isinstance(card, DashboardCard) for card in cards):
            raise TypeError("cards deve conter apenas DashboardCard.")
        object.__setattr__(self, "cards", cards)
