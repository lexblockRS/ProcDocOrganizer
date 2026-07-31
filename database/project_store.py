"""Persistência SQLite direta do Project genérico da plataforma."""

from __future__ import annotations

import json
from pathlib import Path
import sqlite3
from typing import TYPE_CHECKING

from .database import initialize_database

if TYPE_CHECKING:
    from platform_sdk.project import Project, ProjectResource


class ProjectPersistenceError(RuntimeError):
    """Falha ao salvar ou reidratar um Project."""


class ProjectNotFoundError(ProjectPersistenceError):
    """O Project solicitado não existe no armazenamento."""


class SQLiteProjectStore:
    """Armazena Projects sem cache, ORM ou Unit of Work."""

    TABLE = "platform_projects"

    def __init__(self, database_path: str | Path) -> None:
        self.database_path = Path(database_path)
        initialize_database(self.database_path)
        self._connection = sqlite3.connect(self.database_path)
        self._connection.row_factory = sqlite3.Row
        self._connection.execute("PRAGMA foreign_keys = ON")

    def save(self, project: Project) -> None:
        Project, _ProjectResource, _ProjectState = _project_types()
        if not isinstance(project, Project):
            raise TypeError("project deve ser platform_sdk.Project.")
        try:
            self._connection.execute(
                f"""
                INSERT INTO {self.TABLE} (
                    project_id,
                    name,
                    application_id,
                    metadata_json,
                    state,
                    resources_json,
                    revision
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(project_id) DO UPDATE SET
                    name = excluded.name,
                    application_id = excluded.application_id,
                    metadata_json = excluded.metadata_json,
                    state = excluded.state,
                    resources_json = excluded.resources_json,
                    revision = excluded.revision
                """,
                (
                    project.project_id,
                    project.name,
                    project.application_id,
                    _metadata_to_json(project.metadata),
                    project.state.value,
                    _resources_to_json(project.resources),
                    project.revision,
                ),
            )
            self._connection.commit()
        except sqlite3.Error as exc:
            self._connection.rollback()
            raise ProjectPersistenceError(
                "Não foi possível salvar o Project."
            ) from exc

    def get(self, project_id: str) -> Project:
        normalized = _required_text(project_id, "project_id")
        try:
            row = self._connection.execute(
                f"""
                SELECT
                    project_id,
                    name,
                    application_id,
                    metadata_json,
                    state,
                    resources_json,
                    revision
                FROM {self.TABLE}
                WHERE project_id = ?
                """,
                (normalized,),
            ).fetchone()
        except sqlite3.Error as exc:
            raise ProjectPersistenceError(
                "Não foi possível abrir o Project."
            ) from exc
        if row is None:
            raise ProjectNotFoundError(
                f"Project não encontrado: {normalized}."
            )
        try:
            Project, _ProjectResource, ProjectState = _project_types()
            return Project(
                project_id=row["project_id"],
                name=row["name"],
                application_id=row["application_id"],
                metadata=_metadata_from_json(row["metadata_json"]),
                state=ProjectState(row["state"]),
                resources=_resources_from_json(row["resources_json"]),
                revision=row["revision"],
            )
        except (
            KeyError,
            TypeError,
            ValueError,
            json.JSONDecodeError,
        ) as exc:
            raise ProjectPersistenceError(
                "O Project persistido contém dados inválidos."
            ) from exc

    def list_all(self) -> tuple[Project, ...]:
        try:
            rows = self._connection.execute(
                f"SELECT project_id FROM {self.TABLE} ORDER BY project_id"
            ).fetchall()
        except sqlite3.Error as exc:
            raise ProjectPersistenceError(
                "Não foi possível listar Projects."
            ) from exc
        return tuple(self.get(row["project_id"]) for row in rows)

    def close(self) -> None:
        if self._connection is not None:
            self._connection.close()
            self._connection = None

    def __enter__(self) -> "SQLiteProjectStore":
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        self.close()


def _metadata_to_json(metadata) -> str:
    return json.dumps(
        list(metadata),
        ensure_ascii=False,
        separators=(",", ":"),
    )


def _metadata_from_json(payload: str):
    values = json.loads(payload)
    if not isinstance(values, list):
        raise TypeError("metadata persistido deve ser uma lista.")
    if any(
        not isinstance(item, list) or len(item) != 2
        for item in values
    ):
        raise TypeError("metadata persistido contém item inválido.")
    return tuple((item[0], item[1]) for item in values)


def _resources_to_json(resources: tuple[ProjectResource, ...]) -> str:
    return json.dumps(
        [
            {
                "resource_id": resource.resource_id,
                "resource_type": resource.resource_type,
                "reference": resource.reference,
                "metadata": list(resource.metadata),
            }
            for resource in resources
        ],
        ensure_ascii=False,
        separators=(",", ":"),
    )


def _resources_from_json(payload: str) -> tuple[ProjectResource, ...]:
    values = json.loads(payload)
    if not isinstance(values, list):
        raise TypeError("resources persistido deve ser uma lista.")
    _Project, ProjectResource, _ProjectState = _project_types()
    return tuple(
        ProjectResource(
            resource_id=item["resource_id"],
            resource_type=item["resource_type"],
            reference=item["reference"],
            metadata=tuple(
                (metadata[0], metadata[1])
                for metadata in item["metadata"]
            ),
        )
        for item in values
    )


def _required_text(value: object, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} deve ser texto não vazio.")
    return value.strip()


def _project_types():
    """Carrega o modelo somente ao executar o adapter, evitando ciclos."""

    from platform_sdk.project import Project, ProjectResource, ProjectState

    return Project, ProjectResource, ProjectState


__all__ = [
    "ProjectNotFoundError",
    "ProjectPersistenceError",
    "SQLiteProjectStore",
]
