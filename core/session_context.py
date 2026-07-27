"""Recursos compartilhados disponíveis durante uma sessão."""

from collections.abc import Mapping
from dataclasses import dataclass, field
from types import MappingProxyType

from contracts.capabilities import (
    CapabilityProvider,
    NavigationCapability,
)


@dataclass(frozen=True, slots=True)
class SessionContext:
    """Agrupa recursos neutros sem criar ou implementar os engines."""

    document_engine: object
    knowledge_engine: object
    navigation: NavigationCapability | None = None
    shared_services: Mapping[str, object] = field(default_factory=dict)
    capability_provider: CapabilityProvider | None = None

    def __post_init__(self) -> None:
        if self.document_engine is None:
            raise ValueError("document_engine não pode ser None.")
        if self.knowledge_engine is None:
            raise ValueError("knowledge_engine não pode ser None.")
        if (
            self.navigation is not None
            and not isinstance(self.navigation, NavigationCapability)
        ):
            raise TypeError(
                "navigation deve implementar NavigationCapability."
            )
        if (
            self.capability_provider is not None
            and not isinstance(
                self.capability_provider,
                CapabilityProvider,
            )
        ):
            raise TypeError(
                "capability_provider deve implementar CapabilityProvider."
            )
        try:
            services = dict(self.shared_services)
        except (TypeError, ValueError) as exc:
            raise TypeError(
                "shared_services deve ser um mapeamento."
            ) from exc
        if any(
            not isinstance(key, str) or not key.strip()
            for key in services
        ):
            raise ValueError(
                "shared_services deve possuir chaves textuais não vazias."
            )
        if any(service is None for service in services.values()):
            raise ValueError(
                "shared_services não deve conter serviços None."
            )

        object.__setattr__(
            self,
            "shared_services",
            MappingProxyType(services),
        )
