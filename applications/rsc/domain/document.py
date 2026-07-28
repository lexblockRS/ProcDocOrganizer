"""Referência documental neutra do domínio RSC."""

from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import date, datetime
from types import MappingProxyType

from .enums import DocumentStatus
from .identifiers import (
    normalize_uuid,
    optional_text,
    require_aware,
    required_text,
    utc_now,
)


def _simple_metadata(values: Mapping[str, object]) -> Mapping[str, object]:
    allowed = (str, int, float, bool, type(None))
    normalized = dict(values)
    if any(
        not isinstance(key, str) or not isinstance(value, allowed)
        for key, value in normalized.items()
    ):
        raise ValueError("metadata aceita somente chaves textuais e valores simples.")
    return MappingProxyType(normalized)


@dataclass(frozen=True, slots=True)
class RscDocument:
    file_name: str
    id: str | None = None
    original_path: str | None = None
    stored_path: str | None = None
    mime_type: str | None = None
    checksum: str | None = None
    document_date: date | None = None
    description: str | None = None
    status: DocumentStatus = DocumentStatus.AVAILABLE
    created_at: datetime | None = None
    metadata: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "id", normalize_uuid(self.id))
        object.__setattr__(
            self, "file_name", required_text(self.file_name, "file_name")
        )
        for name in (
            "original_path",
            "stored_path",
            "mime_type",
            "checksum",
            "description",
        ):
            object.__setattr__(self, name, optional_text(getattr(self, name), name))
        if self.document_date is not None and (
            isinstance(self.document_date, datetime)
            or not isinstance(self.document_date, date)
        ):
            raise TypeError("document_date deve ser date.")
        if not isinstance(self.status, DocumentStatus):
            raise TypeError("status deve ser DocumentStatus.")
        created = self.created_at or utc_now()
        object.__setattr__(self, "created_at", require_aware(created, "created_at"))
        object.__setattr__(self, "metadata", _simple_metadata(self.metadata))
