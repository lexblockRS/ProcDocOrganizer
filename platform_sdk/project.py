"""Aggregate Root genérico de projeto hospedado pela plataforma."""

from __future__ import annotations

from dataclasses import dataclass, replace
from enum import Enum
from uuid import UUID, uuid4


Metadata = tuple[tuple[str, str | int | bool | None], ...]


class ProjectError(ValueError):
    """Uma operação viola as invariantes do Project."""


class ProjectState(str, Enum):
    DRAFT = "DRAFT"
    ACTIVE = "ACTIVE"
    SUSPENDED = "SUSPENDED"
    ARCHIVED = "ARCHIVED"


@dataclass(frozen=True, slots=True)
class ProjectResource:
    """Referência opaca a um recurso pertencente ao Project."""

    resource_id: str
    resource_type: str
    reference: str
    metadata: Metadata = ()

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "resource_id", _required_text(self.resource_id, "resource_id")
        )
        object.__setattr__(
            self,
            "resource_type",
            _required_text(self.resource_type, "resource_type"),
        )
        object.__setattr__(
            self, "reference", _required_text(self.reference, "reference")
        )
        object.__setattr__(
            self, "metadata", _validated_metadata(self.metadata)
        )


@dataclass(frozen=True, slots=True, eq=False)
class Project:
    """Identidade e ciclo de vida de qualquer projeto da plataforma."""

    project_id: str
    name: str
    application_id: str
    metadata: Metadata = ()
    state: ProjectState = ProjectState.DRAFT
    resources: tuple[ProjectResource, ...] = ()
    revision: int = 0

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "project_id", _normalized_uuid(self.project_id)
        )
        object.__setattr__(self, "name", _required_text(self.name, "name"))
        object.__setattr__(
            self,
            "application_id",
            _required_text(self.application_id, "application_id"),
        )
        object.__setattr__(
            self, "metadata", _validated_metadata(self.metadata)
        )
        if not isinstance(self.state, ProjectState):
            raise TypeError("state deve ser ProjectState.")
        if not isinstance(self.resources, tuple) or any(
            not isinstance(item, ProjectResource) for item in self.resources
        ):
            raise TypeError(
                "resources deve ser uma tupla de ProjectResource."
            )
        resource_ids = tuple(item.resource_id for item in self.resources)
        if len(resource_ids) != len(set(resource_ids)):
            raise ProjectError("Project não aceita recursos duplicados.")
        if (
            isinstance(self.revision, bool)
            or not isinstance(self.revision, int)
            or self.revision < 0
        ):
            raise ValueError("revision deve ser um inteiro não negativo.")

    @classmethod
    def create(
        cls,
        *,
        name: str,
        application_id: str,
        project_id: str | None = None,
        metadata: Metadata = (),
    ) -> "Project":
        return cls(
            project_id=project_id or str(uuid4()),
            name=name,
            application_id=application_id,
            metadata=metadata,
        )

    @property
    def aggregate_id(self) -> str:
        return self.project_id

    def same_project(self, other: object) -> bool:
        return (
            isinstance(other, Project)
            and self.project_id == other.project_id
        )

    def rename(self, name: str) -> "Project":
        self._require_not_archived()
        normalized = _required_text(name, "name")
        if normalized == self.name:
            return self
        return replace(
            self, name=normalized, revision=self.revision + 1
        )

    def change_state(self, target: ProjectState) -> "Project":
        if not isinstance(target, ProjectState):
            raise TypeError("target deve ser ProjectState.")
        if target is self.state:
            return self
        allowed = {
            ProjectState.DRAFT: {
                ProjectState.ACTIVE,
                ProjectState.ARCHIVED,
            },
            ProjectState.ACTIVE: {
                ProjectState.SUSPENDED,
                ProjectState.ARCHIVED,
            },
            ProjectState.SUSPENDED: {
                ProjectState.ACTIVE,
                ProjectState.ARCHIVED,
            },
            ProjectState.ARCHIVED: set(),
        }
        if target not in allowed[self.state]:
            raise ProjectError(
                f"Transição inválida: {self.state.value} → {target.value}."
            )
        return replace(
            self, state=target, revision=self.revision + 1
        )

    def add_resource(self, resource: ProjectResource) -> "Project":
        self._require_not_archived()
        if not isinstance(resource, ProjectResource):
            raise TypeError("resource deve ser ProjectResource.")
        if any(
            item.resource_id == resource.resource_id
            for item in self.resources
        ):
            raise ProjectError("Recurso já associado ao Project.")
        return replace(
            self,
            resources=(*self.resources, resource),
            revision=self.revision + 1,
        )

    def remove_resource(self, resource_id: str) -> "Project":
        self._require_not_archived()
        normalized = _required_text(resource_id, "resource_id")
        if not any(
            item.resource_id == normalized for item in self.resources
        ):
            raise KeyError(normalized)
        return replace(
            self,
            resources=tuple(
                item
                for item in self.resources
                if item.resource_id != normalized
            ),
            revision=self.revision + 1,
        )

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Project):
            return NotImplemented
        return self.project_id == other.project_id

    def __hash__(self) -> int:
        return hash(self.project_id)

    def _require_not_archived(self) -> None:
        if self.state is ProjectState.ARCHIVED:
            raise ProjectError("Project arquivado não pode ser alterado.")


def _required_text(value: object, field_name: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{field_name} deve ser uma string.")
    normalized = " ".join(value.split())
    if not normalized:
        raise ValueError(f"{field_name} não pode ser vazio.")
    return normalized


def _normalized_uuid(value: object) -> str:
    if not isinstance(value, str):
        raise TypeError("project_id deve ser uma string.")
    try:
        return str(UUID(value.strip()))
    except (ValueError, AttributeError) as exc:
        raise ValueError("project_id deve ser um UUID válido.") from exc


def _validated_metadata(value: object) -> Metadata:
    if not isinstance(value, tuple):
        raise TypeError("metadata deve ser uma tupla.")
    normalized: list[tuple[str, str | int | bool | None]] = []
    for item in value:
        if (
            not isinstance(item, tuple)
            or len(item) != 2
            or not isinstance(item[0], str)
            or not item[0].strip()
            or not isinstance(item[1], (str, int, bool, type(None)))
        ):
            raise TypeError(
                "metadata deve conter pares de chave e valor escalar."
            )
        normalized.append((item[0].strip(), item[1]))
    keys = tuple(key for key, _ in normalized)
    if len(keys) != len(set(keys)):
        raise ProjectError("metadata não aceita chaves duplicadas.")
    return tuple(normalized)


__all__ = [
    "Metadata",
    "Project",
    "ProjectError",
    "ProjectResource",
    "ProjectState",
]
