"""Normalização sintática de atribuições funcionais documentais."""

from applications.rsc.models import FunctionalAssignmentEvidence


class FunctionalAssignmentNormalizer:
    """Produz uma nova evidência sintaticamente normalizada."""

    def normalize(
        self,
        evidence: FunctionalAssignmentEvidence,
    ) -> FunctionalAssignmentEvidence:
        if not isinstance(evidence, FunctionalAssignmentEvidence):
            raise TypeError(
                "evidence deve ser FunctionalAssignmentEvidence."
            )

        normalized = FunctionalAssignmentEvidence(
            id=evidence.id,
            person_id=evidence.person_id,
            source_evidence_reference=evidence.source_evidence_reference,
            exercise_type_code=evidence.exercise_type_code,
            exercise_type_label=self._normalize_text(
                evidence.exercise_type_label
            ),
            role=self._normalize_text(evidence.role),
            organization=self._normalize_text(evidence.organization),
            start_date=evidence.start_date,
            end_date=evidence.end_date,
            unit=self._normalize_optional_text(evidence.unit),
            administrative_reference=self._normalize_optional_text(
                evidence.administrative_reference
            ),
            status=evidence.status,
        )
        return normalized.mark_normalized()

    @staticmethod
    def _normalize_text(value: str) -> str:
        return " ".join(value.split())

    @classmethod
    def _normalize_optional_text(
        cls,
        value: str | None,
    ) -> str | None:
        if value is None:
            return None
        return cls._normalize_text(value)
