"""Contrato e projetores iniciais do Resource Presentation Model."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from .resources import (
    PresentationAction,
    Resource,
    ResourceContractError,
    ResourceDisplay,
    ResourceIdentity,
    ResourceType,
)
from .workspace import WorkspaceSnapshot


@runtime_checkable
class ProjectionService(Protocol):
    """Porta comum, independente de toolkit, para projetar Resources."""

    def project(
        self,
        resource_identity: ResourceIdentity,
        workspace_snapshot: WorkspaceSnapshot,
    ) -> Resource: ...


class _TypedResourceProjector:
    resource_type: ResourceType

    def project(
        self,
        resource_identity: ResourceIdentity,
        workspace_snapshot: WorkspaceSnapshot,
    ) -> Resource:
        if not isinstance(resource_identity, ResourceIdentity):
            raise TypeError(
                "resource_identity deve ser ResourceIdentity."
            )
        if not isinstance(workspace_snapshot, WorkspaceSnapshot):
            raise TypeError(
                "workspace_snapshot deve ser WorkspaceSnapshot."
            )
        if resource_identity.resource_type is not self.resource_type:
            raise ResourceContractError(
                f"Projetor {self.resource_type.value} não aceita "
                f"{resource_identity.resource_type.value}."
            )
        return Resource(
            identity=resource_identity,
            display=ResourceDisplay(resource_identity.resource_id),
            available_actions=(PresentationAction.OPEN,),
        )


class DocumentResourceProjector(_TypedResourceProjector):
    """Projeção neutra inicial de uma identidade Document."""

    resource_type = ResourceType.DOCUMENT


class EvidenceResourceProjector(_TypedResourceProjector):
    """Projeção neutra inicial de uma identidade Evidence."""

    resource_type = ResourceType.EVIDENCE


class RequirementResourceProjector(_TypedResourceProjector):
    """Projeção neutra inicial de uma identidade Requirement."""

    resource_type = ResourceType.REQUIREMENT


__all__ = [
    "DocumentResourceProjector",
    "EvidenceResourceProjector",
    "ProjectionService",
    "RequirementResourceProjector",
]
