"""Inspeção genérica de arquivos binários referenciados por documentos RSC."""

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
from pathlib import Path

SHA256_ALGORITHM = "sha256"
HASH_CHUNK_SIZE = 1024 * 1024

FILE_EXTENSION_KEY = "file_extension"
FILE_SIZE_KEY = "file_size"
LAST_MODIFIED_AT_KEY = "last_modified_at"
MANAGED_STATUS_KEY = "managed_status"
REFERENCE_MODE_KEY = "reference_mode"


@dataclass(frozen=True, slots=True)
class DocumentFileIdentity:
    path: str
    exists: bool
    is_file: bool
    extension: str | None = None
    size: int | None = None
    last_modified_at: str | None = None
    sha256: str | None = None


class DocumentHashService:
    """Obtém identidade sem interpretar o conteúdo do arquivo."""

    def inspect(self, path: str | Path) -> DocumentFileIdentity:
        candidate = Path(path)
        normalized = str(candidate)
        if not candidate.exists():
            return DocumentFileIdentity(normalized, False, False)
        if not candidate.is_file():
            return DocumentFileIdentity(normalized, True, False)
        stat = candidate.stat()
        digest = hashlib.sha256()
        with candidate.open("rb") as stream:
            for chunk in iter(lambda: stream.read(HASH_CHUNK_SIZE), b""):
                digest.update(chunk)
        modified = datetime.fromtimestamp(
            stat.st_mtime, tz=timezone.utc
        ).isoformat()
        return DocumentFileIdentity(
            normalized,
            True,
            True,
            candidate.suffix.lower() or None,
            stat.st_size,
            modified,
            digest.hexdigest(),
        )
