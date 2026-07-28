"""Casos de uso de atividades normativas do processo RSC."""

from applications.rsc.services import (
    RscActivityService,
    RscProcessService,
)

from ._support import require_command, require_text, require_uuid
from .commands import (
    CreateActivityCommand,
    GetActivityCommand,
    ListActivitiesByCriterionCommand,
    ListActivitiesByRequirementCommand,
    ListActivitiesCommand,
)
from .errors import (
    ActivityNotFoundError,
    DomainValidationError,
    ProcessNotFoundError,
)
from .results import (
    CreateActivityResult,
    GetActivityResult,
    ListActivitiesResult,
)


class _ActivityUseCase:
    def __init__(
        self,
        processes: RscProcessService,
        activities: RscActivityService,
    ) -> None:
        self._processes = processes
        self._activities = activities

    def _get_process(self, process_id: str):
        normalized = require_uuid(process_id, "process_id")
        try:
            return self._processes.get_process(normalized)
        except KeyError as exc:
            raise ProcessNotFoundError(
                f"processo não encontrado: {normalized}"
            ) from exc

    def _get_activity(self, process, activity_id: str):
        normalized = require_uuid(activity_id, "activity_id")
        try:
            return self._activities.get_activity(process, normalized)
        except KeyError as exc:
            raise ActivityNotFoundError(
                f"atividade não encontrada: {normalized}"
            ) from exc


class CreateActivityUseCase(_ActivityUseCase):
    def execute(
        self, command: CreateActivityCommand
    ) -> CreateActivityResult:
        require_command(command, CreateActivityCommand)
        process = self._get_process(command.process_id)
        title = require_text(command.title, "title")
        try:
            activity = self._activities.create_activity(
                criterion_id=command.criterion_id,
                title=title,
                quantity=command.quantity,
                description=command.description,
                score_variant_id=command.score_variant_id,
                start_date=command.start_date,
                end_date=command.end_date,
                notes=command.notes,
            )
            self._activities.add_activity(process, activity)
        except (KeyError, TypeError, ValueError) as exc:
            raise DomainValidationError(str(exc)) from exc
        return CreateActivityResult(
            process_id=process.id,
            activity_id=activity.id,
            created_at=activity.created_at,
            activity=activity,
        )


class GetActivityUseCase(_ActivityUseCase):
    def execute(self, command: GetActivityCommand) -> GetActivityResult:
        require_command(command, GetActivityCommand)
        process = self._get_process(command.process_id)
        activity = self._get_activity(process, command.activity_id)
        return GetActivityResult(process.id, activity.id, activity)


class ListActivitiesUseCase(_ActivityUseCase):
    def execute(
        self, command: ListActivitiesCommand
    ) -> ListActivitiesResult:
        require_command(command, ListActivitiesCommand)
        process = self._get_process(command.process_id)
        return ListActivitiesResult(
            process.id, self._activities.list_activities(process)
        )


class ListActivitiesByCriterionUseCase(_ActivityUseCase):
    def execute(
        self, command: ListActivitiesByCriterionCommand
    ) -> ListActivitiesResult:
        require_command(command, ListActivitiesByCriterionCommand)
        process = self._get_process(command.process_id)
        try:
            activities = self._activities.list_activities_by_criterion(
                process, command.criterion_id
            )
        except KeyError as exc:
            raise DomainValidationError(str(exc)) from exc
        return ListActivitiesResult(process.id, activities)

class ListActivitiesByRequirementUseCase(_ActivityUseCase):
    def execute(
        self, command: ListActivitiesByRequirementCommand
    ) -> ListActivitiesResult:
        require_command(command, ListActivitiesByRequirementCommand)
        process = self._get_process(command.process_id)
        try:
            activities = self._activities.list_activities_by_requirement(
                process, command.requirement_id
            )
        except KeyError as exc:
            raise DomainValidationError(str(exc)) from exc
        return ListActivitiesResult(process.id, activities)
