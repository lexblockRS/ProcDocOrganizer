"""CRUD explícito da interpretação funcional, sem regras normativas."""

from dataclasses import replace

from applications.rsc.models import (
    FunctionalAssignmentEvidenceId,
    FunctionalAssignmentEvidenceStatus,
)


class FunctionalAssignmentManagementError(ValueError):
    """Falha de validação ou localização da interpretação funcional."""


class FunctionalAssignmentManagementService:
    def __init__(self, repository, source_evidence_lookup) -> None:
        self._repository = repository
        self._source_evidence_lookup = source_evidence_lookup

    def update(self, assignment_id: str, **changes):
        current = self._require(assignment_id)
        changes.pop("id", None)
        changes.pop("source_evidence_reference", None)
        changes.pop("status", None)
        try:
            updated = replace(current, **changes)
        except (TypeError, ValueError) as exc:
            raise FunctionalAssignmentManagementError(str(exc)) from exc
        return self._repository.update(updated)

    def advance(self, assignment_id: str):
        current = self._require(assignment_id)
        try:
            if current.status in (
                FunctionalAssignmentEvidenceStatus.RAW,
                FunctionalAssignmentEvidenceStatus.NORMALIZED,
            ):
                updated = current.mark_identified()
            elif (
                current.status
                is FunctionalAssignmentEvidenceStatus.IDENTIFIED
            ):
                updated = current.mark_linked()
            else:
                raise FunctionalAssignmentManagementError(
                    "A interpretação já atingiu o estado LINKED."
                )
        except ValueError as exc:
            raise FunctionalAssignmentManagementError(str(exc)) from exc
        return self._repository.update(updated)

    def delete(self, assignment_id: str):
        identifier = FunctionalAssignmentEvidenceId.from_string(
            assignment_id
        )
        deleted = self._repository.delete(identifier)
        if deleted is None:
            raise FunctionalAssignmentManagementError(
                "A interpretação funcional não foi localizada."
            )
        return deleted

    def _require(self, assignment_id: str):
        identifier = FunctionalAssignmentEvidenceId.from_string(
            assignment_id
        )
        current = self._repository.get_by_id(identifier)
        if current is None:
            raise FunctionalAssignmentManagementError(
                "A interpretação funcional não foi localizada."
            )
        if not self._source_evidence_lookup.exists(
            str(current.source_evidence_reference)
        ):
            raise FunctionalAssignmentManagementError(
                "A Evidence de origem não está disponível."
            )
        return current
