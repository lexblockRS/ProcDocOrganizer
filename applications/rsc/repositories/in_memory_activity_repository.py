"""Repositório de atividades mantido em memória."""

from applications.rsc.models import Activity


class InMemoryActivityRepository:
    """Mantém atividades na ordem em que foram adicionadas."""

    def __init__(self) -> None:
        self._activities: dict[str, Activity] = {}

    def add(self, activity: Activity) -> None:
        self._activities[activity.activity_id] = activity

    def get(self, activity_id: str) -> Activity | None:
        return self._activities.get(activity_id)

    def list_all(self) -> tuple[Activity, ...]:
        return tuple(self._activities.values())
