"""Discovery público e determinístico de providers de Applications."""

from collections.abc import Iterable
import importlib
import pkgutil
from typing import Protocol, runtime_checkable

from contracts import (
    ApplicationModule,
    ContributionRegistration,
)


@runtime_checkable
class ApplicationProvider(Protocol):
    def applications(self) -> tuple[ApplicationModule, ...]:
        """Fornece módulos de Application."""

    def contributions(self) -> tuple[ContributionRegistration, ...]:
        """Fornece contribuições estáticas dos módulos."""


class ApplicationCatalog:
    """Snapshot público de Applications e contribuições descobertas."""

    def __init__(
        self,
        providers: Iterable[ApplicationProvider] = (),
    ) -> None:
        self._providers = tuple(providers)
        if any(
            not isinstance(provider, ApplicationProvider)
            for provider in self._providers
        ):
            raise TypeError(
                "providers deve conter apenas ApplicationProvider."
            )
        self._applications = tuple(
            application
            for provider in self._providers
            for application in provider.applications()
        )
        self._contributions = tuple(
            contribution
            for provider in self._providers
            for contribution in provider.contributions()
        )
        if any(
            not isinstance(application, ApplicationModule)
            for application in self._applications
        ):
            raise TypeError(
                "Providers devem fornecer apenas ApplicationModule."
            )
        if any(
            not isinstance(item, ContributionRegistration)
            for item in self._contributions
        ):
            raise TypeError(
                "Providers devem fornecer ContributionRegistration."
            )

    @property
    def applications(self) -> tuple[ApplicationModule, ...]:
        return tuple(sorted(
            self._applications,
            key=lambda item: item.descriptor.application_id,
        ))

    @property
    def contributions(self) -> tuple[ContributionRegistration, ...]:
        positions = {
            id(item): index
            for index, item in enumerate(self._contributions)
        }
        return tuple(sorted(
            self._contributions,
            key=lambda item: (
                -item.priority,
                item.application_id,
                item.category.value,
                positions[id(item)],
            ),
        ))

    @classmethod
    def discover(
        cls,
        package_name: str = "applications",
    ) -> "ApplicationCatalog":
        package = importlib.import_module(package_name)
        providers = []
        module_names = sorted(
            item.name
            for item in pkgutil.iter_modules(
                package.__path__,
                f"{package.__name__}.",
            )
            if item.ispkg
        )
        for module_name in module_names:
            provider_name = f"{module_name}.provider"
            try:
                provider_module = importlib.import_module(provider_name)
            except ModuleNotFoundError as exc:
                if exc.name == provider_name:
                    continue
                raise
            provider = getattr(
                provider_module, "APPLICATION_PROVIDER", None
            )
            if provider is not None:
                providers.append(provider)
        return cls(providers)
