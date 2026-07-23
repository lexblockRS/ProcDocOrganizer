"""
Modelo de Documento do ProcDocOrganizer.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime

from models.document_type import DocumentType


@dataclass
class Document:
    """
    Representa um documento importado para um projeto.
    """

    name: str
    relative_path: str
    imported_at: str
    pages: int = 0
    sha256: str = ""
    status: str = "imported"
    document_type: str = DocumentType.UNKNOWN.value
    processed_at: str | None = None
    processing_status: str = "not_processed"

    # ------------------------------------------------------------------

    @staticmethod
    def now() -> str:
        """
        Retorna a data/hora atual em formato ISO 8601.
        """

        return datetime.now().isoformat(timespec="seconds")

    # ------------------------------------------------------------------

    @classmethod
    def create(
        cls,
        name: str,
        relative_path: str,
        pages: int = 0,
        sha256: str = "",
        status: str = "imported",
        document_type: str = DocumentType.UNKNOWN.value,
        processed_at: str | None = None,
        processing_status: str = "not_processed",
    ) -> "Document":
        """
        Cria um novo documento em memória.
        """

        return cls(
            name=name,
            relative_path=relative_path,
            imported_at=cls.now(),
            pages=pages,
            sha256=sha256,
            status=status,
            document_type=document_type,
            processed_at=processed_at,
            processing_status=processing_status,
        )

    # ------------------------------------------------------------------

    def to_dict(self) -> dict:
        """
        Converte o documento para um dicionário.
        """

        return asdict(self)

    # ------------------------------------------------------------------

    def to_json(self) -> str:
        """
        Converte o documento para JSON.
        """

        return json.dumps(
            self.to_dict(),
            indent=4,
            ensure_ascii=False,
        )

    # ------------------------------------------------------------------

    @classmethod
    def from_dict(
        cls,
        data: dict,
    ) -> "Document":
        """
        Cria um documento a partir de um dicionário.
        """

        return cls(
            name=data["name"],
            relative_path=data["relative_path"],
            imported_at=data["imported_at"],
            pages=data.get("pages", 0),
            sha256=data.get("sha256", ""),
            status=data.get("status", "imported"),
            document_type=data.get(
                "document_type",
                DocumentType.UNKNOWN.value,
            ),
            processed_at=data.get("processed_at"),
            processing_status=data.get("processing_status", "not_processed"),
        )

    # ------------------------------------------------------------------

    @classmethod
    def from_json(
        cls,
        json_text: str,
    ) -> "Document":
        """
        Cria um documento a partir de um JSON.
        """

        return cls.from_dict(
            json.loads(json_text)
        )
