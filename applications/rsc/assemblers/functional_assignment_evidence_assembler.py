"""Montagem de uma interpretação funcional documental estruturada."""

from uuid import uuid4

from applications.rsc.commands import (
    CreateFunctionalAssignmentEvidenceCommand,
)
from applications.rsc.models import (
    FunctionalAssignmentEvidence,
    FunctionalAssignmentEvidenceId,
    SourceEvidenceReference,
)


class FunctionalAssignmentEvidenceAssembler:
    """Constrói uma atribuição documental no estado inicial do domínio."""

    def assemble(
        self,
        command: CreateFunctionalAssignmentEvidenceCommand,
    ) -> FunctionalAssignmentEvidence:
        if not isinstance(
            command,
            CreateFunctionalAssignmentEvidenceCommand,
        ):
            raise TypeError(
                "command deve ser "
                "CreateFunctionalAssignmentEvidenceCommand."
            )

        return FunctionalAssignmentEvidence(
            id=FunctionalAssignmentEvidenceId(str(uuid4())),
            person_id=command.person_id,
            source_evidence_reference=SourceEvidenceReference(
                command.source_evidence_reference
            ),
            exercise_type_code=command.exercise_type_code,
            exercise_type_label=command.exercise_type_label,
            role=command.role,
            organization=command.organization,
            start_date=command.start_date,
            end_date=command.end_date,
            unit=command.unit,
            administrative_reference=command.administrative_reference,
        )
