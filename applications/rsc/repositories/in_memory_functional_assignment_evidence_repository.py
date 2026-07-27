"""Armazenamento em memória de atribuições funcionais documentais."""

from applications.rsc.models import (
    FunctionalAssignmentEvidence,
    FunctionalAssignmentEvidenceId,
)
from applications.rsc.ports.errors import (
    DuplicateFunctionalAssignmentEvidenceError,
)


class InMemoryFunctionalAssignmentEvidenceRepository:
    """Mantém atribuições em ordem de criação durante uma sessão RSC."""

    def __init__(self) -> None:
        self._items: dict[
            FunctionalAssignmentEvidenceId,
            FunctionalAssignmentEvidence,
        ] = {}

    def save(
        self,
        evidence: FunctionalAssignmentEvidence,
    ) -> FunctionalAssignmentEvidence:
        if not isinstance(evidence, FunctionalAssignmentEvidence):
            raise TypeError(
                "evidence deve ser FunctionalAssignmentEvidence."
            )
        if evidence.id in self._items:
            raise DuplicateFunctionalAssignmentEvidenceError(
                "A atribuição funcional já existe."
            )
        self._items[evidence.id] = evidence
        return evidence

    def get_by_id(
        self,
        evidence_id: FunctionalAssignmentEvidenceId,
    ) -> FunctionalAssignmentEvidence | None:
        if not isinstance(
            evidence_id,
            FunctionalAssignmentEvidenceId,
        ):
            raise TypeError(
                "evidence_id deve ser FunctionalAssignmentEvidenceId."
            )
        return self._items.get(evidence_id)

    def list_all(
        self,
    ) -> tuple[FunctionalAssignmentEvidence, ...]:
        return tuple(self._items.values())
