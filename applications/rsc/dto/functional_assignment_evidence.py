"""DTO de leitura de uma atribuição funcional documental."""

from dataclasses import dataclass
from datetime import date

from applications.rsc.models import FunctionalAssignmentEvidence


@dataclass(frozen=True, slots=True)
class FunctionalAssignmentEvidenceDTO:
    """Representação externa imutável da atribuição funcional."""

    id: str
    person_id: str
    source_evidence_reference: str
    exercise_type_code: str
    exercise_type_label: str
    role: str
    organization: str
    start_date: date | None
    end_date: date | None
    unit: str | None
    administrative_reference: str | None
    status: str

    @classmethod
    def from_domain(
        cls,
        evidence: FunctionalAssignmentEvidence,
    ) -> "FunctionalAssignmentEvidenceDTO":
        return cls(
            id=str(evidence.id),
            person_id=evidence.person_id,
            source_evidence_reference=str(
                evidence.source_evidence_reference
            ),
            exercise_type_code=evidence.exercise_type_code,
            exercise_type_label=evidence.exercise_type_label,
            role=evidence.role,
            organization=evidence.organization,
            start_date=evidence.start_date,
            end_date=evidence.end_date,
            unit=evidence.unit,
            administrative_reference=evidence.administrative_reference,
            status=evidence.status.value,
        )
