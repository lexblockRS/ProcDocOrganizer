"""Serviços de indexação textual persistente."""

from .document_indexer import DocumentIndexer, IndexingValidationError
from .indexing_result import IndexingResult, RebuildError, RebuildReport
from .processing_search_index_source import ProcessingSearchIndexSource

__all__ = [
    "DocumentIndexer", "IndexingResult", "IndexingValidationError",
    "ProcessingSearchIndexSource", "RebuildError", "RebuildReport",
]
