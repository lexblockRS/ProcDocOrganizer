"""Contrato neutro para extensões do Dashboard."""

from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from enum import Enum
from types import MappingProxyType


class DashboardRefreshPolicy(str, Enum):
    MANUAL = "manual"
    ON_OPEN = "on_open"
    PERIODIC = "periodic"


@dataclass(frozen=True, slots=True)
class DashboardContribution:
    application_id: str
    section: str
    priority: int
    widget_factory: Callable[[], object]
    refresh_policy: DashboardRefreshPolicy
    visibility: bool | Callable[[object | None], bool] = True
    metadata: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for name, value in (
            ("application_id", self.application_id),
            ("section", self.section),
        ):
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} deve ser um texto não vazio.")
            object.__setattr__(self, name, value.strip())
        if isinstance(self.priority, bool) or not isinstance(
            self.priority,
            int,
        ):
            raise TypeError("priority deve ser um inteiro.")
        if not callable(self.widget_factory):
            raise TypeError("widget_factory deve ser chamável.")
        if not isinstance(self.refresh_policy, DashboardRefreshPolicy):
            raise TypeError(
                "refresh_policy deve ser uma DashboardRefreshPolicy."
            )
        if not isinstance(self.visibility, bool) and not callable(
            self.visibility
        ):
            raise TypeError("visibility deve ser bool ou chamável.")
        try:
            metadata = dict(self.metadata)
        except (TypeError, ValueError) as exc:
            raise TypeError("metadata deve ser um mapeamento.") from exc
        object.__setattr__(
            self,
            "metadata",
            MappingProxyType(metadata),
        )
