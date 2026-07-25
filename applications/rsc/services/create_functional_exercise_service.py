"""Serviço do caso de uso CreateFunctionalExercise."""

from applications.rsc.assemblers import ManualFunctionalExerciseAssembler
from applications.rsc.commands import CreateFunctionalExerciseCommand
from applications.rsc.dto import FunctionalExerciseDTO
from applications.rsc.models import FunctionalExercise
from applications.rsc.ports import FunctionalExerciseRepository


class CreateFunctionalExerciseService:
    """Orquestra a criação de um exercício funcional."""

    def __init__(
        self,
        repository: FunctionalExerciseRepository,
        assembler: ManualFunctionalExerciseAssembler,
    ) -> None:
        self._repository = repository
        self._assembler = assembler

    def execute(
        self,
        command: CreateFunctionalExerciseCommand,
    ) -> FunctionalExerciseDTO:
        exercise = self._assembler.assemble(command)
        self._repository.save(exercise)
        return self._to_dto(exercise)

    @staticmethod
    def _to_dto(
        exercise: FunctionalExercise,
    ) -> FunctionalExerciseDTO:
        return FunctionalExerciseDTO(
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
