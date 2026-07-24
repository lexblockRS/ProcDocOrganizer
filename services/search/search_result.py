"""Resultado imutável e independente de infraestrutura."""

from dataclasses import dataclass


@dataclass(frozen=True)
class SearchResult:
    document_identity: str
    document_title: str | None
    page_number: int
    snippet: str
    score: float
    document_date: str | None
    document_type: str | None
    file_path: str | None
    matched_terms: tuple[str, ...] = ()
