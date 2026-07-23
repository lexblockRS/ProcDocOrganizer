"""Compilação privada de consultas para o adaptador SQLite FTS5."""

from __future__ import annotations

from .contracts import SearchMatchMode, SearchQuery, SearchSort
from .search_filters import SearchFilters


class SearchQueryBuilder:
    """Transforma contratos neutros em SQL parametrizado do índice FTS5."""

    def build_query(
        self, query: SearchQuery, fetch_limit: int
    ) -> tuple[str, tuple[object, ...]]:
        if not isinstance(query, SearchQuery):
            raise TypeError("query deve ser uma instância de SearchQuery.")
        if not isinstance(fetch_limit, int) or fetch_limit < 1:
            raise ValueError("fetch_limit deve ser um inteiro positivo.")

        options = query.options
        conditions = ["document_pages_fts MATCH ?"]
        parameters: list[object] = [self._match_expression(query)]

        if options.document_type:
            conditions.append("d.document_type = ?")
            parameters.append(options.document_type)
        if options.start_date:
            conditions.append("d.document_date >= ?")
            parameters.append(options.start_date)
        if options.end_date:
            conditions.append("d.document_date <= ?")
            parameters.append(options.end_date)
        conditions.append("d.processing_status = ?")
        parameters.append("processed")
        parameters.extend((fetch_limit, options.offset))

        return self._select_sql(conditions, self._order_by(options.sort)), tuple(
            parameters
        )

    def _match_expression(self, query: SearchQuery) -> str:
        mode = query.options.match_mode
        if mode is SearchMatchMode.EXACT_PHRASE:
            return self._quote(query.text.strip())
        terms = query.text.split()
        operator = " AND " if mode is SearchMatchMode.ALL_TERMS else " OR "
        return operator.join(self._quote(term) for term in terms)

    @staticmethod
    def _order_by(sort: SearchSort) -> str:
        primary = {
            SearchSort.RELEVANCE: "raw_score ASC",
            SearchSort.DOCUMENT_DATE_DESC: (
                "d.document_date IS NULL ASC, d.document_date DESC"
            ),
            SearchSort.DOCUMENT_NAME_ASC: "document_name COLLATE NOCASE ASC",
        }[sort]
        return (
            f"{primary}, d.sha256 ASC, "
            "CAST(f.page_number AS INTEGER) ASC"
        )

    @staticmethod
    def _select_sql(conditions: list[str], order_by: str) -> str:
        return f"""SELECT
                d.sha256 AS document_identity,
                COALESCE(d.title, d.original_filename, '') AS document_name,
                f.page_number AS page_number,
                snippet(document_pages_fts, 0, '', '', ' … ', 24) AS snippet,
                bm25(document_pages_fts) AS raw_score,
                d.document_date AS document_date,
                d.document_type AS document_type,
                d.stored_path AS file_path,
                f.text AS page_text
            FROM document_pages_fts AS f
            JOIN documents AS d ON d.id = f.document_id
            WHERE {' AND '.join(conditions)}
            ORDER BY {order_by}
            LIMIT ? OFFSET ?"""

    def build(self, filters: SearchFilters) -> tuple[str, tuple[object, ...]]:
        """Compatibilidade transitória com o compilador anterior."""
        if not isinstance(filters, SearchFilters):
            raise TypeError("filters deve ser uma instância de SearchFilters.")

        match_expression = self.build_match_expression(filters)
        conditions = ["document_pages_fts MATCH ?"]
        parameters: list[object] = [match_expression]

        if filters.document_type:
            conditions.append("d.document_type = ?")
            parameters.append(filters.document_type)
        if filters.start_date:
            conditions.append("d.document_date >= ?")
            parameters.append(filters.start_date)
        if filters.end_date:
            conditions.append("d.document_date <= ?")
            parameters.append(filters.end_date)
        if filters.only_processed:
            conditions.append("d.processing_status = ?")
            parameters.append("processed")

        parameters.extend((filters.limit, filters.offset))
        sql = self._select_sql(
            conditions,
            "raw_score ASC, d.document_date IS NULL ASC, "
            "d.document_date DESC, document_name COLLATE NOCASE ASC, "
            "d.sha256 ASC, CAST(f.page_number AS INTEGER) ASC",
        )
        return sql, tuple(parameters)

    def build_match_expression(self, filters: SearchFilters) -> str:
        if filters.match_mode == "phrase" or filters.phrase:
            phrase = filters.phrase
            if not phrase:
                raise ValueError("Uma frase não vazia é obrigatória.")
            return self._quote(phrase)
        operator = " AND " if filters.match_mode == "all" else " OR "
        return operator.join(self._quote(term) for term in filters.terms)

    @staticmethod
    def _quote(value: str) -> str:
        return f'"{value.replace(chr(34), chr(34) * 2)}"'
