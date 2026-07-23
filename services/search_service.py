"""Adaptador de compatibilidade da UI para a busca SQLite/FTS5."""

from models import Document, Project, SearchResult
from services.search import (
    SearchMatchMode,
    SearchOptions,
    SearchQuery,
    SearchService as CoreSearchService,
    SqliteFtsSearchIndex,
)


class SearchService:
    """Mantém o contrato visual existente sem expor SQL à interface."""

    def search(
        self,
        project: Project,
        documents: list[Document],
        query: str,
    ) -> list[SearchResult]:
        if not isinstance(query, str) or not query.strip():
            return []

        documents_by_sha256 = self._documents_by_sha256(documents)
        index = SqliteFtsSearchIndex(project.project_path / project.database)
        page = CoreSearchService(index).search(SearchQuery(
            query.strip(),
            SearchOptions(match_mode=SearchMatchMode.EXACT_PHRASE),
        ))
        results = []

        for indexed_result in page.hits:
            for document in documents_by_sha256.get(
                indexed_result.document_identity, []
            ):
                results.append(SearchResult(
                    document=document,
                    page=indexed_result.page_number,
                    excerpt=indexed_result.snippet,
                ))

        return results

    @staticmethod
    def _documents_by_sha256(
        documents: list[Document],
    ) -> dict[str, list[Document]]:
        documents_by_sha256 = {}
        for document in documents:
            if document.sha256:
                documents_by_sha256.setdefault(document.sha256, []).append(document)
        return documents_by_sha256
