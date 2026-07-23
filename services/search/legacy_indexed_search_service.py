"""Facade transitória para consumidores do SearchResult anterior."""

from .search_filters import SearchFilters
from .sqlite_fts_search_index import SqliteFtsSearchIndex


class LegacyIndexedSearchService:
    """Preserva a API visual enquanto ela ainda usa SearchResult legado."""

    MAX_SNIPPET_LENGTH = SqliteFtsSearchIndex.MAX_SNIPPET_LENGTH

    def __init__(self, index: SqliteFtsSearchIndex) -> None:
        if not isinstance(index, SqliteFtsSearchIndex):
            raise TypeError("index deve ser um SqliteFtsSearchIndex.")
        self._index = index

    def search(self, filters: SearchFilters):
        return self._index.search_legacy(filters)

    def search_phrase(self, phrase: str, filters: SearchFilters | None = None):
        base = filters or SearchFilters(phrase=phrase, match_mode="phrase")
        return self.search(SearchFilters(
            phrase=phrase,
            match_mode="phrase",
            document_type=base.document_type,
            start_date=base.start_date,
            end_date=base.end_date,
            only_processed=base.only_processed,
            limit=base.limit,
            offset=base.offset,
        ))

    def search_all_terms(self, terms, filters: SearchFilters | None = None):
        return self._search_terms(terms, "all", filters)

    def search_any_terms(self, terms, filters: SearchFilters | None = None):
        return self._search_terms(terms, "any", filters)

    def _search_terms(self, terms, mode, filters):
        base = filters or SearchFilters(terms=terms, match_mode=mode)
        return self.search(SearchFilters(
            terms=terms,
            match_mode=mode,
            document_type=base.document_type,
            start_date=base.start_date,
            end_date=base.end_date,
            only_processed=base.only_processed,
            limit=base.limit,
            offset=base.offset,
        ))
