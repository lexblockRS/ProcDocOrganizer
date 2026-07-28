"""Alegação documental que comprova uma atividade RSC."""

from dataclasses import dataclass, replace
from datetime import datetime

from .enums import EvidenceStatus
from .identifiers import (
    normalize_uuid,
    optional_text,
    require_aware,
    required_text,
    utc_now,
)


@dataclass(frozen=True, slots=True)
class RscEvidence:
    activity_id: str
    document_ids: tuple[str, ...]
    description: str
    id: str | None = None
    status: EvidenceStatus = EvidenceStatus.PROPOSED
    justification: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "id", normalize_uuid(self.id))
        object.__setattr__(
            self, "activity_id", required_text(self.activity_id, "activity_id")
        )
        documents = tuple(
            required_text(value, "document_id") for value in self.document_ids
        )
        if not documents:
            raise ValueError("evidência exige ao menos um documento.")
        if len(set(documents)) != len(documents):
            raise ValueError("documentos não podem duplicar.")
        object.__setattr__(self, "document_ids", documents)
        object.__setattr__(
            self, "description", required_text(self.description, "description")
        )
        if not isinstance(self.status, EvidenceStatus):
            raise TypeError("status deve ser EvidenceStatus.")
        object.__setattr__(
            self,
            "justification",
            optional_text(self.justification, "justification"),
        )
        created = self.created_at or utc_now()
        updated = self.updated_at or created
        object.__setattr__(self, "created_at", require_aware(created, "created_at"))
        object.__setattr__(self, "updated_at", require_aware(updated, "updated_at"))

    def link_document(self, document_id: str) -> "RscEvidence":
        normalized = required_text(document_id, "document_id")
        if normalized in self.document_ids:
            raise ValueError("documento já vinculado.")
        return replace(
            self,
            document_ids=(*self.document_ids, normalized),
            updated_at=utc_now(),
        )

    def unlink_document(self, document_id: str) -> "RscEvidence":
        normalized = required_text(document_id, "document_id")
        if normalized not in self.document_ids:
            raise KeyError(f"documento inexistente: {normalized}")
        remaining = tuple(
            value for value in self.document_ids if value != normalized
        )
        if not remaining:
            raise ValueError("evidência exige ao menos um documento.")
        return replace(self, document_ids=remaining, updated_at=utc_now())
