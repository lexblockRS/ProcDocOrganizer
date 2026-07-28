"""Casos de uso de persistência integral da sessão RSC."""

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from applications.rsc.infrastructure import ProjectRepository, ProjectSnapshot

from ._support import require_command


@dataclass(frozen=True, slots=True)
class SaveProjectCommand:
    destination: str | Path


@dataclass(frozen=True, slots=True)
class LoadProjectCommand:
    source: str | Path


@dataclass(frozen=True, slots=True)
class SaveProjectResult:
    destination: Path
    saved_at: datetime
    process_count: int
    document_count: int
    activity_count: int
    evidence_count: int


@dataclass(frozen=True, slots=True)
class LoadProjectResult:
    source: Path
    loaded_at: datetime
    process_count: int
    document_count: int
    activity_count: int
    evidence_count: int


class SaveProjectUseCase:
    def __init__(
        self, processes, documents, evidence, catalog, repository: ProjectRepository
    ) -> None:
        self._processes = processes
        self._documents = documents
        self._evidence = evidence
        self._catalog = catalog
        self._repository = repository

    def execute(self, command: SaveProjectCommand) -> SaveProjectResult:
        require_command(command, SaveProjectCommand)
        processes = self._processes.list_processes()
        documents = self._documents.list_documents()
        evidence = self._evidence.list_all()
        catalog_ids = tuple(
            item.id for item in self._catalog.list_criteria()
        )
        metadata = self._repository.save(
            command.destination,
            ProjectSnapshot(processes, documents, evidence, catalog_ids),
        )
        return SaveProjectResult(
            Path(command.destination),
            datetime.fromisoformat(metadata["saved_at"]),
            len(processes),
            len(documents),
            sum(len(value.activities) for value in processes),
            len(evidence),
        )


class LoadProjectUseCase:
    def __init__(
        self, processes, documents, evidence, catalog, repository: ProjectRepository
    ) -> None:
        self._processes = processes
        self._documents = documents
        self._evidence = evidence
        self._catalog = catalog
        self._repository = repository

    def execute(self, command: LoadProjectCommand) -> LoadProjectResult:
        require_command(command, LoadProjectCommand)
        snapshot = self._repository.load(command.source)
        expected_catalog = tuple(
            item.id for item in self._catalog.list_criteria()
        )
        if snapshot.catalog_ids != expected_catalog:
            raise ValueError("catálogo RSC do projeto é incompatível.")

        processes = self._processes
        documents = self._documents
        evidence = self._evidence
        processes.clear()
        documents.clear()
        evidence.clear()
        for item in snapshot.documents:
            documents.add_document(item)
        for item in snapshot.evidence:
            evidence.create_evidence(
                id=item.id,
                activity_id=item.activity_id,
                document_ids=item.document_ids,
                description=item.description,
                status=item.status,
                justification=item.justification,
                created_at=item.created_at,
                updated_at=item.updated_at,
            )
        for item in snapshot.processes:
            processes.add_process(item)
        return LoadProjectResult(
            Path(command.source),
            datetime.now().astimezone(),
            len(snapshot.processes),
            len(snapshot.documents),
            sum(len(value.activities) for value in snapshot.processes),
            len(snapshot.evidence),
        )
