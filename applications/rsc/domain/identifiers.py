"""Identificadores canônicos e utilidades básicas do domínio RSC."""

from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from uuid import UUID, uuid4

RSC_REQUIREMENT_IDS = tuple(
    f"rsc.requirement.{number}" for number in range(1, 7)
)


def requirement_id(number: int) -> str:
    if number not in range(1, 7):
        raise ValueError("number deve estar entre 1 e 6.")
    return RSC_REQUIREMENT_IDS[number - 1]


def criterion_id(requirement_number: int, item_number: int) -> str:
    requirement_id(requirement_number)
    if isinstance(item_number, bool) or item_number < 1:
        raise ValueError("item_number deve ser positivo.")
    return f"rsc.criterion.{requirement_number}.{item_number}"


def new_uuid() -> str:
    return str(uuid4())


def normalize_uuid(value: str | None) -> str:
    if value is None:
        return new_uuid()
    if not isinstance(value, str):
        raise TypeError("id deve ser uma string UUID.")
    try:
        return str(UUID(value.strip()))
    except (ValueError, AttributeError) as exc:
        raise ValueError("id deve ser um UUID válido.") from exc


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def require_aware(value: datetime, field: str) -> datetime:
    if not isinstance(value, datetime):
        raise TypeError(f"{field} deve ser datetime.")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field} deve possuir timezone.")
    return value


def required_text(value: object, field: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{field} deve ser string.")
    normalized = " ".join(value.split())
    if not normalized:
        raise ValueError(f"{field} é obrigatório.")
    return normalized


def optional_text(value: object, field: str) -> str | None:
    return None if value is None else required_text(value, field)


def positive_decimal(value: object, field: str = "quantity") -> Decimal:
    if isinstance(value, bool):
        raise TypeError(f"{field} deve ser numérico.")
    try:
        result = Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise TypeError(f"{field} deve ser compatível com Decimal.") from exc
    if not result.is_finite() or result <= 0:
        raise ValueError(f"{field} deve ser maior que zero.")
    return result
