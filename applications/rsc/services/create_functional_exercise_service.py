"""Serviço do caso de uso CreateFunctionalExercise."""

from applications.rsc.assemblers import ManualFunctionalExerciseAssembler
from applications.rsc.commands import CreateFunctionalExerciseCommand
from applications.rsc.dto import FunctionalExerciseDTO
from applications.rsc.models import (
    FunctionalAssignmentEvidenceId,
    FunctionalAssignmentEvidenceStatus,
    FunctionalExercise,
)
from applications.rsc.ports import (
    FunctionalAssignmentEvidenceRepository,
    FunctionalExerciseRepository,
)


class FunctionalAssignmentEvidenceRequiredError(ValueError):
    """Indica que nenhuma evidência foi selecionada."""


class DuplicateFunctionalAssignmentEvidenceReferenceError(ValueError):
    """Indica referências repetidas na seleção."""


class FunctionalAssignmentEvidenceNotFoundError(LookupError):
    """Indica referência a uma atribuição inexistente."""


class IncompatibleFunctionalAssignmentEvidenceError(ValueError):
    """Indica atribuição fora do estágio aceito pelo fluxo atual."""


class CreateFunctionalExerciseService:
    """Orquestra a criação de um exercício funcional."""

    def __init__(
        self,
        repository: FunctionalExerciseRepository,
        assembler: ManualFunctionalExerciseAssembler,
        assignment_evidence_repository: (
            FunctionalAssignmentEvidenceRepository | None
        ) = None,
    ) -> None:
        self._repository = repository
        self._assembler = assembler
        self._assignment_evidence_repository = (
            assignment_evidence_repository
        )

    def execute(
        self,
        command: CreateFunctionalExerciseCommand,
    ) -> FunctionalExerciseDTO:
        if not isinstance(command, CreateFunctionalExerciseCommand):
            raise TypeError(
                "command deve ser CreateFunctionalExerciseCommand."
            )
        if self._assignment_evidence_repository is not None:
            self._validate_assignment_evidences(command)
        exercise = self._assembler.assemble(command)
        self._repository.save(exercise)
        return self._to_dto(exercise)

    def _validate_assignment_evidences(
        self,
        command: CreateFunctionalExerciseCommand,
    ) -> None:
        references = command.functional_assignment_evidence_ids
        if not references:
            raise FunctionalAssignmentEvidenceRequiredError(
                "Ao menos uma evidência de atribuição funcional é "
                "obrigatória."
            )
        evidence_ids = tuple(
            FunctionalAssignmentEvidenceId.from_string(reference)
            for reference in references
        )
        if len(set(evidence_ids)) != len(evidence_ids):
            raise DuplicateFunctionalAssignmentEvidenceReferenceError(
                "A seleção contém referências duplicadas."
            )

        for reference, evidence_id in zip(references, evidence_ids):
            evidence = self._assignment_evidence_repository.get_by_id(
                evidence_id
            )
            if evidence is None:
                raise FunctionalAssignmentEvidenceNotFoundError(
                    f"Evidência de atribuição funcional não encontrada: "
                    f"{reference}."
                )
            if evidence.status not in (
                FunctionalAssignmentEvidenceStatus.NORMALIZED,
                FunctionalAssignmentEvidenceStatus.LINKED,
            ):
                raise IncompatibleFunctionalAssignmentEvidenceError(
                    "O fluxo atual aceita apenas evidências de atribuição "
                    "funcional normalizadas."
                )

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
            functional_assignment_evidence_ids=tuple(
                str(evidence_id)
                for evidence_id
                in exercise.functional_assignment_evidence_ids
            ),
        )
