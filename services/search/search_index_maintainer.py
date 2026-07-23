"""Porta exclusivamente de escrita e manutenção do índice."""

from typing import Protocol, runtime_checkable

from .maintenance_contracts import (
    IndexRebuildReport,
    IndexReconcileReport,
    SearchIndexDocument,
    SearchIndexStatus,
)
from .search_index_source import SearchIndexSource


@runtime_checkable
class SearchIndexMaintainer(Protocol):
    def upsert(self, document: SearchIndexDocument) -> None: ...

    def remove(self, document_identity: str) -> bool: ...

    def rebuild(self, source: SearchIndexSource) -> IndexRebuildReport: ...

    def reconcile(self, source: SearchIndexSource) -> IndexReconcileReport: ...

    def inspect(self) -> SearchIndexStatus: ...
