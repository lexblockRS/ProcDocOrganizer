"""Serviço do caso de uso CreateActivity."""

from uuid import uuid4

from applications.rsc.commands import CreateActivityCommand
from applications.rsc.dto import ActivityDTO
from applications.rsc.models import (
    Activity,
    FunctionalAssignmentEvidenceId,
    FunctionalExerciseId,
)
from applications.rsc.ports import (
    ActivityRepository,
    FunctionalAssignmentEvidenceRepository,
    FunctionalExerciseRepository,
)


class CreateActivityService:
    """Orquestra a criação de uma atividade profissional."""

    def __init__(
        self,
        repository: ActivityRepository,
        functional_assignment_evidence_repository:
            FunctionalAssignmentEvidenceRepository | None = None,
        functional_exercise_repository:
            FunctionalExerciseRepository | None = None,
    ) -> None:
        self._repository = repository
        self._assignment_repository = (
            functional_assignment_evidence_repository
        )
        self._exercise_repository = functional_exercise_repository

    def execute(
        self,
        command: CreateActivityCommand,
    ) -> ActivityDTO:
        if not isinstance(command.description, str):
            raise TypeError("description deve ser uma string.")

        description = command.description.strip()
        if not description:
            raise ValueError("description não pode ser vazia.")

        evidence_ids = tuple(
            FunctionalAssignmentEvidenceId.from_string(item)
            for item in command.functional_assignment_evidence_ids
        )
        exercise_ids = tuple(
            FunctionalExerciseId.from_string(item)
            for item in command.functional_exercise_ids
        )
        if len(set(evidence_ids)) != len(evidence_ids):
            raise ValueError("Referências de interpretações duplicadas.")
        if len(set(exercise_ids)) != len(exercise_ids):
            raise ValueError("Referências de exercícios duplicadas.")
        if self._assignment_repository is not None:
            for item in evidence_ids:
                if self._assignment_repository.get_by_id(item) is None:
                    raise LookupError(
                        f"Interpretação funcional não encontrada: {item}."
                    )
        if self._exercise_repository is not None:
            for item in exercise_ids:
                if self._exercise_repository.get_by_id(item) is None:
                    raise LookupError(
                        f"Exercício funcional não encontrado: {item}."
                    )

        activity = Activity(
            activity_id=str(uuid4()),
            description=description,
            state=Activity.INITIAL_STATE,
            functional_assignment_evidence_ids=evidence_ids,
            functional_exercise_ids=exercise_ids,
        )
        self._repository.add(activity)

        return ActivityDTO(
            activity_id=activity.activity_id,
            description=activity.description,
            state=activity.state.value,
            functional_assignment_evidence_ids=tuple(
                str(item)
                for item in activity.functional_assignment_evidence_ids
            ),
            functional_exercise_ids=tuple(
                str(item) for item in activity.functional_exercise_ids
            ),
        )
