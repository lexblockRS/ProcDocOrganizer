"""Resultados determinísticos das operações de indexação."""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class IndexingResult:
    document_sha256: str
    status: str
    document_id: int | None
    pages_indexed: int = 0
    message: str | None = None


@dataclass(frozen=True)
class RebuildError:
    file: str
    message: str


@dataclass
class RebuildReport:
    mode: str
    total: int = 0
    indexed: int = 0
    updated: int = 0
    skipped: int = 0
    removed: int = 0
    failed: int = 0
    pages_indexed: int = 0
    documents_removed_before_rebuild: int = 0
    errors: list[RebuildError] = field(default_factory=list)

    @property
    def successful(self) -> int:
        return self.indexed + self.updated + self.skipped + self.removed

    def add_result(self, result: IndexingResult) -> None:
        if result.status not in {
            "indexed", "updated", "skipped", "removed", "failed"
        }:
            raise ValueError(f"Status de indexação desconhecido: {result.status}")
        setattr(self, result.status, getattr(self, result.status) + 1)
        self.pages_indexed += result.pages_indexed

    def add_error(self, file: str, message: str) -> None:
        self.failed += 1
        self.errors.append(RebuildError(file=file, message=message))
