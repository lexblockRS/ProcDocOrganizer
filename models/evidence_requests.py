"""Objetos imutáveis de entrada para operações de evidência."""

from __future__ import annotations

from dataclasses import dataclass

from .evidence import Evidence


def _normalize_request(instance, *, validate_id: bool = False) -> None:
    if validate_id:
        object.__setattr__(instance, "evidence_id", Evidence._uuid(instance.evidence_id))
    object.__setattr__(
        instance, "document_identity",
        Evidence._identity(instance.document_identity),
    )
    page = instance.page_number
    if page is not None and (
        isinstance(page, bool) or not isinstance(page, int) or page < 1
    ):
        raise ValueError("page_number deve ser um inteiro maior ou igual a 1.")
    title = Evidence._required_text(instance.title, "title")
    if len(title) > Evidence.MAX_TITLE_LENGTH:
        raise ValueError(
            f"title deve possuir no máximo {Evidence.MAX_TITLE_LENGTH} caracteres."
        )
    object.__setattr__(instance, "title", title)
    for field in ("source_snippet", "user_notes", "category"):
        object.__setattr__(
            instance,
            field,
            Evidence._optional_text(getattr(instance, field), field),
        )
    start = Evidence._date(instance.start_date, "start_date")
    end = Evidence._date(instance.end_date, "end_date")
    if start and end and start > end:
        raise ValueError("end_date não pode ser anterior a start_date.")
    object.__setattr__(instance, "start_date", start)
    object.__setattr__(instance, "end_date", end)


@dataclass(frozen=True, init=False)
class CreateEvidenceRequest:
    document_identity: str
    title: str
    page_number: int | None = None
    source_snippet: str | None = None
    user_notes: str | None = None
    category: str | None = None
    start_date: str | None = None
    end_date: str | None = None

    def __init__(
        self,
        document_identity: str | None = None,
        title: str = "",
        page_number: int | None = None,
        source_snippet: str | None = None,
        user_notes: str | None = None,
        category: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> None:
        _initialize_request(
            self, document_identity, title, page_number, source_snippet,
            user_notes, category, start_date, end_date,
        )
        _normalize_request(self)


@dataclass(frozen=True, init=False)
class UpdateEvidenceRequest:
    evidence_id: str
    document_identity: str
    title: str
    page_number: int | None = None
    source_snippet: str | None = None
    user_notes: str | None = None
    category: str | None = None
    start_date: str | None = None
    end_date: str | None = None

    def __init__(
        self,
        evidence_id: str,
        document_identity: str | None = None,
        title: str = "",
        page_number: int | None = None,
        source_snippet: str | None = None,
        user_notes: str | None = None,
        category: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> None:
        object.__setattr__(self, "evidence_id", evidence_id)
        _initialize_request(
            self, document_identity, title, page_number, source_snippet,
            user_notes, category, start_date, end_date,
        )
        _normalize_request(self, validate_id=True)


def _initialize_request(
    instance,
    document_identity,
    title,
    page_number,
    source_snippet,
    user_notes,
    category,
    start_date,
    end_date,
) -> None:
    values = {
        "document_identity": Evidence._identity(document_identity),
        "title": title,
        "page_number": page_number,
        "source_snippet": source_snippet,
        "user_notes": user_notes,
        "category": category,
        "start_date": start_date,
        "end_date": end_date,
    }
    for field, value in values.items():
        object.__setattr__(instance, field, value)
