"""Fronteira arquitetural neutra para Applications."""

from typing import Protocol, runtime_checkable

from models import Project


@runtime_checkable
class Application(Protocol):
    """Contrato mínimo implementado por uma Application do ProcDoc."""

    @property
    def application_id(self) -> str:
        """Identidade persistível e estável da Application."""

    @property
    def display_name(self) -> str:
        """Nome curto apresentado ao usuário."""

    def can_open(self, project: Project) -> bool:
        """Informa se a Application é compatível com o projeto."""

    def contributions(self) -> tuple[object, ...]:
        """Declara contribuições opacas fornecidas pela Application."""
