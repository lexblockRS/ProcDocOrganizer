"""
Modelo de Documento do ProcDocOrganizer.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime
from enum import Enum
from pathlib import PurePosixPath
from uuid import uuid4

from models.document_type import DocumentType


class DocumentStatus(str, Enum):
    IMPORTED = "imported"


class DocumentProcessingStatus(str, Enum):
    NOT_PROCESSED = "not_processed"
    PENDING = "pending"
    PROCESSING = "processing"
    PROCESSED = "processed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    OCR_REQUIRED = "ocr_required"


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
    processing_status: str = DocumentProcessingStatus.NOT_PROCESSED
    id: str = ""
    original_filename: str = ""
    stored_filename: str = ""
    file_size: int = 0
    extension: str = ""
    mime_type: str = "application/octet-stream"
    created_at: str = ""
    updated_at: str = ""

    def __post_init__(self) -> None:
        if not self.id:
            self.id = str(uuid4())
        if not self.original_filename:
            self.original_filename = self.name
        if not self.stored_filename:
            self.stored_filename = PurePosixPath(
                self.relative_path
            ).name
        if not self.extension:
            self.extension = PurePosixPath(
                self.original_filename
            ).suffix.lower()
        if not self.created_at:
            self.created_at = self.imported_at
        if not self.updated_at:
            self.updated_at = self.created_at

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
        processing_status: str = DocumentProcessingStatus.NOT_PROCESSED,
        stored_filename: str = "",
        file_size: int = 0,
        extension: str = "",
        mime_type: str = "application/octet-stream",
    ) -> "Document":
        """
        Cria um novo documento em memória.
        """

        now = cls.now()
        return cls(
            name=name,
            relative_path=relative_path,
            imported_at=now,
            pages=pages,
            sha256=sha256,
            status=status,
            document_type=document_type,
            processed_at=processed_at,
            processing_status=processing_status,
            id=str(uuid4()),
            original_filename=name,
            stored_filename=stored_filename,
            file_size=file_size,
            extension=extension,
            mime_type=mime_type,
            created_at=now,
            updated_at=now,
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
            processing_status=data.get(
                "processing_status",
                DocumentProcessingStatus.NOT_PROCESSED,
            ),
            id=data.get("id", ""),
            original_filename=data.get("original_filename", ""),
            stored_filename=data.get("stored_filename", ""),
            file_size=data.get("file_size", 0),
            extension=data.get("extension", ""),
            mime_type=data.get("mime_type", "application/octet-stream"),
            created_at=data.get("created_at", ""),
            updated_at=data.get("updated_at", ""),
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
