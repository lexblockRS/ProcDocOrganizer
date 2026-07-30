"""Porta de persistência de atividades profissionais."""

from typing import Protocol

from applications.rsc.models import Activity


class ActivityRepository(Protocol):
    """Operações necessárias aos casos de uso atuais de atividades."""

    def add(self, activity: Activity) -> None: ...

    def save(self, activity: Activity) -> None: ...

    def get(self, activity_id: str) -> Activity | None: ...

    def list_all(self) -> tuple[Activity, ...]: ...

    def delete(self, activity_id: str) -> Activity | None: ...
