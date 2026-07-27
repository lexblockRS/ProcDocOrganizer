"""Montagem de exercício funcional a partir de entrada manual."""

from uuid import uuid4

from applications.rsc.commands import CreateFunctionalExerciseCommand
from applications.rsc.models import (
    FunctionalContext,
    FunctionalAssignmentEvidenceId,
    FunctionalExercise,
    FunctionalExerciseId,
    FunctionalExerciseStatus,
    FunctionalExerciseType,
    FunctionalPeriod,
    FunctionalRole,
)


class ManualFunctionalExerciseAssembler:
    """Constrói um exercício funcional originado por entrada manual."""

    def assemble(
        self,
        command: CreateFunctionalExerciseCommand,
    ) -> FunctionalExercise:
        if not isinstance(command, CreateFunctionalExerciseCommand):
            raise TypeError(
                "command deve ser CreateFunctionalExerciseCommand."
            )

        period = FunctionalPeriod(
            start_date=command.start_date,
            end_date=command.end_date,
        )
        status = (
            FunctionalExerciseStatus.ACTIVE
            if period.is_open
            else FunctionalExerciseStatus.ENDED
        )
        return FunctionalExercise(
            id=FunctionalExerciseId(str(uuid4())),
            person_id=command.person_id,
            exercise_type=FunctionalExerciseType(
                code=command.exercise_type_code,
                label=command.exercise_type_label,
            ),
            role=FunctionalRole(command.role),
            context=FunctionalContext(
                organization=command.context_organization,
                unit=command.context_unit,
                reference=command.context_reference,
            ),
            period=period,
            status=status,
            functional_assignment_evidence_ids=tuple(
                FunctionalAssignmentEvidenceId.from_string(evidence_id)
                for evidence_id
                in command.functional_assignment_evidence_ids
            ),
        )
