"""Enquadramento explícito entre fato e contrato normativo."""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime, timezone
from enum import Enum
from uuid import UUID, uuid4

from .evidence import Metadata


class ExecutionBindingError(ValueError):
    """Um Binding viola suas invariantes estruturais."""


class BindingOrigin(str, Enum):
    MANUAL = "MANUAL"


@dataclass(frozen=True, slots=True, eq=False)
class ExecutionBinding:
    """Decisão de enquadramento, sem fato ou regra normativa própria."""

    binding_id: str
    execution_fact_id: str
    criterion_id: str
    requirement_id: str
    execution_rule_id: str
    origin: BindingOrigin
    created_at: datetime
    metadata: Metadata = ()

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "binding_id", _uuid(self.binding_id, "binding_id")
        )
        object.__setattr__(
            self,
            "execution_fact_id",
            _uuid(self.execution_fact_id, "execution_fact_id"),
        )
        for field_name in (
            "criterion_id",
            "requirement_id",
            "execution_rule_id",
        ):
            object.__setattr__(
                self,
                field_name,
                _required_text(getattr(self, field_name), field_name),
            )
        if not isinstance(self.origin, BindingOrigin):
            raise TypeError("origin deve ser BindingOrigin.")
        if (
            not isinstance(self.created_at, datetime)
            or self.created_at.tzinfo is None
        ):
            raise TypeError("created_at deve possuir timezone.")
        object.__setattr__(self, "metadata", _metadata(self.metadata))

    @classmethod
    def create(
        cls,
        *,
        execution_fact_id: str,
        criterion_id: str,
        requirement_id: str,
        execution_rule_id: str,
        origin: BindingOrigin = BindingOrigin.MANUAL,
        metadata: Metadata = (),
        binding_id: str | None = None,
        now: datetime | None = None,
    ) -> "ExecutionBinding":
        return cls(
            binding_id=binding_id or str(uuid4()),
            execution_fact_id=execution_fact_id,
            criterion_id=criterion_id,
            requirement_id=requirement_id,
            execution_rule_id=execution_rule_id,
            origin=origin,
            created_at=now or datetime.now(timezone.utc),
            metadata=metadata,
        )

    @property
    def aggregate_id(self) -> str:
        return self.binding_id

    def same_binding(self, other: object) -> bool:
        return (
            isinstance(other, ExecutionBinding)
            and self.binding_id == other.binding_id
        )

    def rebind(
        self,
        *,
        criterion_id: str,
        requirement_id: str,
        execution_rule_id: str,
        metadata: Metadata | None = None,
    ) -> "ExecutionBinding":
        values = {
            "criterion_id": criterion_id,
            "requirement_id": requirement_id,
            "execution_rule_id": execution_rule_id,
            "metadata": self.metadata if metadata is None else metadata,
        }
        if all(getattr(self, key) == value for key, value in values.items()):
            return self
        return replace(self, **values)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ExecutionBinding):
            return NotImplemented
        return self.binding_id == other.binding_id

    def __hash__(self) -> int:
        return hash(self.binding_id)


def _uuid(value: object, field_name: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{field_name} deve ser uma string.")
    try:
        return str(UUID(value.strip()))
    except (ValueError, AttributeError) as exc:
        raise ValueError(f"{field_name} deve ser UUID válido.") from exc


def _required_text(value: object, field_name: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{field_name} deve ser uma string.")
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{field_name} não pode ser vazio.")
    return normalized


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
        raise ExecutionBindingError(
            "metadata não aceita chaves duplicadas."
        )
    return tuple(normalized)


__all__ = [
    "BindingOrigin",
    "ExecutionBinding",
    "ExecutionBindingError",
]
