"""Interfaces públicas para capabilities compartilhadas da plataforma."""

from collections.abc import Mapping
from datetime import datetime
from typing import Protocol, runtime_checkable


DOCUMENT_ENGINE_CAPABILITY = "platform.document_engine"
KNOWLEDGE_ENGINE_CAPABILITY = "platform.knowledge_engine"
NAVIGATION_CAPABILITY = "platform.navigation"
LOGGING_CAPABILITY = "platform.logging"
CLOCK_CAPABILITY = "platform.clock"
ID_GENERATOR_CAPABILITY = "platform.id_generator"


@runtime_checkable
class Capability(Protocol):
    """Identidade mínima comum a uma capability pública."""

    @property
    def capability_id(self) -> str:
        """Identificador estável e global da capability."""


@runtime_checkable
class DocumentEngineCapability(Capability, Protocol):
    """Fronteira nominal do Document Engine."""


@runtime_checkable
class KnowledgeEngineCapability(Capability, Protocol):
    """Fronteira nominal do Knowledge Engine."""


@runtime_checkable
class NavigationCapability(Capability, Protocol):
    """Solicita navegação sem depender de uma toolkit de interface."""

    def navigate(
        self,
        destination: str,
        parameters: Mapping[str, object] | None = None,
    ) -> bool:
        """Tenta navegar para um destino lógico."""


@runtime_checkable
class LoggingCapability(Capability, Protocol):
    """Registra diagnósticos sem expor um backend de logging."""

    def debug(self, message: str) -> None:
        """Registra diagnóstico detalhado."""

    def info(self, message: str) -> None:
        """Registra informação operacional."""

    def warning(self, message: str) -> None:
        """Registra condição recuperável."""

    def error(
        self,
        message: str,
        exception: BaseException | None = None,
    ) -> None:
        """Registra uma falha e sua causa opcional."""


@runtime_checkable
class ClockCapability(Capability, Protocol):
    """Fornece o instante corrente de forma substituível."""

    def now(self) -> datetime:
        """Retorna o instante corrente."""


@runtime_checkable
class IdGeneratorCapability(Capability, Protocol):
    """Gera identidades opacas sem impor sua representação interna."""

    def new_id(self) -> str:
        """Retorna uma nova identidade."""


@runtime_checkable
class CapabilityProvider(Protocol):
    """Expõe capabilities por identidade sem conhecer implementações."""

    @property
    def capability_ids(self) -> frozenset[str]:
        """Identidades das capabilities disponíveis."""

    def get_capability(self, capability_id: str) -> Capability:
        """Obtém uma capability registrada."""
