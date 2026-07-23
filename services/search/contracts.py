"""Contratos públicos e neutros do módulo Search."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from enum import Enum
import math

from .exceptions import InvalidSearchQueryError


class SearchMatchMode(str, Enum):
    ALL_TERMS = "all_terms"
    ANY_TERM = "any_term"
    EXACT_PHRASE = "exact_phrase"


class SearchSort(str, Enum):
    RELEVANCE = "relevance"
    DOCUMENT_DATE_DESC = "document_date_desc"
    DOCUMENT_NAME_ASC = "document_name_asc"


@dataclass(frozen=True)
class SearchOptions:
    DEFAULT_LIMIT = 50
    MAX_LIMIT = 200

    limit: int = DEFAULT_LIMIT
    offset: int = 0
    sort: SearchSort = SearchSort.RELEVANCE
    match_mode: SearchMatchMode = SearchMatchMode.ALL_TERMS
    document_type: str | None = None
    start_date: str | None = None
    end_date: str | None = None

    def __post_init__(self) -> None:
        if (
            isinstance(self.limit, bool)
            or not isinstance(self.limit, int)
            or not 1 <= self.limit <= self.MAX_LIMIT
        ):
            raise InvalidSearchQueryError(
                f"limit deve estar entre 1 e {self.MAX_LIMIT}."
            )
        if (
            isinstance(self.offset, bool)
            or not isinstance(self.offset, int)
            or self.offset < 0
        ):
            raise InvalidSearchQueryError(
                "offset deve ser um inteiro não negativo."
            )
        if not isinstance(self.sort, SearchSort):
            raise InvalidSearchQueryError("sort deve ser um SearchSort válido.")
        if not isinstance(self.match_mode, SearchMatchMode):
            raise InvalidSearchQueryError(
                "match_mode deve ser um SearchMatchMode válido."
            )
        object.__setattr__(
            self, "document_type",
            self._optional_text(self.document_type, "document_type"),
        )
        start = self._optional_date(self.start_date, "start_date")
        end = self._optional_date(self.end_date, "end_date")
        if start and end and start > end:
            raise InvalidSearchQueryError(
                "start_date não pode ser posterior a end_date."
            )
        object.__setattr__(self, "start_date", start)
        object.__setattr__(self, "end_date", end)

    @staticmethod
    def _optional_text(value: object, field_name: str) -> str | None:
        if value is None:
            return None
        if not isinstance(value, str) or not value.strip():
            raise InvalidSearchQueryError(
                f"{field_name} deve ser um texto não vazio."
            )
        return value.strip()

    @staticmethod
    def _optional_date(value: object, field_name: str) -> str | None:
        if value is None:
            return None
        if not isinstance(value, str):
            raise InvalidSearchQueryError(
                f"{field_name} deve usar o formato ISO AAAA-MM-DD."
            )
        try:
            return date.fromisoformat(value.strip()).isoformat()
        except ValueError as exc:
            raise InvalidSearchQueryError(
                f"{field_name} deve usar o formato ISO AAAA-MM-DD."
            ) from exc


@dataclass(frozen=True)
class SearchQuery:
    text: str
    options: SearchOptions = field(default_factory=SearchOptions)

    def __post_init__(self) -> None:
        if not isinstance(self.text, str) or not self.text.strip():
            raise InvalidSearchQueryError(
                "O texto da pesquisa não pode ser vazio."
            )
        if not isinstance(self.options, SearchOptions):
            raise InvalidSearchQueryError(
                "options deve ser uma instância de SearchOptions."
            )


@dataclass(frozen=True)
class SearchHit:
    document_identity: str
    document_name: str
    page_number: int
    snippet: str
    score: float | None = None

    def __post_init__(self) -> None:
        if (
            not isinstance(self.document_identity, str)
            or not self.document_identity.strip()
        ):
            raise ValueError("document_identity deve ser um texto não vazio.")
        if not isinstance(self.document_name, str):
            raise TypeError("document_name deve ser texto.")
        if (
            isinstance(self.page_number, bool)
            or not isinstance(self.page_number, int)
            or self.page_number < 1
        ):
            raise ValueError("page_number deve ser um inteiro a partir de 1.")
        if not isinstance(self.snippet, str):
            raise TypeError("snippet deve ser texto.")
        if self.score is not None and (
            isinstance(self.score, bool)
            or not isinstance(self.score, (int, float))
            or not math.isfinite(float(self.score))
        ):
            raise ValueError("score deve ser um número finito ou None.")
        object.__setattr__(self, "document_identity", self.document_identity.strip())
        if self.score is not None:
            object.__setattr__(self, "score", float(self.score))


@dataclass(frozen=True)
class SearchResultPage:
    hits: tuple[SearchHit, ...]
    offset: int
    page_size: int
    total_hits: int | None
    has_more: bool

    def __post_init__(self) -> None:
        try:
            hits = tuple(self.hits)
        except TypeError as exc:
            raise TypeError("hits deve ser uma sequência de SearchHit.") from exc
        if any(not isinstance(hit, SearchHit) for hit in hits):
            raise TypeError("hits deve conter apenas SearchHit.")
        if (
            isinstance(self.offset, bool)
            or not isinstance(self.offset, int)
            or self.offset < 0
        ):
            raise ValueError("offset deve ser um inteiro não negativo.")
        if (
            isinstance(self.page_size, bool)
            or not isinstance(self.page_size, int)
            or self.page_size < 0
        ):
            raise ValueError("page_size deve ser um inteiro não negativo.")
        if self.page_size != len(hits):
            raise ValueError("page_size deve corresponder à quantidade de hits.")
        if self.total_hits is not None and (
            isinstance(self.total_hits, bool)
            or not isinstance(self.total_hits, int)
            or self.total_hits < 0
        ):
            raise ValueError("total_hits deve ser não negativo ou None.")
        if not isinstance(self.has_more, bool):
            raise TypeError("has_more deve ser booleano.")
        if self.total_hits is not None:
            expected = self.offset + self.page_size < self.total_hits
            if self.has_more != expected:
                raise ValueError("has_more diverge de total_hits.")
        object.__setattr__(self, "hits", hits)
