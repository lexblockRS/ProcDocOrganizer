"""Coordenação de atividades normativas contra o catálogo oficial."""

from applications.rsc.catalogs import OfficialRscCatalog
from applications.rsc.domain import RscActivity, RscProcess


class RscActivityService:
    def __init__(self, catalog: OfficialRscCatalog) -> None:
        self._catalog = catalog

    def create_activity(self, **values) -> RscActivity:
        activity = RscActivity(**values)
        self._validate_criterion(activity)
        return activity

    def add_activity(
        self, process: RscProcess, activity: RscActivity
    ) -> RscActivity:
        self._validate_criterion(activity)
        process.add_activity(activity)
        return activity

    def update_activity(
        self, process: RscProcess, activity: RscActivity
    ) -> RscActivity:
        self._validate_criterion(activity)
        process.update_activity(activity)
        return activity

    def remove_activity(
        self, process: RscProcess, activity_id: str
    ) -> RscActivity:
        return process.remove_activity(activity_id)

    def list_activities(
        self, process: RscProcess
    ) -> tuple[RscActivity, ...]:
        return process.list_activities()

    def get_activity(
        self, process: RscProcess, activity_id: str
    ) -> RscActivity:
        return process.get_activity(activity_id)

    def list_activities_by_criterion(
        self, process: RscProcess, criterion_id: str
    ) -> tuple[RscActivity, ...]:
        self._catalog.get_criterion(criterion_id)
        return tuple(
            activity
            for activity in process.list_activities()
            if activity.criterion_id == criterion_id
        )

    def list_activities_by_requirement(
        self, process: RscProcess, requirement_id: str
    ) -> tuple[RscActivity, ...]:
        criterion_ids = {
            criterion.id
            for criterion in self._catalog.list_criteria_by_requirement(
                requirement_id
            )
        }
        return tuple(
            activity
            for activity in process.list_activities()
            if activity.criterion_id in criterion_ids
        )

    def _validate_criterion(self, activity: RscActivity) -> None:
        criterion = self._catalog.get_criterion(activity.criterion_id)
        if criterion.score_variants:
            if activity.score_variant_id is None:
                raise ValueError("critério exige score_variant_id.")
            criterion.get_variant(activity.score_variant_id)
        elif activity.score_variant_id is not None:
            raise ValueError("critério comum não aceita score_variant_id.")
