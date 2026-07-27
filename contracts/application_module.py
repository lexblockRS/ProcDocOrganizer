"""Contrato conceitual de um módulo de Application da plataforma."""

from typing import Protocol, runtime_checkable

from .application_descriptor import ApplicationDescriptor
from .lifecycle import ApplicationLifecycleTransition


@runtime_checkable
class ApplicationModule(Protocol):
    """Fronteira futura de composição e lifecycle de uma Application."""

    @property
    def descriptor(self) -> ApplicationDescriptor:
        """Metadados estáticos do módulo."""

    def prepare(self, context: object) -> None:
        """Prepara o módulo para um projeto, sem criar a sessão do Host."""

    def create_session(self, context: object) -> object:
        """Cria a sessão da Application a partir do SessionContext do Host."""

    def contributions(self, session: object) -> tuple[object, ...]:
        """Declara futuramente contribuições pertencentes à sessão."""

    def transition(
        self,
        transition: ApplicationLifecycleTransition,
    ) -> None:
        """Recebe uma transição já validada do lifecycle."""

    def dispose(self) -> None:
        """Libera recursos pertencentes ao módulo."""
