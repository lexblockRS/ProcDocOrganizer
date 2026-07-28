"""Ocorrência de atividade declarada para avaliação RSC."""

from dataclasses import dataclass, replace
from datetime import date, datetime
from decimal import Decimal

from .enums import ActivityStatus
from .identifiers import (
    normalize_uuid,
    optional_text,
    positive_decimal,
    require_aware,
    required_text,
    utc_now,
)


@dataclass(frozen=True, slots=True)
class RscActivity:
    criterion_id: str
    title: str
    quantity: Decimal | int | str
    id: str | None = None
    description: str | None = None
    score_variant_id: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    status: ActivityStatus = ActivityStatus.DRAFT
    evidence_ids: tuple[str, ...] = ()
    notes: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "id", normalize_uuid(self.id))
        object.__setattr__(
            self, "criterion_id", required_text(self.criterion_id, "criterion_id")
        )
        object.__setattr__(self, "title", required_text(self.title, "title"))
        object.__setattr__(
            self, "description", optional_text(self.description, "description")
        )
        object.__setattr__(
            self,
            "score_variant_id",
            optional_text(self.score_variant_id, "score_variant_id"),
        )
        object.__setattr__(self, "quantity", positive_decimal(self.quantity))
        for field_name in ("start_date", "end_date"):
            value = getattr(self, field_name)
            if value is not None and (
                isinstance(value, datetime) or not isinstance(value, date)
            ):
                raise TypeError(f"{field_name} deve ser date.")
        if (
            self.start_date is not None
            and self.end_date is not None
            and self.start_date > self.end_date
        ):
            raise ValueError("start_date não pode ser posterior a end_date.")
        if not isinstance(self.status, ActivityStatus):
            raise TypeError("status deve ser ActivityStatus.")
        evidence_ids = tuple(
            required_text(value, "evidence_id") for value in self.evidence_ids
        )
        if len(set(evidence_ids)) != len(evidence_ids):
            raise ValueError("evidências não podem duplicar.")
        object.__setattr__(self, "evidence_ids", evidence_ids)
        object.__setattr__(self, "notes", optional_text(self.notes, "notes"))
        created = self.created_at or utc_now()
        updated = self.updated_at or created
        object.__setattr__(self, "created_at", require_aware(created, "created_at"))
        object.__setattr__(self, "updated_at", require_aware(updated, "updated_at"))

    def link_evidence(self, evidence_id: str) -> "RscActivity":
        normalized = required_text(evidence_id, "evidence_id")
        if normalized in self.evidence_ids:
            raise ValueError("evidência já vinculada.")
        return replace(
            self,
            evidence_ids=(*self.evidence_ids, normalized),
            updated_at=utc_now(),
        )

    def unlink_evidence(self, evidence_id: str) -> "RscActivity":
        normalized = required_text(evidence_id, "evidence_id")
        if normalized not in self.evidence_ids:
            raise KeyError(f"evidência inexistente: {normalized}")
        return replace(
            self,
            evidence_ids=tuple(
                value for value in self.evidence_ids if value != normalized
            ),
            updated_at=utc_now(),
        )
