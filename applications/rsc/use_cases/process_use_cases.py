"""Casos de uso do ciclo inicial do processo RSC."""

from applications.rsc.services import RscProcessService

from ._support import require_command, require_text, require_uuid
from .commands import (
    CreateProcessCommand,
    GetProcessCommand,
    ListProcessesCommand,
)
from .errors import InvalidCommandError, ProcessNotFoundError
from .results import (
    CreateProcessResult,
    GetProcessResult,
    ListProcessesResult,
)


class CreateProcessUseCase:
    def __init__(self, processes: RscProcessService) -> None:
        self._processes = processes

    def execute(self, command: CreateProcessCommand) -> CreateProcessResult:
        require_command(command, CreateProcessCommand)
        applicant_name = require_text(
            command.applicant_name, "applicant_name"
        )
        institution = require_text(command.institution, "institution")
        try:
            process = self._processes.create_process(
                applicant_name=applicant_name,
                institution=institution,
                applicant_identifier=command.applicant_identifier,
            )
        except (TypeError, ValueError) as exc:
            raise InvalidCommandError(str(exc)) from exc
        return CreateProcessResult(
            process_id=process.id,
            created_at=process.created_at,
            process=process,
        )


class GetProcessUseCase:
    def __init__(self, processes: RscProcessService) -> None:
        self._processes = processes

    def execute(self, command: GetProcessCommand) -> GetProcessResult:
        require_command(command, GetProcessCommand)
        process_id = require_uuid(command.process_id, "process_id")
        try:
            process = self._processes.get_process(process_id)
        except KeyError as exc:
            raise ProcessNotFoundError(
                f"processo não encontrado: {process_id}"
            ) from exc
        return GetProcessResult(process_id=process_id, process=process)


class ListProcessesUseCase:
    def __init__(self, processes: RscProcessService) -> None:
        self._processes = processes

    def execute(
        self, command: ListProcessesCommand
    ) -> ListProcessesResult:
        require_command(command, ListProcessesCommand)
        return ListProcessesResult(self._processes.list_processes())
