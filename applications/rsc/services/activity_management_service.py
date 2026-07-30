"""Gestão factual de Activity, sem enquadramento ou regras normativas."""

from uuid import uuid4

from applications.rsc.models import (
    Activity,
    ActivityState,
    FunctionalExerciseId,
)
from applications.rsc.ports import (
    ActivityRepository,
    FunctionalExerciseRepository,
)


class ActivityManagementError(ValueError):
    """Falha de validação ou localização no CRUD factual."""


class ActivityManagementService:
    """Coordena criação, edição e exclusão no repository de Activity."""

    def __init__(
        self,
        repository: ActivityRepository,
        functional_exercise_repository:
            FunctionalExerciseRepository | None = None,
    ) -> None:
        self._repository = repository
        self._functional_exercise_repository = (
            functional_exercise_repository
        )

    def create(
        self,
        description: str,
        functional_exercise_ids=(),
    ) -> Activity:
        try:
            exercise_ids = self._exercise_ids(
                functional_exercise_ids,
                required=(
                    self._functional_exercise_repository is not None
                ),
            )
            activity = Activity(
                str(uuid4()),
                description,
                functional_exercise_ids=exercise_ids,
            )
        except (TypeError, ValueError) as exc:
            raise ActivityManagementError(str(exc)) from exc
        self._repository.add(activity)
        return activity

    def update_description(
        self,
        activity_id: str,
        description: str,
    ) -> Activity:
        activity = self._require(activity_id)
        return self.update(
            activity_id,
            description,
            activity.state,
        )

    def update(
        self,
        activity_id: str,
        description: str,
        state: ActivityState | str,
    ) -> Activity:
        activity = self._require(activity_id)
        try:
            target_state = (
                state
                if isinstance(state, ActivityState)
                else ActivityState(state)
            )
            updated = activity.update_description(description)
            updated = self._transition(updated, target_state)
        except (TypeError, ValueError) as exc:
            raise ActivityManagementError(str(exc)) from exc
        self._repository.save(updated)
        return updated

    def update_exercises(
        self,
        activity_id: str,
        functional_exercise_ids,
    ) -> Activity:
        activity = self._require(activity_id)
        exercise_ids = self._exercise_ids(
            functional_exercise_ids,
            required=True,
        )
        try:
            updated = Activity(
                activity_id=activity.activity_id,
                description=activity.description,
                state=activity.state,
                functional_assignment_evidence_ids=(
                    activity.functional_assignment_evidence_ids
                ),
                functional_exercise_ids=exercise_ids,
            )
        except (TypeError, ValueError) as exc:
            raise ActivityManagementError(str(exc)) from exc
        self._repository.save(updated)
        return updated

    def delete(self, activity_id: str) -> Activity:
        activity = self._repository.delete(activity_id)
        if activity is None:
            raise ActivityManagementError(
                "A Activity selecionada não foi localizada."
            )
        return activity

    def _require(self, activity_id: str) -> Activity:
        activity = self._repository.get(activity_id)
        if activity is None:
            raise ActivityManagementError(
                "A Activity selecionada não foi localizada."
            )
        return activity

    def _exercise_ids(self, values, *, required):
        try:
            identifiers = tuple(
                FunctionalExerciseId.from_string(value)
                for value in values
            )
        except (TypeError, ValueError) as exc:
            raise ActivityManagementError(str(exc)) from exc
        if required and not identifiers:
            raise ActivityManagementError(
                "A Activity exige ao menos um FunctionalExercise."
            )
        if len(set(identifiers)) != len(identifiers):
            raise ActivityManagementError(
                "Referências de FunctionalExercise não podem se repetir."
            )
        if self._functional_exercise_repository is not None:
            for identifier in identifiers:
                if (
                    self._functional_exercise_repository.get_by_id(identifier)
                    is None
                ):
                    raise ActivityManagementError(
                        "Um FunctionalExercise referenciado não existe."
                    )
        return identifiers

    @staticmethod
    def _transition(
        activity: Activity,
        target: ActivityState,
    ) -> Activity:
        if target is activity.state:
            return activity
        transitions = {
            ActivityState.REMEMBERED: (
                ActivityState.UNDER_INVESTIGATION,
                activity.start_investigation,
            ),
            ActivityState.UNDER_INVESTIGATION: (
                ActivityState.PARTIALLY_PROVEN,
                activity.mark_partially_proven,
            ),
            ActivityState.PARTIALLY_PROVEN: (
                ActivityState.PROVEN,
                activity.mark_proven,
            ),
        }
        transition = transitions.get(activity.state)
        if transition is None or transition[0] is not target:
            raise ActivityManagementError(
                "A alteração de estado deve respeitar o ciclo sequencial "
                "da Activity."
            )
        return transition[1]()
