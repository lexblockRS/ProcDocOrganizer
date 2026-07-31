"""Contratos imutáveis e independentes de toolkit para navegação."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import Enum
from types import MappingProxyType
from typing import TypeAlias


class NavigationContractError(ValueError):
    """Uma intenção ou filtro não preserva o contrato de apresentação."""


class NavigationIntentType(str, Enum):
    OPEN_PERSPECTIVE = "open_perspective"
    OPEN_DASHBOARD = "open_dashboard"
    OPEN_DOCUMENT = "open_document"
    OPEN_EVIDENCE = "open_evidence"
    OPEN_EXECUTION_FACT = "open_execution_fact"
    OPEN_REQUIREMENT = "open_requirement"
    OPEN_CRITERION = "open_criterion"
    OPEN_EVALUATION = "open_evaluation"
    OPEN_REPORT = "open_report"


Scalar: TypeAlias = str | int | float | bool | None


def _normalized_optional(value: str | None, name: str) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise NavigationContractError(f"{name} deve ser string ou None.")
    normalized = value.strip()
    if not normalized:
        raise NavigationContractError(f"{name} não pode ser vazio.")
    return normalized


def _freeze_scalars(
    values: Mapping[str, Scalar], name: str
) -> Mapping[str, Scalar]:
    if not isinstance(values, Mapping):
        raise NavigationContractError(f"{name} deve ser um mapping.")
    frozen: dict[str, Scalar] = {}
    for key, value in values.items():
        if not isinstance(key, str) or not key.strip():
            raise NavigationContractError(
                f"{name} exige chaves textuais não vazias."
            )
        if not isinstance(value, (str, int, float, bool, type(None))):
            raise NavigationContractError(
                f"{name}.{key} deve possuir valor escalar."
            )
        normalized = key.strip()
        if normalized in frozen:
            raise NavigationContractError(
                f"{name} contém chave duplicada."
            )
        frozen[normalized] = value.strip() if isinstance(value, str) else value
    return MappingProxyType(frozen)


@dataclass(frozen=True, slots=True)
class WorkspaceFilter:
    """Filtro tipado pertencente ao contexto do Workspace."""

    filter_id: str
    parameters: Mapping[str, Scalar] = field(default_factory=dict)

    def __post_init__(self) -> None:
        normalized = _normalized_optional(self.filter_id, "filter_id")
        object.__setattr__(self, "filter_id", normalized)
        object.__setattr__(
            self, "parameters", _freeze_scalars(self.parameters, "parameters")
        )


@dataclass(frozen=True, slots=True)
class NavigationIntent:
    """Solicitação única de navegação, sem conhecimento de interface."""

    intent_type: NavigationIntentType
    target_id: str | None = None
    project_id: str | None = None
    origin: str | None = None
    filters: tuple[WorkspaceFilter, ...] = ()
    metadata: Mapping[str, Scalar] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not isinstance(self.intent_type, NavigationIntentType):
            raise NavigationContractError(
                "intent_type deve ser NavigationIntentType."
            )
        for name in ("target_id", "project_id", "origin"):
            object.__setattr__(
                self, name, _normalized_optional(getattr(self, name), name)
            )
        if not isinstance(self.filters, tuple) or any(
            not isinstance(item, WorkspaceFilter) for item in self.filters
        ):
            raise NavigationContractError(
                "filters deve ser tuple de WorkspaceFilter."
            )
        if len({item.filter_id for item in self.filters}) != len(self.filters):
            raise NavigationContractError("filters contém IDs duplicados.")
        object.__setattr__(
            self, "metadata", _freeze_scalars(self.metadata, "metadata")
        )
        if self.intent_type is not NavigationIntentType.OPEN_DASHBOARD and (
            self.target_id is None
        ):
            raise NavigationContractError(
                f"{self.intent_type.value} exige target_id."
            )

    @classmethod
    def open_dashboard(cls, **values) -> "NavigationIntent":
        return cls(NavigationIntentType.OPEN_DASHBOARD, **values)

    @classmethod
    def open_document(cls, target_id: str, **values) -> "NavigationIntent":
        return cls(NavigationIntentType.OPEN_DOCUMENT, target_id, **values)

    @classmethod
    def open_evidence(cls, target_id: str, **values) -> "NavigationIntent":
        return cls(NavigationIntentType.OPEN_EVIDENCE, target_id, **values)

    @classmethod
    def open_execution_fact(
        cls, target_id: str, **values
    ) -> "NavigationIntent":
        return cls(
            NavigationIntentType.OPEN_EXECUTION_FACT, target_id, **values
        )

    @classmethod
    def open_requirement(cls, target_id: str, **values) -> "NavigationIntent":
        return cls(NavigationIntentType.OPEN_REQUIREMENT, target_id, **values)

    @classmethod
    def open_criterion(cls, target_id: str, **values) -> "NavigationIntent":
        return cls(NavigationIntentType.OPEN_CRITERION, target_id, **values)

    @classmethod
    def open_evaluation(cls, target_id: str, **values) -> "NavigationIntent":
        return cls(NavigationIntentType.OPEN_EVALUATION, target_id, **values)

    @classmethod
    def open_report(cls, target_id: str, **values) -> "NavigationIntent":
        return cls(NavigationIntentType.OPEN_REPORT, target_id, **values)


__all__ = [
    "NavigationContractError",
    "NavigationIntent",
    "NavigationIntentType",
    "Scalar",
    "WorkspaceFilter",
]
