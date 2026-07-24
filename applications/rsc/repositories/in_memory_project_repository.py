"""Repositório de Projetos RSC mantido em memória."""

from applications.rsc.models import Project


class InMemoryProjectRepository:
    """Mantém projetos na ordem em que foram adicionados."""

    def __init__(self) -> None:
        self._projects: dict[str, Project] = {}

    def add(self, project: Project) -> None:
        self._projects[project.project_id] = project

    def get(self, project_id: str) -> Project | None:
        return self._projects.get(project_id)

    def list_all(self) -> tuple[Project, ...]:
        return tuple(self._projects.values())
