"""Contratos neutros para contribuições declaradas por Applications."""

from collections.abc import Callable
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ActionContribution:
    """Declara uma ação sem depender de detalhes da interface gráfica."""

    contribution_id: str
    text: str
    callback: Callable[[], None]
    menu_id: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.contribution_id, str):
            raise TypeError("contribution_id deve ser uma string.")
        if not self.contribution_id.strip():
            raise ValueError("contribution_id não pode ser vazio.")

        if not isinstance(self.text, str):
            raise TypeError("text deve ser uma string.")
        if not self.text.strip():
            raise ValueError("text não pode ser vazio.")

        if not callable(self.callback):
            raise TypeError("callback deve ser chamável.")

        if self.menu_id is not None:
            if not isinstance(self.menu_id, str):
                raise TypeError("menu_id deve ser uma string ou None.")
            if not self.menu_id.strip():
                raise ValueError("menu_id não pode ser vazio.")
