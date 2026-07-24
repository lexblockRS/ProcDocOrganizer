"""Serviços de indexação textual persistente."""

from .document_indexer import DocumentIndexer, IndexingValidationError
from .indexing_result import IndexingResult, RebuildError, RebuildReport

__all__ = [
    "DocumentIndexer", "IndexingResult", "IndexingValidationError",
    "RebuildError", "RebuildReport",
]
