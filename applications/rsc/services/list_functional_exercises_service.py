"""Serviço de consulta dos exercícios funcionais existentes."""

from applications.rsc.dto import FunctionalExerciseDTO
from applications.rsc.ports import FunctionalExerciseRepository


class ListFunctionalExercisesService:
    """Projeta os exercícios do repository em DTOs de leitura."""

    def __init__(
        self,
        repository: FunctionalExerciseRepository,
    ) -> None:
        self._repository = repository

    def execute(self) -> tuple[FunctionalExerciseDTO, ...]:
        return tuple(
            FunctionalExerciseDTO(
                id=str(exercise.id),
                person_id=exercise.person_id,
                exercise_type_code=exercise.exercise_type.code,
                exercise_type_label=exercise.exercise_type.label,
                role=exercise.role.name,
                context_organization=exercise.context.organization,
                context_unit=exercise.context.unit,
                context_reference=exercise.context.reference,
                start_date=exercise.period.start_date,
                end_date=exercise.period.end_date,
                status=exercise.status.value,
            )
            for exercise in self._repository.list_all()
        )
