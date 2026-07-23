"""Porta neutra da fonte canônica consumida pela manutenção."""

from collections.abc import Iterable
from typing import Protocol, runtime_checkable

from .maintenance_contracts import SearchIndexDocument


@runtime_checkable
class SearchIndexSource(Protocol):
    def iter_documents(self) -> Iterable[SearchIndexDocument]: ...

    def get_document(self, identity: str) -> SearchIndexDocument | None: ...
