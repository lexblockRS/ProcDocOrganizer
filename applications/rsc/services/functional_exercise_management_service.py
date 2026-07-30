"""CRUD explícito de FunctionalExercise, sem interpretação normativa."""

from applications.rsc.models import (
    FunctionalAssignmentEvidenceId,
    FunctionalContext,
    FunctionalExercise,
    FunctionalExerciseId,
    FunctionalExerciseStatus,
    FunctionalExerciseType,
    FunctionalPeriod,
    FunctionalRole,
)


class FunctionalExerciseManagementError(ValueError):
    """Falha de validação ou localização de um exercício funcional."""


class FunctionalExerciseManagementService:
    def __init__(self, repository, assignment_evidence_repository) -> None:
        self._repository = repository
        self._assignment_evidence_repository = assignment_evidence_repository

    def update(
        self,
        exercise_id: str,
        *,
        person_id: str,
        exercise_type_code: str,
        exercise_type_label: str,
        role: str,
        context_organization: str,
        start_date,
        end_date=None,
        context_unit=None,
        context_reference=None,
        functional_assignment_evidence_ids=(),
    ) -> FunctionalExercise:
        current = self._require(exercise_id)
        references = self._references(
            functional_assignment_evidence_ids
        )
        try:
            period = FunctionalPeriod(start_date, end_date)
            updated = FunctionalExercise(
                id=current.id,
                person_id=person_id,
                exercise_type=FunctionalExerciseType(
                    exercise_type_code,
                    exercise_type_label,
                ),
                role=FunctionalRole(role),
                context=FunctionalContext(
                    context_organization,
                    context_unit,
                    context_reference,
                ),
                period=period,
                status=(
                    FunctionalExerciseStatus.ACTIVE
                    if period.is_open
                    else FunctionalExerciseStatus.ENDED
                ),
                functional_assignment_evidence_ids=references,
            )
        except (TypeError, ValueError) as exc:
            raise FunctionalExerciseManagementError(str(exc)) from exc
        return self._repository.update(updated)

    def delete(self, exercise_id: str) -> FunctionalExercise:
        identifier = FunctionalExerciseId.from_string(exercise_id)
        deleted = self._repository.delete(identifier)
        if deleted is None:
            raise FunctionalExerciseManagementError(
                "O exercício funcional não foi localizado."
            )
        return deleted

    def _require(self, exercise_id: str) -> FunctionalExercise:
        identifier = FunctionalExerciseId.from_string(exercise_id)
        current = self._repository.get_by_id(identifier)
        if current is None:
            raise FunctionalExerciseManagementError(
                "O exercício funcional não foi localizado."
            )
        return current

    def _references(self, values) -> tuple[FunctionalAssignmentEvidenceId, ...]:
        try:
            references = tuple(
                FunctionalAssignmentEvidenceId.from_string(value)
                for value in values
            )
        except (TypeError, ValueError) as exc:
            raise FunctionalExerciseManagementError(str(exc)) from exc
        if not references:
            raise FunctionalExerciseManagementError(
                "Ao menos uma interpretação funcional é obrigatória."
            )
        if len(set(references)) != len(references):
            raise FunctionalExerciseManagementError(
                "As referências não podem conter duplicidades."
            )
        for reference in references:
            if (
                self._assignment_evidence_repository.get_by_id(reference)
                is None
            ):
                raise FunctionalExerciseManagementError(
                    "Uma interpretação funcional referenciada não existe."
                )
        return references
