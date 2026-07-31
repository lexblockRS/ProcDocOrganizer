"""DTOs imutáveis do modelo oficial de Workspace Insights."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from .resources import ResourceIdentity


class InsightContractError(ValueError):
    """Um valor não preserva o contrato de Insight."""


class InsightCategory(str, Enum):
    COVERAGE = "coverage"
    VALIDATION = "validation"
    ORGANIZATION = "organization"
    COMPLETENESS = "completeness"
    INFORMATION = "information"


class InsightSeverity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    SUCCESS = "success"


class InsightAction(str, Enum):
    OPEN_RESOURCE = "open_resource"
    INSPECT_RESOURCE = "inspect_resource"
    REVEAL_RESOURCE = "reveal_resource"
    EXECUTE_EVALUATION = "execute_evaluation"


class InsightResourceRole(str, Enum):
    SUBJECT = "subject"
    SOURCE = "source"
    RELATED = "related"
    TARGET = "target"


def _text(value: object, name: str, *, optional: bool = False) -> str | None:
    if optional and value is None:
        return None
    if not isinstance(value, str):
        suffix = " ou None" if optional else ""
        raise InsightContractError(f"{name} deve ser string{suffix}.")
    normalized = value.strip()
    if not normalized:
        raise InsightContractError(f"{name} não pode ser vazio.")
    return normalized


def _revision(value: object, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise InsightContractError(f"{name} deve ser inteiro.")
    if value < 0:
        raise InsightContractError(f"{name} não pode ser negativa.")
    return value


@dataclass(frozen=True, slots=True, order=True)
class InsightIdentity:
    provider_id: str
    insight_code: str
    discriminator: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "provider_id", _text(self.provider_id, "provider_id")
        )
        object.__setattr__(
            self, "insight_code", _text(self.insight_code, "insight_code")
        )
        object.__setattr__(
            self,
            "discriminator",
            _text(self.discriminator, "discriminator", optional=True),
        )


@dataclass(frozen=True, slots=True)
class InsightResourceReference:
    identity: ResourceIdentity
    role: InsightResourceRole

    def __post_init__(self) -> None:
        if not isinstance(self.identity, ResourceIdentity):
            raise InsightContractError(
                "identity deve ser ResourceIdentity."
            )
        if not isinstance(self.role, InsightResourceRole):
            raise InsightContractError(
                "role deve ser InsightResourceRole."
            )


@dataclass(frozen=True, slots=True)
class Insight:
    identity: InsightIdentity
    category: InsightCategory
    severity: InsightSeverity
    title: str
    message: str
    explanation: str
    related_resources: tuple[InsightResourceReference, ...]
    available_actions: tuple[InsightAction, ...]
    source_revision: int
    evaluation_id: str | None = None
    evaluation_revision: int | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.identity, InsightIdentity):
            raise InsightContractError(
                "identity deve ser InsightIdentity."
            )
        if not isinstance(self.category, InsightCategory):
            raise InsightContractError(
                "category deve ser InsightCategory."
            )
        if not isinstance(self.severity, InsightSeverity):
            raise InsightContractError(
                "severity deve ser InsightSeverity."
            )
        for name in ("title", "message", "explanation"):
            object.__setattr__(self, name, _text(getattr(self, name), name))
        if not isinstance(self.related_resources, tuple) or any(
            not isinstance(item, InsightResourceReference)
            for item in self.related_resources
        ):
            raise InsightContractError(
                "related_resources deve ser tuple de InsightResourceReference."
            )
        reference_keys = {
            (item.identity, item.role) for item in self.related_resources
        }
        if len(reference_keys) != len(self.related_resources):
            raise InsightContractError(
                "related_resources contém identidade e papel duplicados."
            )
        if sum(
            item.role is InsightResourceRole.SUBJECT
            for item in self.related_resources
        ) > 1:
            raise InsightContractError(
                "related_resources aceita no máximo um SUBJECT."
            )
        if not isinstance(self.available_actions, tuple) or any(
            not isinstance(item, InsightAction)
            for item in self.available_actions
        ):
            raise InsightContractError(
                "available_actions deve ser tuple de InsightAction."
            )
        if len(set(self.available_actions)) != len(self.available_actions):
            raise InsightContractError(
                "available_actions não aceita duplicatas."
            )
        object.__setattr__(
            self,
            "source_revision",
            _revision(self.source_revision, "source_revision"),
        )
        evaluation_id = _text(
            self.evaluation_id, "evaluation_id", optional=True
        )
        if (evaluation_id is None) != (self.evaluation_revision is None):
            raise InsightContractError(
                "evaluation_id e evaluation_revision devem coexistir."
            )
        object.__setattr__(self, "evaluation_id", evaluation_id)
        if self.evaluation_revision is not None:
            object.__setattr__(
                self,
                "evaluation_revision",
                _revision(
                    self.evaluation_revision, "evaluation_revision"
                ),
            )


_SEVERITY_ORDER = {
    InsightSeverity.ERROR: 0,
    InsightSeverity.WARNING: 1,
    InsightSeverity.INFO: 2,
    InsightSeverity.SUCCESS: 3,
}


def insight_sort_key(insight: Insight) -> tuple[object, ...]:
    if not isinstance(insight, Insight):
        raise TypeError("insight deve ser Insight.")
    return (
        _SEVERITY_ORDER[insight.severity],
        insight.category.value,
        insight.identity.insight_code,
        insight.identity.provider_id,
        insight.identity.discriminator or "",
    )


@dataclass(frozen=True, slots=True)
class InsightCollection:
    insights: tuple[Insight, ...]
    total: int
    workspace_revision: int
    generated_at: datetime | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.insights, tuple) or any(
            not isinstance(item, Insight) for item in self.insights
        ):
            raise InsightContractError(
                "insights deve ser tuple de Insight."
            )
        identities = {item.identity for item in self.insights}
        if len(identities) != len(self.insights):
            raise InsightContractError(
                "insights contém identidades duplicadas."
            )
        if isinstance(self.total, bool) or not isinstance(self.total, int):
            raise InsightContractError("total deve ser inteiro.")
        if self.total != len(self.insights):
            raise InsightContractError(
                "total deve corresponder à quantidade de Insights."
            )
        object.__setattr__(
            self,
            "workspace_revision",
            _revision(self.workspace_revision, "workspace_revision"),
        )
        if self.generated_at is not None and not isinstance(
            self.generated_at, datetime
        ):
            raise InsightContractError(
                "generated_at deve ser datetime ou None."
            )
        object.__setattr__(
            self, "insights", tuple(sorted(self.insights, key=insight_sort_key))
        )


def serialize_insight(insight: Insight) -> dict[str, object]:
    if not isinstance(insight, Insight):
        raise TypeError("insight deve ser Insight.")
    return {
        "identity": {
            "provider_id": insight.identity.provider_id,
            "insight_code": insight.identity.insight_code,
            "discriminator": insight.identity.discriminator,
        },
        "category": insight.category.value,
        "severity": insight.severity.value,
        "title": insight.title,
        "message": insight.message,
        "explanation": insight.explanation,
        "related_resources": [
            {
                "resource_type": item.identity.resource_type.value,
                "resource_id": item.identity.resource_id,
                "role": item.role.value,
            }
            for item in insight.related_resources
        ],
        "available_actions": [
            item.value for item in insight.available_actions
        ],
        "source_revision": insight.source_revision,
        "evaluation_id": insight.evaluation_id,
        "evaluation_revision": insight.evaluation_revision,
    }


def serialize_insight_collection(
    collection: InsightCollection,
) -> dict[str, object]:
    if not isinstance(collection, InsightCollection):
        raise TypeError("collection deve ser InsightCollection.")
    return {
        "insights": [serialize_insight(item) for item in collection.insights],
        "total": collection.total,
        "workspace_revision": collection.workspace_revision,
        "generated_at": (
            None
            if collection.generated_at is None
            else collection.generated_at.isoformat()
        ),
    }


__all__ = [
    "Insight",
    "InsightAction",
    "InsightCategory",
    "InsightCollection",
    "InsightContractError",
    "InsightIdentity",
    "InsightResourceReference",
    "InsightResourceRole",
    "InsightSeverity",
    "insight_sort_key",
    "serialize_insight",
    "serialize_insight_collection",
]
