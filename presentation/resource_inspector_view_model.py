"""Projeção passiva de Resource para o Inspector."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .navigation_contracts import NavigationIntent
from .resources import (
    PresentationAction,
    Resource,
    ResourceIdentity,
    ResourceType,
)


class ResourceInspectorState(str, Enum):
    EMPTY = "empty"
    UNAVAILABLE = "unavailable"
    READY = "ready"


@dataclass(frozen=True, slots=True)
class MetadataItemView:
    label: str
    value: str


@dataclass(frozen=True, slots=True)
class RelationshipItemView:
    relationship_type: str
    target_type: str
    target_id: str
    label: str
    intent: NavigationIntent


@dataclass(frozen=True, slots=True)
class ResourceActionView:
    action: PresentationAction
    label: str
    intent: NavigationIntent


@dataclass(frozen=True, slots=True)
class ResourceInspectorViewData:
    state: ResourceInspectorState
    message: str
    resource_type: str = "—"
    resource_id: str = "—"
    display_name: str = "—"
    status: str = "—"
    metadata: tuple[MetadataItemView, ...] = ()
    relationships: tuple[RelationshipItemView, ...] = ()
    actions: tuple[ResourceActionView, ...] = ()


class ResourceInspectorViewModel:
    """Adapta Resource para DTOs visuais sem consultar sua origem."""

    def __init__(self, data: ResourceInspectorViewData) -> None:
        if not isinstance(data, ResourceInspectorViewData):
            raise TypeError("data deve ser ResourceInspectorViewData.")
        self._data = data

    @property
    def data(self) -> ResourceInspectorViewData:
        return self._data

    @classmethod
    def empty(cls) -> "ResourceInspectorViewModel":
        return cls(ResourceInspectorViewData(
            ResourceInspectorState.EMPTY,
            "Nenhum Resource selecionado.",
        ))

    @classmethod
    def unavailable(
        cls, identity: ResourceIdentity | None = None
    ) -> "ResourceInspectorViewModel":
        if identity is not None and not isinstance(identity, ResourceIdentity):
            raise TypeError("identity deve ser ResourceIdentity ou None.")
        return cls(ResourceInspectorViewData(
            ResourceInspectorState.UNAVAILABLE,
            "Projeção do Resource indisponível.",
            resource_type=(
                "—" if identity is None else identity.resource_type.value
            ),
            resource_id="—" if identity is None else identity.resource_id,
        ))

    @classmethod
    def from_resource(cls, resource: Resource) -> "ResourceInspectorViewModel":
        if not isinstance(resource, Resource):
            raise TypeError("resource deve ser Resource.")
        identity = resource.identity
        return cls(ResourceInspectorViewData(
            state=ResourceInspectorState.READY,
            message="",
            resource_type=identity.resource_type.value,
            resource_id=identity.resource_id,
            display_name=resource.display.display_name,
            status=resource.display.status or "—",
            metadata=tuple(
                MetadataItemView(key, _display_value(value))
                for key, value in sorted(resource.display.metadata.items())
            ),
            relationships=tuple(
                RelationshipItemView(
                    relationship.relationship_type.value,
                    relationship.target_identity.resource_type.value,
                    relationship.target_identity.resource_id,
                    relationship.label or "—",
                    _intent_for(
                        relationship.target_identity,
                        origin="resource_inspector_relationship",
                    ),
                )
                for relationship in resource.relationships
            ),
            actions=tuple(
                ResourceActionView(
                    action,
                    _ACTION_LABELS[action],
                    _intent_for(
                        identity,
                        origin="resource_inspector_action",
                        action=action,
                    ),
                )
                for action in resource.available_actions
            ),
        ))


_ACTION_LABELS = {
    PresentationAction.OPEN: "Abrir",
    PresentationAction.INSPECT: "Inspecionar",
    PresentationAction.REVEAL: "Revelar",
    PresentationAction.COPY_IDENTIFIER: "Copiar identificador",
}


def _intent_for(
    identity: ResourceIdentity,
    *,
    origin: str,
    action: PresentationAction | None = None,
) -> NavigationIntent:
    factories = {
        ResourceType.DOCUMENT: NavigationIntent.open_document,
        ResourceType.EVIDENCE: NavigationIntent.open_evidence,
        ResourceType.EXECUTION_FACT: NavigationIntent.open_execution_fact,
        ResourceType.REQUIREMENT: NavigationIntent.open_requirement,
        ResourceType.CRITERION: NavigationIntent.open_criterion,
        ResourceType.EVALUATION: NavigationIntent.open_evaluation,
        ResourceType.REPORT: NavigationIntent.open_report,
    }
    metadata = {} if action is None else {"action": action.value}
    return factories[identity.resource_type](
        identity.resource_id,
        origin=origin,
        metadata=metadata,
    )


def _display_value(value) -> str:
    if value is None:
        return "—"
    if isinstance(value, bool):
        return "Sim" if value else "Não"
    return str(value)


__all__ = [
    "MetadataItemView",
    "RelationshipItemView",
    "ResourceActionView",
    "ResourceInspectorState",
    "ResourceInspectorViewData",
    "ResourceInspectorViewModel",
]
