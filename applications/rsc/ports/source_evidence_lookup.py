"""Porta mínima para validar a Evidence de origem."""

from typing import Protocol


class SourceEvidenceLookup(Protocol):
    """Consulta se uma Evidence pertence ao projeto aberto."""

    def exists(self, evidence_id: str) -> bool: ...
