"""DTOs imutáveis do Resource Presentation Model."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import Enum
from types import MappingProxyType
from typing import TypeAlias


class ResourceContractError(ValueError):
    """Um valor não preserva o contrato de Resource."""


class ResourceType(str, Enum):
    DOCUMENT = "document"
    EVIDENCE = "evidence"
    EXECUTION_FACT = "execution_fact"
    REQUIREMENT = "requirement"
    CRITERION = "criterion"
    EVALUATION = "evaluation"
    REPORT = "report"


class RelationshipType(str, Enum):
    USED_BY = "used_by"
    CONTAINS = "contains"
    PRODUCES = "produces"
    BELONGS_TO = "belongs_to"
    REFERENCES = "references"
    DEPENDS_ON = "depends_on"


class PresentationAction(str, Enum):
    OPEN = "open"
    INSPECT = "inspect"
    REVEAL = "reveal"
    COPY_IDENTIFIER = "copy_identifier"


Scalar: TypeAlias = str | int | float | bool | None


def _text(value: object, name: str, *, optional: bool = False) -> str | None:
    if optional and value is None:
        return None
    if not isinstance(value, str):
        suffix = " ou None" if optional else ""
        raise ResourceContractError(f"{name} deve ser string{suffix}.")
    normalized = value.strip()
    if not normalized:
        raise ResourceContractError(f"{name} não pode ser vazio.")
    return normalized


def _metadata(
    value: Mapping[str, Scalar], name: str
) -> Mapping[str, Scalar]:
    if not isinstance(value, Mapping):
        raise ResourceContractError(f"{name} deve ser um mapping.")
    frozen: dict[str, Scalar] = {}
    for key, item in value.items():
        normalized_key = _text(key, f"{name}.key")
        if normalized_key in frozen:
            raise ResourceContractError(
                f"{name} contém chave duplicada após normalização."
            )
        if not isinstance(item, (str, int, float, bool, type(None))):
            raise ResourceContractError(
                f"{name}.{normalized_key} deve possuir valor escalar."
            )
        frozen[normalized_key] = (
            item.strip() if isinstance(item, str) else item
        )
    return MappingProxyType(frozen)


@dataclass(frozen=True, slots=True)
class ResourceIdentity:
    resource_type: ResourceType
    resource_id: str

    def __post_init__(self) -> None:
        if not isinstance(self.resource_type, ResourceType):
            raise ResourceContractError(
                "resource_type deve ser ResourceType."
            )
        object.__setattr__(
            self, "resource_id", _text(self.resource_id, "resource_id")
        )


@dataclass(frozen=True, slots=True)
class ResourceDisplay:
    display_name: str
    status: str | None = None
    metadata: Mapping[str, Scalar] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "display_name", _text(self.display_name, "display_name")
        )
        object.__setattr__(
            self, "status", _text(self.status, "status", optional=True)
        )
        object.__setattr__(
            self, "metadata", _metadata(self.metadata, "metadata")
        )


@dataclass(frozen=True, slots=True)
class ResourceRelationship:
    relationship_type: RelationshipType
    target_identity: ResourceIdentity
    label: str | None = None
    metadata: Mapping[str, Scalar] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not isinstance(self.relationship_type, RelationshipType):
            raise ResourceContractError(
                "relationship_type deve ser RelationshipType."
            )
        if not isinstance(self.target_identity, ResourceIdentity):
            raise ResourceContractError(
                "target_identity deve ser ResourceIdentity."
            )
        object.__setattr__(
            self, "label", _text(self.label, "label", optional=True)
        )
        object.__setattr__(
            self, "metadata", _metadata(self.metadata, "metadata")
        )


@dataclass(frozen=True, slots=True)
class Resource:
    identity: ResourceIdentity
    display: ResourceDisplay
    relationships: tuple[ResourceRelationship, ...] = ()
    available_actions: tuple[PresentationAction, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.identity, ResourceIdentity):
            raise ResourceContractError(
                "identity deve ser ResourceIdentity."
            )
        if not isinstance(self.display, ResourceDisplay):
            raise ResourceContractError("display deve ser ResourceDisplay.")
        if not isinstance(self.relationships, tuple) or any(
            not isinstance(item, ResourceRelationship)
            for item in self.relationships
        ):
            raise ResourceContractError(
                "relationships deve ser tuple de ResourceRelationship."
            )
        if not isinstance(self.available_actions, tuple) or any(
            not isinstance(item, PresentationAction)
            for item in self.available_actions
        ):
            raise ResourceContractError(
                "available_actions deve ser tuple de PresentationAction."
            )
        if len(set(self.available_actions)) != len(self.available_actions):
            raise ResourceContractError(
                "available_actions não aceita duplicatas."
            )


@dataclass(frozen=True, slots=True)
class ResourceCollection:
    resources: tuple[Resource, ...]
    total: int
    projection_context: Mapping[str, Scalar] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not isinstance(self.resources, tuple) or any(
            not isinstance(item, Resource) for item in self.resources
        ):
            raise ResourceContractError(
                "resources deve ser tuple de Resource."
            )
        if isinstance(self.total, bool) or not isinstance(self.total, int):
            raise ResourceContractError("total deve ser inteiro.")
        if self.total < len(self.resources):
            raise ResourceContractError(
                "total não pode ser menor que a coleção projetada."
            )
        object.__setattr__(
            self,
            "projection_context",
            _metadata(self.projection_context, "projection_context"),
        )


def serialize_resource(resource: Resource) -> dict[str, object]:
    """Converte um Resource em dados simples, sem semântica adicional."""
    if not isinstance(resource, Resource):
        raise TypeError("resource deve ser Resource.")
    return {
        "identity": {
            "resource_type": resource.identity.resource_type.value,
            "resource_id": resource.identity.resource_id,
        },
        "display": {
            "display_name": resource.display.display_name,
            "status": resource.display.status,
            "metadata": dict(resource.display.metadata),
        },
        "relationships": [
            {
                "relationship_type": item.relationship_type.value,
                "target_identity": {
                    "resource_type": item.target_identity.resource_type.value,
                    "resource_id": item.target_identity.resource_id,
                },
                "label": item.label,
                "metadata": dict(item.metadata),
            }
            for item in resource.relationships
        ],
        "available_actions": [
            item.value for item in resource.available_actions
        ],
    }


def serialize_resource_collection(
    collection: ResourceCollection,
) -> dict[str, object]:
    if not isinstance(collection, ResourceCollection):
        raise TypeError("collection deve ser ResourceCollection.")
    return {
        "resources": [serialize_resource(item) for item in collection.resources],
        "total": collection.total,
        "projection_context": dict(collection.projection_context),
    }


__all__ = [
    "PresentationAction",
    "RelationshipType",
    "Resource",
    "ResourceCollection",
    "ResourceContractError",
    "ResourceDisplay",
    "ResourceIdentity",
    "ResourceRelationship",
    "ResourceType",
    "Scalar",
    "serialize_resource",
    "serialize_resource_collection",
]
