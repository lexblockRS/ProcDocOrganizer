"""Evidence documental neutra, pertencente a um Project."""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime, timezone
from enum import Enum
from pathlib import PurePosixPath
import re
from uuid import UUID, uuid4


Metadata = tuple[tuple[str, str | int | bool | None], ...]
_SHA256 = re.compile(r"^[0-9a-fA-F]{64}$")


class EvidenceError(ValueError):
    """Uma operação viola as invariantes de Evidence."""


class EvidenceState(str, Enum):
    ACTIVE = "ACTIVE"
    ARCHIVED = "ARCHIVED"


@dataclass(frozen=True, slots=True)
class Document:
    """Referência descritiva a um arquivo, sem comportamento físico."""

    document_id: str
    name: str
    relative_path: str
    document_type: str
    sha256: str | None = None
    size: int | None = None

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "document_id", _required_text(self.document_id, "document_id")
        )
        object.__setattr__(self, "name", _required_text(self.name, "name"))
        path = PurePosixPath(
            _required_text(self.relative_path, "relative_path")
        )
        if path.is_absolute() or ".." in path.parts:
            raise ValueError(
                "relative_path deve permanecer relativo ao Workspace."
            )
        object.__setattr__(self, "relative_path", path.as_posix())
        object.__setattr__(
            self,
            "document_type",
            _required_text(self.document_type, "document_type"),
        )
        if self.sha256 is not None:
            if not isinstance(self.sha256, str) or not _SHA256.fullmatch(
                self.sha256
            ):
                raise ValueError("sha256 deve conter 64 dígitos hexadecimais.")
            object.__setattr__(self, "sha256", self.sha256.lower())
        if self.size is not None and (
            isinstance(self.size, bool)
            or not isinstance(self.size, int)
            or self.size < 0
        ):
            raise ValueError("size deve ser inteiro não negativo ou None.")


