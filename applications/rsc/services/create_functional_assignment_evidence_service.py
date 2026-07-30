"""Caso de uso de criação de atribuição funcional documental."""

from applications.rsc.assemblers import (
    FunctionalAssignmentEvidenceAssembler,
)
from applications.rsc.commands import (
    CreateFunctionalAssignmentEvidenceCommand,
)
from applications.rsc.dto import FunctionalAssignmentEvidenceDTO
from applications.rsc.ports import (
    FunctionalAssignmentEvidenceRepository,
    SourceEvidenceLookup,
)

from .functional_assignment_normalizer import (
    FunctionalAssignmentNormalizer,
)


class SourceEvidenceNotFoundError(LookupError):
    """A Evidence referenciada não existe no projeto aberto."""


class CreateFunctionalAssignmentEvidenceService:
    """Valida a fonte, monta, normaliza e armazena uma atribuição."""

    def __init__(
        self,
        source_evidence_lookup: SourceEvidenceLookup,
        repository: FunctionalAssignmentEvidenceRepository,
        assembler: FunctionalAssignmentEvidenceAssembler,
        normalizer: FunctionalAssignmentNormalizer,
    ) -> None:
        self._source_evidence_lookup = source_evidence_lookup
        self._repository = repository
        self._assembler = assembler
        self._normalizer = normalizer

    def execute(
        self,
        command: CreateFunctionalAssignmentEvidenceCommand,
    ) -> FunctionalAssignmentEvidenceDTO:
        if not isinstance(
            command,
            CreateFunctionalAssignmentEvidenceCommand,
        ):
            raise TypeError(
                "command deve ser "
                "CreateFunctionalAssignmentEvidenceCommand."
            )
        if not self._source_evidence_lookup.exists(
            command.source_evidence_reference
        ):
            raise SourceEvidenceNotFoundError(
                "Evidence de origem não encontrada."
            )

        raw = self._assembler.assemble(command)
        stored = self._repository.save(raw)
        return FunctionalAssignmentEvidenceDTO.from_domain(stored)
