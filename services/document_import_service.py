"""Importação e remoção do acervo documental sem análise de conteúdo."""

from dataclasses import dataclass
import hashlib
import mimetypes
from pathlib import Path
import shutil
from uuid import uuid4

from models import Document, DocumentStatus, Project


@dataclass(frozen=True, slots=True)
class DocumentImportResult:
    document: Document
    is_duplicate: bool = False


class DocumentImportService:
    """Copia arquivos e mantém o catálogo persistente do projeto."""

    def __init__(self, project: Project, repository) -> None:
        self.project = project
        self.repository = repository

    @property
    def documents_folder(self) -> Path:
        return self.project.project_path / "documents"

    def import_file(self, source_file: str | Path) -> DocumentImportResult:
        source = Path(source_file)
        if not source.is_file():
            raise FileNotFoundError(f"Arquivo não encontrado: {source}")
        sha256 = self.calculate_sha256(source)
        existing = self.repository.find_by_hash(sha256)
        if existing is not None:
            return DocumentImportResult(existing, is_duplicate=True)

        extension = source.suffix.lower()
        stored_filename = f"{uuid4()}{extension}"
        relative_path = f"documents/{stored_filename}"
        destination = self.project.project_path / relative_path
        self.documents_folder.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
        document = Document.create(
            name=source.name,
            stored_filename=stored_filename,
            relative_path=relative_path,
            sha256=sha256,
            file_size=source.stat().st_size,
            extension=extension,
            mime_type=(
                mimetypes.guess_type(source.name)[0]
                or "application/octet-stream"
            ),
            status=DocumentStatus.IMPORTED,
        )
        try:
            self.repository.create(document)
        except Exception:
            destination.unlink(missing_ok=True)
            raise
        return DocumentImportResult(document)

    def remove(self, document_id: str) -> bool:
        document = self.repository.find_by_id(document_id)
        if document is None:
            return False
        paths = [
            self.project.project_path / document.relative_path,
            self.project.project_path / "processing" / f"{document.sha256}.json",
        ]
        staged: list[tuple[Path, Path]] = []
        try:
            for path in paths:
                if not path.exists():
                    continue
                temporary = path.with_name(
                    f".{path.name}.{uuid4()}.pending-delete"
                )
                path.replace(temporary)
                staged.append((path, temporary))
            removed = self.repository.delete(document_id)
            if removed is None:
                self._restore_staged(staged)
                return False
        except Exception:
            self._restore_staged(staged)
            raise

        for _, temporary in staged:
            temporary.unlink(missing_ok=True)
        return True

    @staticmethod
    def _restore_staged(staged: list[tuple[Path, Path]]) -> None:
        for original, temporary in reversed(staged):
            if temporary.exists():
                temporary.replace(original)

    @staticmethod
    def calculate_sha256(file_path: Path) -> str:
        digest = hashlib.sha256()
        with file_path.open("rb") as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest()
