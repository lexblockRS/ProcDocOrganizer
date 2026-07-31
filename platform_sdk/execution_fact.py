"""Fato estruturado e factual associado a uma Evidence."""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import date, datetime, timezone
from decimal import Decimal
from enum import Enum
from uuid import UUID, uuid4

from .evidence import Metadata


class ExecutionFactError(ValueError):
    """Uma operação viola as invariantes do ExecutionFact."""


class ExecutionFactState(str, Enum):
    ACTIVE = "ACTIVE"
    ARCHIVED = "ARCHIVED"


@dataclass(frozen=True, slots=True, eq=False)
class ExecutionFact:
    """Interpretação estruturada de uma Evidence, sem lógica normativa."""

    execution_fact_id: str
    project_id: str
    evidence_id: str
    fact_type: str
    description: str
    quantity: Decimal | None
    unit: str
    period_start: date | None
    period_end: date | None
    metadata: Metadata
    created_at: datetime
    updated_at: datetime
    state: ExecutionFactState = ExecutionFactState.ACTIVE

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "execution_fact_id",
            _uuid(self.execution_fact_id, "execution_fact_id"),
        )
        object.__setattr__(
            self, "project_id", _uuid(self.project_id, "project_id")
        )
        object.__setattr__(
            self, "evidence_id", _uuid(self.evidence_id, "evidence_id")
        )
        object.__setattr__(
            self, "fact_type", _required_text(self.fact_type, "fact_type")
        )
        object.__setattr__(
            self,
            "description",
            _required_text(self.description, "description"),
        )
        if self.quantity is not None and not isinstance(
            self.quantity, Decimal
        ):
            raise TypeError("quantity deve ser Decimal ou None.")
        object.__setattr__(self, "unit", _required_text(self.unit, "unit"))
        if self.period_start is not None and not isinstance(
            self.period_start, date
        ):
            raise TypeError("period_start deve ser date ou None.")
        if self.period_end is not None and not isinstance(
            self.period_end, date
        ):
            raise TypeError("period_end deve ser date ou None.")
        if (
            self.period_start is not None
            and self.period_end is not None
            and self.period_end < self.period_start
        ):
            raise ValueError("period_end não pode anteceder period_start.")
        object.__setattr__(self, "metadata", _metadata(self.metadata))
        created = _aware(self.created_at, "created_at")
        updated = _aware(self.updated_at, "updated_at")
        if updated < created:
            raise ValueError("updated_at não pode anteceder created_at.")
        object.__setattr__(self, "created_at", created)
        object.__setattr__(self, "updated_at", updated)
        if not isinstance(self.state, ExecutionFactState):
            raise TypeError("state deve ser ExecutionFactState.")

    @classmethod
    def create(
        cls,
        *,
        project_id: str,
        evidence_id: str,
        fact_type: str,
        description: str,
        quantity: Decimal | None = None,
        unit: str,
        period_start: date | None = None,
        period_end: date | None = None,
        metadata: Metadata = (),
        execution_fact_id: str | None = None,
        now: datetime | None = None,
    ) -> "ExecutionFact":
        timestamp = now or datetime.now(timezone.utc)
        return cls(
            execution_fact_id=execution_fact_id or str(uuid4()),
            project_id=project_id,
            evidence_id=evidence_id,
            fact_type=fact_type,
            description=description,
            quantity=quantity,
            unit=unit,
            period_start=period_start,
            period_end=period_end,
            metadata=metadata,
            created_at=timestamp,
            updated_at=timestamp,
        )

    @property
    def aggregate_id(self) -> str:
        return self.execution_fact_id

    def same_execution_fact(self, other: object) -> bool:
        return (
            isinstance(other, ExecutionFact)
            and self.execution_fact_id == other.execution_fact_id
        )

    def edit(
        self,
        *,
        fact_type: str | None = None,
        description: str | None = None,
        quantity: Decimal | None = None,
        unit: str | None = None,
        period_start: date | None = None,
        period_end: date | None = None,
        metadata: Metadata | None = None,
        now: datetime | None = None,
    ) -> "ExecutionFact":
        self._require_active()
        values = {
            "fact_type": self.fact_type if fact_type is None else fact_type,
            "description": (
                self.description if description is None else description
            ),
            "quantity": self.quantity if quantity is None else quantity,
            "unit": self.unit if unit is None else unit,
            "period_start": (
                self.period_start if period_start is None else period_start
            ),
            "period_end": self.period_end if period_end is None else period_end,
            "metadata": self.metadata if metadata is None else metadata,
        }
        if all(getattr(self, key) == value for key, value in values.items()):
            return self
        return replace(
            self,
            **values,
            updated_at=now or datetime.now(timezone.utc),
        )

    def change_state(
        self,
        state: ExecutionFactState,
        *,
        now: datetime | None = None,
    ) -> "ExecutionFact":
        if not isinstance(state, ExecutionFactState):
            raise TypeError("state deve ser ExecutionFactState.")
        if state is self.state:
            return self
        if self.state is ExecutionFactState.ARCHIVED:
            raise ExecutionFactError(
                "ExecutionFact arquivado não pode ser reativado."
            )
        return replace(
            self,
            state=state,
            updated_at=now or datetime.now(timezone.utc),
        )

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ExecutionFact):
            return NotImplemented
        return self.execution_fact_id == other.execution_fact_id

    def __hash__(self) -> int:
        return hash(self.execution_fact_id)

    def _require_active(self) -> None:
        if self.state is ExecutionFactState.ARCHIVED:
            raise ExecutionFactError(
                "ExecutionFact arquivado não pode ser alterado."
            )


def _required_text(value: object, field_name: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{field_name} deve ser uma string.")
    normalized = " ".join(value.split())
    if not normalized:
        raise ValueError(f"{field_name} não pode ser vazio.")
    return normalized


def _uuid(value: object, field_name: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{field_name} deve ser uma string.")
    try:
        return str(UUID(value.strip()))
    except (ValueError, AttributeError) as exc:
        raise ValueError(f"{field_name} deve ser UUID válido.") from exc


def _aware(value: object, field_name: str) -> datetime:
    if not isinstance(value, datetime) or value.tzinfo is None:
        raise TypeError(f"{field_name} deve possuir timezone.")
    return value


def _metadata(value: object) -> Metadata:
    if not isinstance(value, tuple):
        raise TypeError("metadata deve ser uma tupla.")
    normalized = []
    for item in value:
        if (
            not isinstance(item, tuple)
            or len(item) != 2
            or not isinstance(item[0], str)
            or not item[0].strip()
            or not isinstance(item[1], (str, int, bool, type(None)))
        ):
            raise TypeError("metadata deve conter pares escalares.")
        normalized.append((item[0].strip(), item[1]))
    if len(normalized) != len({key for key, _ in normalized}):
        raise ExecutionFactError("metadata não aceita chaves duplicadas.")
    return tuple(normalized)


__all__ = [
    "ExecutionFact",
    "ExecutionFactError",
    "ExecutionFactState",
]
