"""Porta de consulta do índice de pesquisa."""

from typing import Protocol, runtime_checkable

from .contracts import SearchQuery, SearchResultPage


@runtime_checkable
class SearchIndex(Protocol):
    def search(self, query: SearchQuery) -> SearchResultPage:
        """Executa uma consulta somente leitura."""
