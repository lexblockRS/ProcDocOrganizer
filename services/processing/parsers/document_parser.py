"""Contrato mínimo para parsers documentais."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Mapping

from ..processing_result import ProcessingResult


class DocumentParser(ABC):
    """Produz a representação canônica de uma origem suportada."""

    parser_id: str

    @abstractmethod
    def supports(self, source: Path) -> bool:
        """Informa se este parser reconhece a origem."""

    @abstractmethod
    def parse(
        self,
        source: Path,
        context: Mapping[str, Any] | None = None,
    ) -> ProcessingResult:
        """Interpreta a origem e retorna um resultado canônico."""
