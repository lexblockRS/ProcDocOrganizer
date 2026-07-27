"""Porta de armazenamento de atribuições funcionais documentais."""

from typing import Protocol

from applications.rsc.models import (
    FunctionalAssignmentEvidence,
    FunctionalAssignmentEvidenceId,
)


class FunctionalAssignmentEvidenceRepository(Protocol):
    """Persistência de atribuições, em ordem de inserção."""

    def save(
        self,
        evidence: FunctionalAssignmentEvidence,
    ) -> FunctionalAssignmentEvidence:
        """Insere e retorna evidence.

        Raises:
            DuplicateFunctionalAssignmentEvidenceError: se o ID existir.
        """
        ...

    def get_by_id(
        self,
        evidence_id: FunctionalAssignmentEvidenceId,
    ) -> FunctionalAssignmentEvidence | None: ...

    def list_all(
        self,
    ) -> tuple[FunctionalAssignmentEvidence, ...]:
        """Retorna todas as atribuições em ordem de inserção."""
        ...
