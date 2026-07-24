"""Serviço do caso de uso CreateActivity."""

from uuid import uuid4

from applications.rsc.commands import CreateActivityCommand
from applications.rsc.dto import ActivityDTO
from applications.rsc.models import Activity
from applications.rsc.ports import ActivityRepository


class CreateActivityService:
    """Orquestra a criação de uma atividade profissional."""

    def __init__(self, repository: ActivityRepository) -> None:
        self._repository = repository

    def execute(
        self,
        command: CreateActivityCommand,
    ) -> ActivityDTO:
        if not isinstance(command.description, str):
            raise TypeError("description deve ser uma string.")

        description = command.description.strip()
        if not description:
            raise ValueError("description não pode ser vazia.")

        activity = Activity(
            activity_id=str(uuid4()),
            description=description,
            state=Activity.INITIAL_STATE,
        )
        self._repository.add(activity)

        return ActivityDTO(
            activity_id=activity.activity_id,
            description=activity.description,
            state=activity.state,
        )
