"""Serviço em memória para processos RSC."""

from applications.rsc.domain import RscProcess


class RscProcessService:
    def __init__(self) -> None:
        self._processes: dict[str, RscProcess] = {}

    def create_process(self, **values) -> RscProcess:
        process = RscProcess(**values)
        self.add_process(process)
        return process

    def add_process(self, process: RscProcess) -> None:
        if not isinstance(process, RscProcess):
            raise TypeError("process deve ser RscProcess.")
        if process.id in self._processes:
            raise ValueError(f"processo duplicado: {process.id}")
        self._processes[process.id] = process

    def get_process(self, process_id: str) -> RscProcess:
        try:
            return self._processes[process_id]
        except KeyError as exc:
            raise KeyError(f"processo inexistente: {process_id}") from exc

    def list_processes(self) -> tuple[RscProcess, ...]:
        return tuple(self._processes.values())

    def remove_process(self, process_id: str) -> RscProcess:
        try:
            return self._processes.pop(process_id)
        except KeyError as exc:
            raise KeyError(f"processo inexistente: {process_id}") from exc

    def count_processes(self) -> int:
        return len(self._processes)

    def clear(self) -> None:
        self._processes.clear()
