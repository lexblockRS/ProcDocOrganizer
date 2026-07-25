"""Fundação imutável do domínio de exercício funcional do ProcDoc RSC."""

from dataclasses import dataclass
from datetime import date, datetime
from enum import Enum
from uuid import UUID


def _normalized_text(value: object, field: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{field} deve ser uma string.")
    normalized = " ".join(value.split())
    if not normalized:
        raise ValueError(f"{field} não pode ser vazio.")
    return normalized


def _optional_normalized_text(
    value: object,
    field: str,
) -> str | None:
    if value is None:
        return None
    return _normalized_text(value, field)


@dataclass(frozen=True, slots=True)
class FunctionalExerciseId:
    """Identidade opaca de um exercício funcional."""

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
    def from_string(cls, value: str) -> "FunctionalExerciseId":
        return cls(value)


@dataclass(frozen=True, slots=True)
class FunctionalExerciseType:
    """Classificação aberta de um exercício funcional."""

    code: str
    label: str

    def __post_init__(self) -> None:
        normalized_code = _normalized_text(self.code, "code")
        normalized_label = _normalized_text(self.label, "label")
        object.__setattr__(
            self,
            "code",
            normalized_code.lower().replace(" ", "_"),
        )
        object.__setattr__(self, "label", normalized_label)


@dataclass(frozen=True, slots=True)
class FunctionalRole:
    """Função exercida pela pessoa."""

    name: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "name",
            _normalized_text(self.name, "name"),
        )


@dataclass(frozen=True, slots=True)
class FunctionalContext:
    """Contexto institucional em que a função é exercida."""

    organization: str
    unit: str | None = None
    reference: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "organization",
            _normalized_text(self.organization, "organization"),
        )
        object.__setattr__(
            self,
            "unit",
            _optional_normalized_text(self.unit, "unit"),
        )
        object.__setattr__(
            self,
            "reference",
            _optional_normalized_text(self.reference, "reference"),
        )


class FunctionalExerciseStatus(str, Enum):
    """Situação temporal de um exercício funcional."""

    ACTIVE = "active"
    ENDED = "ended"


@dataclass(frozen=True, slots=True)
class FunctionalPeriod:
    """Intervalo inclusivo de um exercício funcional."""

    start_date: date
    end_date: date | None = None

    def __post_init__(self) -> None:
        self._require_date(self.start_date, "start_date")
        if self.end_date is not None:
            self._require_date(self.end_date, "end_date")
            if self.end_date < self.start_date:
                raise ValueError(
                    "end_date não pode ser anterior a start_date."
                )

    @property
    def is_open(self) -> bool:
        return self.end_date is None

    @property
    def is_closed(self) -> bool:
        return self.end_date is not None

    def contains(self, target: date) -> bool:
        self._require_date(target, "target")
        return (
            target >= self.start_date
            and (self.end_date is None or target <= self.end_date)
        )

    @staticmethod
    def _require_date(value: object, field: str) -> None:
        if isinstance(value, datetime) or not isinstance(value, date):
            raise TypeError(f"{field} deve ser uma data sem horário.")


@dataclass(frozen=True, slots=True)
class FunctionalExercise:
    """Exercício contínuo de uma função em um contexto específico."""

    id: FunctionalExerciseId
    person_id: str
    exercise_type: FunctionalExerciseType
    role: FunctionalRole
    context: FunctionalContext
    period: FunctionalPeriod
    status: FunctionalExerciseStatus

    def __post_init__(self) -> None:
        self._require_instance(
            self.id,
            FunctionalExerciseId,
            "id",
        )
        if not isinstance(self.person_id, str):
            raise TypeError("person_id deve ser uma string.")
        person_id = self.person_id.strip()
        if not person_id:
            raise ValueError("person_id não pode ser vazio.")
        object.__setattr__(self, "person_id", person_id)
        self._require_instance(
            self.exercise_type,
            FunctionalExerciseType,
            "exercise_type",
        )
        self._require_instance(self.role, FunctionalRole, "role")
        self._require_instance(
            self.context,
            FunctionalContext,
            "context",
        )
        self._require_instance(
            self.period,
            FunctionalPeriod,
            "period",
        )
        self._require_instance(
            self.status,
            FunctionalExerciseStatus,
            "status",
        )
        if (
            self.status is FunctionalExerciseStatus.ACTIVE
            and self.period.is_closed
        ):
            raise ValueError("status ACTIVE exige período aberto.")
        if (
            self.status is FunctionalExerciseStatus.ENDED
            and self.period.is_open
        ):
            raise ValueError("status ENDED exige período fechado.")

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
