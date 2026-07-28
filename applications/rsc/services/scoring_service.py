"""Cálculo puro e determinístico da pontuação declarada."""

from datetime import datetime, timezone
from decimal import Decimal

from applications.rsc.catalogs import OfficialRscCatalog
from applications.rsc.domain import (
    ActivityScore,
    ActivityStatus,
    RequirementScore,
    RscActivity,
    RscProcess,
    RscScoreResult,
)


class RscScoringService:
    def __init__(self, catalog: OfficialRscCatalog) -> None:
        self._catalog = catalog

    def calculate_activity(self, activity: RscActivity) -> ActivityScore:
        criterion = self._catalog.get_criterion(activity.criterion_id)
        if criterion.score_variants:
            if activity.score_variant_id is None:
                raise ValueError("critério exige score_variant_id.")
            points = criterion.get_variant(
                activity.score_variant_id
            ).points_per_unit
        else:
            if activity.score_variant_id is not None:
                raise ValueError("critério comum não aceita score_variant_id.")
            points = criterion.points_per_unit
        raw = activity.quantity * points
        excluded = activity.status is ActivityStatus.EXCLUDED
        return ActivityScore(
            activity_id=activity.id,
            criterion_id=activity.criterion_id,
            quantity=activity.quantity,
            points_per_unit=points,
            raw_score=raw,
            applied_score=Decimal("0") if excluded else raw,
            warnings=("Atividade excluída.",) if excluded else (),
        )

    def calculate_requirement(
        self, process: RscProcess, requirement_id: str
    ) -> RequirementScore:
        self._catalog.get_requirement(requirement_id)
        scores = tuple(
            self.calculate_activity(activity)
            for activity in process.list_activities()
            if self._catalog.get_criterion(
                activity.criterion_id
            ).requirement_id == requirement_id
            and activity.status is not ActivityStatus.EXCLUDED
        )
        return RequirementScore(
            requirement_id=requirement_id,
            activity_scores=scores,
            total_score=sum(
                (score.applied_score for score in scores), Decimal("0")
            ),
        )

    def calculate_process(self, process: RscProcess) -> RscScoreResult:
        requirements = tuple(
            self.calculate_requirement(process, requirement.id)
            for requirement in self._catalog.list_requirements()
        )
        return RscScoreResult(
            process_id=process.id,
            requirement_scores=requirements,
            total_score=sum(
                (item.total_score for item in requirements), Decimal("0")
            ),
            warnings=tuple(
                warning
                for item in requirements
                for score in item.activity_scores
                for warning in score.warnings
            ),
            calculated_at=datetime.now(timezone.utc),
        )
