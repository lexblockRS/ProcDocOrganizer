"""Projeções imutáveis para leitura e apresentação documental."""

from dataclasses import dataclass, field
from enum import Enum
from types import MappingProxyType
from typing import Any, Mapping


class DocumentAvailability(str, Enum):
    AVAILABLE = "available"
    MISSING = "missing"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class DocumentSummary:
    identity: str
    sha256: str
    name: str
    relative_path: str
    document_type: str
    document_date: str | None
    page_count: int
    processing_status: str
    availability: DocumentAvailability
    has_processing_result: bool
    extension: str = ""
    file_size: int = 0
    imported_at: str = ""
    status: str = "imported"
    ocr_used: bool = False


@dataclass(frozen=True)
class DocumentDetails:
    summary: DocumentSummary
    imported_at: str
    processed_at: str | None
    text_source: str | None
    ocr_used: bool
    processing_error: str | None
    metadata: Mapping[str, Any] = field(default_factory=dict)
    page_count: int = 0
    has_pages: bool = False

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "metadata", MappingProxyType(dict(self.metadata or {}))
        )


@dataclass(frozen=True)
class DocumentPageSummary:
    document_identity: str
    document_sha256: str
    page_number: int
    text: str
    text_source: str
    character_count: int

