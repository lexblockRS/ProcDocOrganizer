"""Serviço do caso de uso CreateProject."""

from uuid import uuid4

from applications.rsc.commands import CreateProjectCommand
from applications.rsc.dto import ProjectDTO
from applications.rsc.models import Project
from applications.rsc.ports import ProjectRepository


class CreateProjectService:
    """Orquestra a criação de um Projeto RSC."""

    def __init__(self, repository: ProjectRepository) -> None:
        self._repository = repository

    def execute(
        self,
        command: CreateProjectCommand,
    ) -> ProjectDTO:
        if not isinstance(command.title, str):
            raise TypeError("title deve ser uma string.")

        title = command.title.strip()
        if not title:
            raise ValueError("title não pode ser vazio.")

        project = Project(
            project_id=str(uuid4()),
            title=title,
            status=Project.INITIAL_STATUS,
        )
        self._repository.add(project)

        return ProjectDTO(
            project_id=project.project_id,
            title=project.title,
            status=project.status,
        )
