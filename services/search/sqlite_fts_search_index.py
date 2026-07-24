"""Adaptador somente leitura do índice SQLite FTS5."""

from __future__ import annotations

import math
from pathlib import Path
import sqlite3
import unicodedata
from collections.abc import Callable

from .contracts import SearchHit, SearchQuery, SearchResultPage
from .exceptions import (
    SearchExecutionError,
    SearchIndexCorruptedError,
    SearchIndexUnavailableError,
)
from .search_filters import SearchFilters
from .search_query_builder import SearchQueryBuilder
from .search_result import SearchResult


class SqliteFtsSearchIndex:
    """Implementa SearchIndex sem expor detalhes do SQLite ao núcleo."""

    MAX_SNIPPET_LENGTH = 240

    def __init__(
        self,
        database_path: str | Path,
        connection_factory: Callable[..., sqlite3.Connection] = sqlite3.connect,
    ) -> None:
        self._database_path = Path(database_path)
        self._connection_factory = connection_factory
        self._query_builder = SearchQueryBuilder()

    def search(self, query: SearchQuery) -> SearchResultPage:
        fetch_limit = query.options.limit + 1
        sql, parameters = self._query_builder.build_query(query, fetch_limit)
        rows = self._execute(sql, parameters)
        has_more = len(rows) > query.options.limit
        hits = tuple(
            self._to_hit(row) for row in rows[: query.options.limit]
        )
        return SearchResultPage(
            hits=hits,
            offset=query.options.offset,
            page_size=len(hits),
            total_hits=None,
            has_more=has_more,
        )

    def search_legacy(self, filters: SearchFilters) -> tuple[SearchResult, ...]:
        """Adapta o resultado concreto para consumidores legados."""
        sql, parameters = self._query_builder.build(filters)
        rows = self._execute(sql, parameters)
        return tuple(self._to_legacy_result(row, filters) for row in rows)

    def _execute(
        self, sql: str, parameters: tuple[object, ...]
    ) -> list[sqlite3.Row]:
        connection = self._open_read_only()
        try:
            return connection.execute(sql, parameters).fetchall()
        except sqlite3.DatabaseError as exc:
            self._raise_query_error(exc)
        finally:
            connection.close()

    def _open_read_only(self) -> sqlite3.Connection:
        if not self._database_path.is_file():
            raise SearchIndexUnavailableError(
                "O índice de pesquisa não está disponível."
            )
        try:
            connection = self._connection_factory(
                f"{self._database_path.resolve().as_uri()}?mode=ro",
                uri=True,
            )
            connection.row_factory = sqlite3.Row
            return connection
        except sqlite3.DatabaseError as exc:
            if self._is_corruption(exc):
                raise SearchIndexCorruptedError(
                    "O índice de pesquisa está corrompido."
                ) from exc
            raise SearchIndexUnavailableError(
                "Não foi possível abrir o índice de pesquisa."
            ) from exc

    @classmethod
    def _raise_query_error(cls, exc: sqlite3.DatabaseError) -> None:
        message = str(exc).lower()
        if cls._is_corruption(exc) or "no such table" in message:
            raise SearchIndexCorruptedError(
                "A estrutura do índice de pesquisa é inválida."
            ) from exc
        if "no such module" in message and "fts" in message:
            raise SearchIndexUnavailableError(
                "O mecanismo de pesquisa textual não está disponível."
            ) from exc
        raise SearchExecutionError(
            "Não foi possível executar a pesquisa."
        ) from exc

    @staticmethod
    def _is_corruption(exc: sqlite3.DatabaseError) -> bool:
        message = str(exc).lower()
        return any(
            marker in message
            for marker in (
                "database disk image is malformed",
                "file is not a database",
                "database corrupt",
                "malformed database schema",
            )
        )

    def _to_hit(self, row: sqlite3.Row) -> SearchHit:
        return SearchHit(
            document_identity=str(row["document_identity"]),
            document_name=str(row["document_name"] or ""),
            page_number=int(row["page_number"]),
            snippet=self._snippet(row["snippet"]),
            score=self._normalize_score(row["raw_score"]),
        )

    def _to_legacy_result(
        self, row: sqlite3.Row, filters: SearchFilters
    ) -> SearchResult:
        candidates = (filters.phrase,) if filters.phrase else filters.terms
        normalized_text = self._normalize(row["page_text"])
        matched = tuple(
            term
            for term in candidates
            if term and self._normalize(term) in normalized_text
        )
        raw_score = row["raw_score"]
        return SearchResult(
            document_identity=str(row["document_identity"]),
            document_title=row["document_name"],
            page_number=int(row["page_number"]),
            snippet=self._snippet(row["snippet"]),
            score=float(raw_score) if raw_score is not None else 0.0,
            document_date=row["document_date"],
            document_type=row["document_type"],
            file_path=row["file_path"],
            matched_terms=matched,
        )

    @classmethod
    def _snippet(cls, value: object) -> str:
        snippet = " ".join(str(value or "").split())
        if len(snippet) > cls.MAX_SNIPPET_LENGTH:
            return f"{snippet[:cls.MAX_SNIPPET_LENGTH - 1].rstrip()}…"
        return snippet

    @staticmethod
    def _normalize_score(value: object) -> float | None:
        try:
            raw_score = float(value)
        except (TypeError, ValueError):
            return None
        if not math.isfinite(raw_score):
            return None
        # O FTS5 ordena BM25 de forma crescente. A inversão preserva a ordem
        # e oferece a semântica pública "maior significa mais relevante".
        return -raw_score

    @staticmethod
    def _normalize(value: str) -> str:
        decomposed = unicodedata.normalize("NFKD", value.casefold())
        return "".join(
            char for char in decomposed if not unicodedata.combining(char)
        )
