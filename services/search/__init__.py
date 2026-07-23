"""API pública do módulo Search."""

from .contracts import (
    SearchHit,
    SearchMatchMode,
    SearchOptions,
    SearchQuery,
    SearchResultPage,
    SearchSort,
)
from .exceptions import (
    InvalidIndexDocumentError,
    InvalidSearchQueryError,
    SearchError,
    SearchExecutionError,
    SearchIndexCorruptedError,
    SearchIndexMaintenanceError,
    SearchIndexRebuildError,
    SearchIndexSourceError,
    SearchIndexUnavailableError,
    SearchIndexWriteError,
    UnsupportedSearchFeatureError,
)
from .maintenance_contracts import (
    IndexMaintenanceIssue,
    IndexRebuildReport,
    IndexReconcileReport,
    SearchIndexDocument,
    SearchIndexPage,
    SearchIndexStatus,
)
from .legacy_indexed_search_service import LegacyIndexedSearchService
from .search_filters import SearchFilters
from .search_index import SearchIndex
from .search_index_maintainer import SearchIndexMaintainer
from .search_index_source import SearchIndexSource
from .search_result import SearchResult
from .search_service import SearchService
from .sqlite_fts_search_index import SqliteFtsSearchIndex
from .sqlite_fts_index_maintainer import SqliteFtsIndexMaintainer

__all__ = [
    "IndexMaintenanceIssue",
    "IndexRebuildReport",
    "IndexReconcileReport",
    "InvalidIndexDocumentError",
    "InvalidSearchQueryError",
    "LegacyIndexedSearchService",
    "SearchError",
    "SearchExecutionError",
    "SearchFilters",
    "SearchHit",
    "SearchIndex",
    "SearchIndexCorruptedError",
    "SearchIndexDocument",
    "SearchIndexMaintenanceError",
    "SearchIndexMaintainer",
    "SearchIndexPage",
    "SearchIndexRebuildError",
    "SearchIndexSource",
    "SearchIndexSourceError",
    "SearchIndexStatus",
    "SearchIndexUnavailableError",
    "SearchIndexWriteError",
    "SearchMatchMode",
    "SearchOptions",
    "SearchQuery",
    "SearchResult",
    "SearchResultPage",
    "SearchService",
    "SearchSort",
    "SqliteFtsSearchIndex",
    "SqliteFtsIndexMaintainer",
    "UnsupportedSearchFeatureError",
]
