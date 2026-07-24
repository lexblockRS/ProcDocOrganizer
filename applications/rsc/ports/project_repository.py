"""Porta de persistência de Projetos RSC."""

from typing import Protocol

from applications.rsc.models import Project


class ProjectRepository(Protocol):
    """Operações necessárias aos casos de uso atuais de projetos."""

    def add(self, project: Project) -> None: ...

    def get(self, project_id: str) -> Project | None: ...

    def list_all(self) -> tuple[Project, ...]: ...
