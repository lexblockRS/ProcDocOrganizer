"""Interpretação funcional estruturada de uma evidência documental."""

from dataclasses import dataclass, replace
from datetime import date, datetime
from enum import Enum
from uuid import UUID


def _required_text(value: object, field: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{field} deve ser uma string.")
    normalized = " ".join(value.split())
    if not normalized:
        raise ValueError(f"{field} não pode ser vazio.")
    return normalized


def _optional_text(value: object, field: str) -> str | None:
    if value is None:
        return None
    return _required_text(value, field)


@dataclass(frozen=True, slots=True)
class FunctionalAssignmentEvidenceId:
    """Identidade de uma interpretação funcional documental."""

    value: str

    def __post_init__(self) -> None:
        if not isinstance(self.value, str):
            raise TypeError("value deve ser uma string.")
        normalized = self.value.strip()
        if not normalized:
            raise ValueError("value não pode ser vazio.")
        try:
            normalized = str(UUID(normalized))
        except ValueError as exc:
            raise ValueError("value deve ser um UUID válido.") from exc
        object.__setattr__(self, "value", normalized)

    def __str__(self) -> str:
        return self.value

    @classmethod
    def from_string(
        cls,
        value: str,
    ) -> "FunctionalAssignmentEvidenceId":
        return cls(value)


@dataclass(frozen=True, slots=True)
class SourceEvidenceReference:
    """Referência opaca a uma Evidence pertencente ao ProcDoc Base."""

    value: str

    def __post_init__(self) -> None:
        if not isinstance(self.value, str):
            raise TypeError("value deve ser uma string.")
        normalized = self.value.strip()
        if not normalized:
            raise ValueError("value não pode ser vazio.")
        object.__setattr__(self, "value", normalized)

    def __str__(self) -> str:
        return self.value


class FunctionalAssignmentEvidenceStatus(str, Enum):
    """Etapa alcançada no processamento da interpretação documental."""

    RAW = "raw"
    NORMALIZED = "normalized"
    IDENTIFIED = "identified"
    LINKED = "linked"


@dataclass(frozen=True, slots=True)
class FunctionalAssignmentEvidence:
    """Afirmação documental sobre um possível exercício funcional."""

    id: FunctionalAssignmentEvidenceId
    person_id: str
    source_evidence_reference: SourceEvidenceReference
    exercise_type_code: str
    exercise_type_label: str
    role: str
    organization: str
    start_date: date | None = None
    end_date: date | None = None
    unit: str | None = None
    administrative_reference: str | None = None
    status: FunctionalAssignmentEvidenceStatus = (
        FunctionalAssignmentEvidenceStatus.RAW
    )

    def __post_init__(self) -> None:
        self._require_instance(
            self.id,
            FunctionalAssignmentEvidenceId,
            "id",
        )
        self._require_instance(
            self.source_evidence_reference,
            SourceEvidenceReference,
            "source_evidence_reference",
        )
        for field in (
            "person_id",
            "exercise_type_code",
            "exercise_type_label",
            "role",
            "organization",
        ):
            object.__setattr__(
                self,
                field,
                _required_text(getattr(self, field), field),
            )
        for field in ("unit", "administrative_reference"):
            object.__setattr__(
                self,
                field,
                _optional_text(getattr(self, field), field),
            )
        self._validate_optional_date(self.start_date, "start_date")
        self._validate_optional_date(self.end_date, "end_date")
        if (
            self.start_date is not None
            and self.end_date is not None
            and self.end_date < self.start_date
        ):
            raise ValueError(
                "end_date não pode ser anterior a start_date."
            )
        self._require_instance(
            self.status,
            FunctionalAssignmentEvidenceStatus,
            "status",
        )

    def mark_normalized(self) -> "FunctionalAssignmentEvidence":
        return self._transition(
            FunctionalAssignmentEvidenceStatus.RAW,
            FunctionalAssignmentEvidenceStatus.NORMALIZED,
        )

    def mark_identified(self) -> "FunctionalAssignmentEvidence":
        return self._transition(
            FunctionalAssignmentEvidenceStatus.NORMALIZED,
            FunctionalAssignmentEvidenceStatus.IDENTIFIED,
        )

    def mark_linked(self) -> "FunctionalAssignmentEvidence":
        return self._transition(
            FunctionalAssignmentEvidenceStatus.IDENTIFIED,
            FunctionalAssignmentEvidenceStatus.LINKED,
        )

    def _transition(
        self,
        expected: FunctionalAssignmentEvidenceStatus,
        target: FunctionalAssignmentEvidenceStatus,
    ) -> "FunctionalAssignmentEvidence":
        if self.status is not expected:
            raise ValueError(
                f"transição para {target.value} exige status "
                f"{expected.value}."
            )
        return replace(self, status=target)

    @staticmethod
    def _validate_optional_date(value: object, field: str) -> None:
        if value is None:
            return
        if isinstance(value, datetime) or not isinstance(value, date):
            raise TypeError(f"{field} deve ser uma data sem horário.")

    @staticmethod
    def _require_instance(
        value: object,
        expected_type: type,
        field: str,
    ) -> None:
        if not isinstance(value, expected_type):
            raise TypeError(
                f"{field} deve ser {expected_type.__name__}."
            )