@dataclass(frozen=True, slots=True, eq=False)
class Evidence:
    """Unidade de comprovação editável dentro de um Project."""

    evidence_id: str
    project_id: str
    title: str
    description: str
    created_at: datetime
    updated_at: datetime
    state: EvidenceState = EvidenceState.ACTIVE
    metadata: Metadata = ()
    documents: tuple[Document, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "evidence_id", _normalized_uuid(self.evidence_id, "evidence_id")
        )
        object.__setattr__(
            self, "project_id", _normalized_uuid(self.project_id, "project_id")
        )
        object.__setattr__(self, "title", _required_text(self.title, "title"))
        object.__setattr__(
            self,
            "description",
            _normalized_text(self.description, "description"),
        )
        created = _aware_datetime(self.created_at, "created_at")
        updated = _aware_datetime(self.updated_at, "updated_at")
        if updated < created:
            raise ValueError("updated_at não pode ser anterior a created_at.")
        object.__setattr__(self, "created_at", created)
        object.__setattr__(self, "updated_at", updated)
        if not isinstance(self.state, EvidenceState):
            raise TypeError("state deve ser EvidenceState.")
        object.__setattr__(self, "metadata", _metadata(self.metadata))
        if not isinstance(self.documents, tuple) or any(
            not isinstance(item, Document) for item in self.documents
        ):
            raise TypeError("documents deve ser uma tupla de Document.")
        document_ids = tuple(item.document_id for item in self.documents)
        if len(document_ids) != len(set(document_ids)):
            raise EvidenceError("Evidence não aceita Documents duplicados.")

    @classmethod
    def create(
        cls,
        *,
        project_id: str,
        title: str,
        description: str = "",
        evidence_id: str | None = None,
        metadata: Metadata = (),
        now: datetime | None = None,
    ) -> "Evidence":
        timestamp = now or datetime.now(timezone.utc)
        return cls(
            evidence_id=evidence_id or str(uuid4()),
            project_id=project_id,
            title=title,
            description=description,
            created_at=timestamp,
            updated_at=timestamp,
            metadata=metadata,
        )

    @property
    def aggregate_id(self) -> str:
        return self.evidence_id

    def same_evidence(self, other: object) -> bool:
        return (
            isinstance(other, Evidence)
            and self.evidence_id == other.evidence_id
        )

    def edit(
        self,
        *,
        title: str | None = None,
        description: str | None = None,
        now: datetime | None = None,
    ) -> "Evidence":
        self._require_active()
        next_title = self.title if title is None else _required_text(
            title, "title"
        )
        next_description = (
            self.description
            if description is None
            else _normalized_text(description, "description")
        )
        if (
            next_title == self.title
            and next_description == self.description
        ):
            return self
        return replace(
            self,
            title=next_title,
            description=next_description,
            updated_at=now or datetime.now(timezone.utc),
        )

    def add_document(
        self,
        document: Document,
        *,
        now: datetime | None = None,
    ) -> "Evidence":
        self._require_active()
        if not isinstance(document, Document):
            raise TypeError("document deve ser Document.")
        if any(
            item.document_id == document.document_id
            for item in self.documents
        ):
            raise EvidenceError("Document já associado à Evidence.")
        return replace(
            self,
            documents=(*self.documents, document),
            updated_at=now or datetime.now(timezone.utc),
        )

    def remove_document(
        self,
        document_id: str,
        *,
        now: datetime | None = None,
    ) -> "Evidence":
        self._require_active()
        normalized = _required_text(document_id, "document_id")
        if not any(
            item.document_id == normalized for item in self.documents
        ):
            raise KeyError(normalized)
        return replace(
            self,
            documents=tuple(
                item
                for item in self.documents
                if item.document_id != normalized
            ),
            updated_at=now or datetime.now(timezone.utc),
        )

    def change_state(
        self,
        state: EvidenceState,
        *,
        now: datetime | None = None,
    ) -> "Evidence":
        if not isinstance(state, EvidenceState):
            raise TypeError("state deve ser EvidenceState.")
        if state is self.state:
            return self
        if self.state is EvidenceState.ARCHIVED:
            raise EvidenceError("Evidence arquivada não pode ser reativada.")
        return replace(
            self,
            state=state,
            updated_at=now or datetime.now(timezone.utc),
        )

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Evidence):
            return NotImplemented
        return self.evidence_id == other.evidence_id

    def __hash__(self) -> int:
        return hash(self.evidence_id)

    def _require_active(self) -> None:
        if self.state is EvidenceState.ARCHIVED:
            raise EvidenceError("Evidence arquivada não pode ser alterada.")


def _required_text(value: object, field_name: str) -> str:
    normalized = _normalized_text(value, field_name)
    if not normalized:
        raise ValueError(f"{field_name} não pode ser vazio.")
    return normalized


def _normalized_text(value: object, field_name: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{field_name} deve ser uma string.")
    return " ".join(value.split())


def _normalized_uuid(value: object, field_name: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{field_name} deve ser uma string.")
    try:
        return str(UUID(value.strip()))
    except (ValueError, AttributeError) as exc:
        raise ValueError(f"{field_name} deve ser UUID válido.") from exc


def _aware_datetime(value: object, field_name: str) -> datetime:
    if not isinstance(value, datetime) or value.tzinfo is None:
        raise TypeError(f"{field_name} deve possuir timezone.")
    return value


def _metadata(value: object) -> Metadata:
    if not isinstance(value, tuple):
        raise TypeError("metadata deve ser uma tupla.")
    if any(
        not isinstance(item, tuple)
        or len(item) != 2
        or not isinstance(item[0], str)
        or not item[0].strip()
        or not isinstance(item[1], (str, int, bool, type(None)))
        for item in value
    ):
        raise TypeError("metadata deve conter pares escalares.")
    keys = tuple(item[0].strip() for item in value)
    if len(keys) != len(set(keys)):
        raise EvidenceError("metadata não aceita chaves duplicadas.")
    return tuple(
        (key, item[1])
        for key, item in zip(keys, value, strict=True)
    )


__all__ = [
    "Document",
    "Evidence",
    "EvidenceError",
    "EvidenceState",
    "Metadata",
]
