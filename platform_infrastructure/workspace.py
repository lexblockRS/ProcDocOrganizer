"""Ambiente físico opcional de um Project da plataforma."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
import shutil
from tempfile import mkdtemp

from platform_sdk.project import Project


class WorkspaceError(RuntimeError):
    """Operação física inválida sobre um Workspace."""


class WorkspaceDirectory(str, Enum):
    DOCUMENTS = "documents"
    EXPORTS = "exports"
    CACHE = "cache"
    TEMP = "temp"
    SETTINGS = "settings"
    LOGS = "logs"
    THUMBNAILS = "thumbnails"
    ATTACHMENTS = "attachments"


@dataclass(frozen=True, slots=True)
class Workspace:
    """Associação entre um Project e sua raiz física."""

    project: Project
    root: Path
    temporary: bool = False

    def __post_init__(self) -> None:
        if not isinstance(self.project, Project):
            raise TypeError("project deve ser platform_sdk.Project.")
        if not isinstance(self.root, Path):
            raise TypeError("root deve ser pathlib.Path.")
        object.__setattr__(self, "root", self.root.resolve())
        if not isinstance(self.temporary, bool):
            raise TypeError("temporary deve ser bool.")

    @property
    def aggregate_id(self) -> str:
        return self.project.aggregate_id

    @property
    def exists(self) -> bool:
        return self.root.is_dir()

    @property
    def documents(self) -> Path:
        return self.path(WorkspaceDirectory.DOCUMENTS)

    @property
    def exports(self) -> Path:
        return self.path(WorkspaceDirectory.EXPORTS)

    @property
    def cache(self) -> Path:
        return self.path(WorkspaceDirectory.CACHE)

    @property
    def temp(self) -> Path:
        return self.path(WorkspaceDirectory.TEMP)

    @property
    def settings(self) -> Path:
        return self.path(WorkspaceDirectory.SETTINGS)

    @property
    def logs(self) -> Path:
        return self.path(WorkspaceDirectory.LOGS)

    @property
    def thumbnails(self) -> Path:
        return self.path(WorkspaceDirectory.THUMBNAILS)

    @property
    def attachments(self) -> Path:
        return self.path(WorkspaceDirectory.ATTACHMENTS)

    def path(self, directory: WorkspaceDirectory) -> Path:
        if not isinstance(directory, WorkspaceDirectory):
            raise TypeError("directory deve ser WorkspaceDirectory.")
        return self.root / directory.value

    def ensure(self, directory: WorkspaceDirectory) -> Path:
        if not self.exists:
            raise WorkspaceError("A raiz do Workspace não existe.")
        destination = self.path(directory)
        destination.mkdir(exist_ok=True)
        return destination

    def existing_directories(self) -> tuple[WorkspaceDirectory, ...]:
        return tuple(
            directory
            for directory in WorkspaceDirectory
            if self.path(directory).is_dir()
        )

    def delete_temporary(self) -> None:
        if not self.temporary:
            raise WorkspaceError(
                "Somente Workspaces temporários podem ser excluídos."
            )
        if self.root.exists():
            shutil.rmtree(self.root)


class WorkspaceLocator:
    """Deriva e localiza raízes sem criar diretórios."""

    def __init__(self, base_directory: str | Path) -> None:
        self.base_directory = Path(base_directory).resolve()

    def path_for(self, project: Project) -> Path:
        if not isinstance(project, Project):
            raise TypeError("project deve ser platform_sdk.Project.")
        return self.base_directory / project.aggregate_id

    def locate(self, project: Project) -> Workspace | None:
        root = self.path_for(project)
        if not root.is_dir():
            return None
        return Workspace(project=project, root=root)


class WorkspaceFactory:
    """Cria somente a raiz; diretórios internos permanecem opcionais."""

    def __init__(self, base_directory: str | Path) -> None:
        self.locator = WorkspaceLocator(base_directory)

    def create(self, project: Project) -> Workspace:
        root = self.locator.path_for(project)
        try:
            root.mkdir(parents=True, exist_ok=False)
        except FileExistsError as exc:
            raise WorkspaceError("O Workspace já existe.") from exc
        return Workspace(project=project, root=root)

    def create_temporary(self, project: Project) -> Workspace:
        if not isinstance(project, Project):
            raise TypeError("project deve ser platform_sdk.Project.")
        root = Path(mkdtemp(prefix="procdoc-workspace-")).resolve()
        return Workspace(project=project, root=root, temporary=True)


__all__ = [
    "Workspace",
    "WorkspaceDirectory",
    "WorkspaceError",
    "WorkspaceFactory",
    "WorkspaceLocator",
]
