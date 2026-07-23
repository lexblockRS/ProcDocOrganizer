"""Porta canônica de persistência do módulo Evidence."""

from __future__ import annotations

from typing import Protocol

from models import Evidence


class EvidenceRepository(Protocol):
    """Operações canônicas exigidas pelos casos de uso de Evidence."""

    def add(self, evidence: Evidence) -> Evidence: ...

    def get_by_id(self, evidence_id: str) -> Evidence | None: ...

    def list_all(self) -> list[Evidence]: ...

    def list_by_document(self, document_identity: str) -> list[Evidence]: ...

    def update(self, evidence: Evidence) -> Evidence: ...

    def delete(self, evidence_id: str) -> bool: ...

    def exists(self, evidence_id: str) -> bool: ...

    def count(self) -> int: ...
