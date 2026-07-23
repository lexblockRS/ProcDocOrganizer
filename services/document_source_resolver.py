"""Porta de resolução da disponibilidade documental para Evidence."""

from typing import Protocol


class DocumentSourceResolver(Protocol):
    """Resolve exclusivamente se uma fonte documental está disponível."""

    def is_document_available(self, document_identity: str) -> bool: ...
