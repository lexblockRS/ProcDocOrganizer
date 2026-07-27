"""Consulta das atribuições funcionais documentais da sessão."""

from applications.rsc.dto import FunctionalAssignmentEvidenceDTO
from applications.rsc.ports import (
    FunctionalAssignmentEvidenceRepository,
)


class ListFunctionalAssignmentEvidencesService:
    """Projeta atribuições armazenadas em DTOs imutáveis."""

    def __init__(
        self,
        repository: FunctionalAssignmentEvidenceRepository,
    ) -> None:
        self._repository = repository

    def execute(
        self,
    ) -> tuple[FunctionalAssignmentEvidenceDTO, ...]:
        return tuple(
            FunctionalAssignmentEvidenceDTO.from_domain(evidence)
            for evidence in self._repository.list_all()
        )
