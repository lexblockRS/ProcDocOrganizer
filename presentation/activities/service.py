"""Construção das projeções de leitura de atividades."""

from applications.rsc.models import ActivityState
from applications.rsc.ports import ActivityRepository

from .projections import (
    ActivitiesProjection,
    ActivitiesViewState,
    ActivityDetailsProjection,
    ActivityListItemProjection,
    RelatedInterpretationProjection,
    RelatedExerciseProjection,
)


class ActivitiesService:
    """Consulta a port e converte o domínio em dados de apresentação."""

    STATE_LABELS = {
        ActivityState.REMEMBERED: "Lembrada",
        ActivityState.UNDER_INVESTIGATION: "Em investigação",
        ActivityState.PARTIALLY_PROVEN: "Parcialmente comprovada",
        ActivityState.PROVEN: "Comprovada",
    }

    def __init__(
        self,
        repository: ActivityRepository,
        project_name: str,
        exercise_repository=None,
        assignment_repository=None,
        evidence_service=None,
    ) -> None:
        self._repository = repository
        self._project_name = project_name
        self._exercise_repository = exercise_repository
        self._assignment_repository = assignment_repository
        self._evidence_service = evidence_service

    def build(
        self,
        selected_activity_id: str | None = None,
    ) -> ActivitiesProjection:
        activities = tuple(self._repository.list_all())
        if not activities:
            return ActivitiesProjection(
                state=ActivitiesViewState.EMPTY,
                project_name=self._project_name,
            )
        identifiers = {item.activity_id for item in activities}
        selected_id = (
            selected_activity_id
            if selected_activity_id in identifiers
            else activities[0].activity_id
        )
        items = tuple(
            self._item(item, item.activity_id == selected_id)
            for item in activities
        )
        selected = next(
            item for item in activities
            if item.activity_id == selected_id
        )
        return ActivitiesProjection(
            state=ActivitiesViewState.READY,
            project_name=self._project_name,
            items=items,
            selected_activity_id=selected_id,
            selected_activity=self._details(selected),
            total=len(activities),
            remembered_count=self._count(
                activities, ActivityState.REMEMBERED
            ),
            investigating_count=self._count(
                activities, ActivityState.UNDER_INVESTIGATION
            ),
            partially_proven_count=self._count(
                activities, ActivityState.PARTIALLY_PROVEN
            ),
            proven_count=self._count(activities, ActivityState.PROVEN),
        )

    @classmethod
    def _item(cls, activity, selected):
        return ActivityListItemProjection(
            activity_id=activity.activity_id,
            description=activity.description,
            state=activity.state.value,
            state_label=cls.STATE_LABELS[activity.state],
            evidence_count=len(
                activity.functional_assignment_evidence_ids
            ),
            exercise_count=len(activity.functional_exercise_ids),
            is_selected=selected,
        )

    def _details(self, activity):
        return ActivityDetailsProjection(
            activity_id=activity.activity_id,
            description=activity.description,
            state=activity.state.value,
            state_label=self.STATE_LABELS[activity.state],
            evidence_ids=tuple(
                str(item)
                for item in activity.functional_assignment_evidence_ids
            ),
            exercise_ids=tuple(
                str(item) for item in activity.functional_exercise_ids
            ),
            evidence_count=len(
                activity.functional_assignment_evidence_ids
            ),
            exercise_count=len(activity.functional_exercise_ids),
            state_options=tuple(
                (state.value, self.STATE_LABELS[state])
                for state in ActivityState
            ),
            related_interpretations=self._related(activity),
            related_exercises=self._related_exercises(activity),
        )

    def _related_exercises(self, activity):
        result = []
        for exercise_id in activity.functional_exercise_ids:
            exercise = (
                self._exercise_repository.get_by_id(exercise_id)
                if self._exercise_repository is not None else None
            )
            if exercise is None:
                result.append(RelatedExerciseProjection(
                    exercise_id=str(exercise_id),
                    available=False,
                    unavailable_reason=(
                        "Exercício funcional referenciado não pôde "
                        "ser localizado."
                    ),
                ))
                continue
            end = (
                exercise.period.end_date.isoformat()
                if exercise.period.end_date else "aberto"
            )
            result.append(RelatedExerciseProjection(
                exercise_id=str(exercise.id),
                available=True,
                person_id=exercise.person_id,
                role=exercise.role.name,
                organization=exercise.context.organization,
                unit=exercise.context.unit,
                period=(
                    f"{exercise.period.start_date.isoformat()} a {end}"
                ),
                status=exercise.status.value,
                assignment_count=len(
                    exercise.functional_assignment_evidence_ids
                ),
            ))
        return tuple(result)

    def _related(self, activity):
        assignment_to_exercise = {
            str(item): None
            for item in activity.functional_assignment_evidence_ids
        }
        if self._exercise_repository is not None:
            for exercise_id in activity.functional_exercise_ids:
                exercise = self._exercise_repository.get_by_id(exercise_id)
                if exercise is not None:
                    for assignment_id in (
                        exercise.functional_assignment_evidence_ids
                    ):
                        assignment_to_exercise.setdefault(
                            str(assignment_id), str(exercise_id)
                        )
        result = []
        for assignment_id, exercise_id in assignment_to_exercise.items():
            from applications.rsc.models import (
                FunctionalAssignmentEvidenceId,
            )
            assignment = (
                self._assignment_repository.get_by_id(
                    FunctionalAssignmentEvidenceId.from_string(assignment_id)
                )
                if self._assignment_repository is not None else None
            )
            if assignment is None:
                result.append(RelatedInterpretationProjection(
                    assignment_id=assignment_id,
                    exercise_id=exercise_id,
                    person_id="Indisponível",
                    role="Interpretação funcional indisponível",
                    evidence_id="Indisponível",
                    document_identity=None,
                    page_number=None,
                    snippet=None,
                    source_available=False,
                    assignment_available=False,
                    evidence_available=False,
                    document_available=False,
                    unavailable_reason=(
                        "Interpretação funcional referenciada não pôde "
                        "ser localizada."
                    ),
                ))
                continue
            evidence_id = str(assignment.source_evidence_reference)
            evidence = (
                self._evidence_service.get(evidence_id)
                if self._evidence_service is not None else None
            )
            document_available = (
                self._evidence_service.is_document_available(
                    evidence.document_identity
                )
                if evidence is not None
                and self._evidence_service is not None else False
            )
            result.append(RelatedInterpretationProjection(
                assignment_id=assignment_id,
                exercise_id=exercise_id,
                person_id=assignment.person_id,
                role=assignment.role,
                evidence_id=evidence_id,
                document_identity=(
                    evidence.document_identity if evidence else None
                ),
                page_number=evidence.page_number if evidence else None,
                snippet=evidence.source_snippet if evidence else None,
                source_available=(
                    evidence is not None and document_available
                ),
                evidence_available=evidence is not None,
                document_available=document_available,
                unavailable_reason=(
                    None
                    if evidence is not None and document_available
                    else (
                        "Documento de origem não está mais disponível "
                        "no acervo."
                        if evidence is not None
                        else "Evidence de origem removida ou inacessível."
                    )
                ),
            ))
        return tuple(result)

    @staticmethod
    def _count(activities, state):
        return sum(item.state is state for item in activities)
