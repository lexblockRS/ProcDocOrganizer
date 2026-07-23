"""Casos de uso do módulo Search, independentes de infraestrutura."""

from __future__ import annotations

from dataclasses import replace

from .contracts import (
    SearchMatchMode,
    SearchOptions,
    SearchQuery,
    SearchResultPage,
)
from .exceptions import InvalidSearchQueryError
from .search_index import SearchIndex


class SearchService:
    """Valida a entrada e delega consultas exclusivamente a SearchIndex."""

    def __init__(self, index: SearchIndex) -> None:
        if not isinstance(index, SearchIndex):
            raise TypeError("index deve implementar SearchIndex.")
        self._index = index

    def search(self, query: SearchQuery) -> SearchResultPage:
        if not isinstance(query, SearchQuery):
            raise InvalidSearchQueryError(
                "query deve ser uma instância de SearchQuery."
            )
        return self._index.search(query)

    def search_phrase(
        self, phrase: str, options: SearchOptions | None = None
    ) -> SearchResultPage:
        """Compatibilidade transitória para pesquisa de frase."""
        base = options or SearchOptions()
        return self.search(SearchQuery(
            phrase,
            replace(base, match_mode=SearchMatchMode.EXACT_PHRASE),
        ))

    def search_all_terms(
        self,
        terms: list[str] | tuple[str, ...],
        options: SearchOptions | None = None,
    ) -> SearchResultPage:
        """Compatibilidade transitória para pesquisa de todos os termos."""
        return self._search_terms(
            terms, SearchMatchMode.ALL_TERMS, options
        )

    def search_any_terms(
        self,
        terms: list[str] | tuple[str, ...],
        options: SearchOptions | None = None,
    ) -> SearchResultPage:
        """Compatibilidade transitória para pesquisa de qualquer termo."""
        return self._search_terms(
            terms, SearchMatchMode.ANY_TERM, options
        )

    def _search_terms(
        self,
        terms: list[str] | tuple[str, ...],
        mode: SearchMatchMode,
        options: SearchOptions | None,
    ) -> SearchResultPage:
        if isinstance(terms, str):
            raise InvalidSearchQueryError(
                "terms deve ser uma sequência de textos."
            )
        try:
            normalized = tuple(terms)
        except TypeError as exc:
            raise InvalidSearchQueryError(
                "terms deve ser uma sequência de textos."
            ) from exc
        if (
            not normalized
            or any(not isinstance(term, str) or not term.strip() for term in normalized)
        ):
            raise InvalidSearchQueryError(
                "terms deve conter textos não vazios."
            )
        base = options or SearchOptions()
        return self.search(SearchQuery(
            " ".join(term.strip() for term in normalized),
            replace(base, match_mode=mode),
        ))
