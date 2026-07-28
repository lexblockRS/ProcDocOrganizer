"""Repositório do contêiner versionado .pdop."""

from dataclasses import dataclass
from datetime import datetime, timezone
import json
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any
from zipfile import BadZipFile, ZIP_DEFLATED, ZipFile

from applications.rsc.domain import RscActivity, RscDocument, RscEvidence, RscProcess

from .serializers import (
    ActivitySerializer,
    DocumentSerializer,
    EvidenceSerializer,
    ProcessSerializer,
    ProjectSerializer,
)
from .schema_migration import (
    CURRENT_SCHEMA_VERSION,
    MigrationPipeline,
    create_default_migration_pipeline,
)

SCHEMA_VERSION = CURRENT_SCHEMA_VERSION
APPLICATION_VERSION = "1.5"
GENERATOR = "ProcDocOrganizer RSC"

_FILES = (
    "project.json",
    "process.json",
    "documents.json",
    "activities.json",
    "evidence.json",
    "metadata.json",
)
_SCHEMAS = {
    "process.json": "rsc.process.collection/1",
    "documents.json": "rsc.document.collection/1",
    "activities.json": "rsc.activity.collection/1",
    "evidence.json": "rsc.evidence.collection/1",
}


class InvalidProjectFileError(ValueError):
    """O arquivo não representa um projeto .pdop compatível."""


@dataclass(frozen=True, slots=True)
class ProjectSnapshot:
    processes: tuple[RscProcess, ...]
    documents: tuple[RscDocument, ...]
    evidence: tuple[RscEvidence, ...]
    catalog_ids: tuple[str, ...]


class ProjectRepository:
    """Salva, valida e carrega um projeto RSC sem conhecer UI."""

    def __init__(
        self, migration_pipeline: MigrationPipeline | None = None
    ) -> None:
        self._migration_pipeline = (
            migration_pipeline
            if migration_pipeline is not None
            else create_default_migration_pipeline()
        )
        if not isinstance(self._migration_pipeline, MigrationPipeline):
            raise TypeError(
                "migration_pipeline deve ser MigrationPipeline."
            )

    def save(
        self,
        destination: str | Path,
        snapshot: ProjectSnapshot,
    ) -> dict[str, Any]:
        path = self._save_path(destination)
        now = datetime.now(timezone.utc)
        created_at = self._existing_created_at(path) or now
        activities = tuple(
            activity
            for process in snapshot.processes
            for activity in process.activities
        )
        payloads = {
            "project.json": ProjectSerializer.dump(
                snapshot.processes, snapshot.catalog_ids
            ),
            "process.json": self._collection(
                _SCHEMAS["process.json"],
                [ProcessSerializer.dump(value) for value in snapshot.processes],
            ),
            "documents.json": self._collection(
                _SCHEMAS["documents.json"],
                [DocumentSerializer.dump(value) for value in snapshot.documents],
            ),
            "activities.json": self._collection(
                _SCHEMAS["activities.json"],
                [ActivitySerializer.dump(value) for value in activities],
            ),
            "evidence.json": self._collection(
                _SCHEMAS["evidence.json"],
                [EvidenceSerializer.dump(value) for value in snapshot.evidence],
            ),
            "metadata.json": {
                "schema": "rsc.metadata/1",
                "schema_version": SCHEMA_VERSION,
                "application_version": APPLICATION_VERSION,
                "created_at": created_at.isoformat(),
                "saved_at": now.isoformat(),
                "generator": GENERATOR,
            },
        }
        temporary: Path | None = None
        try:
            with NamedTemporaryFile(
                prefix=f".{path.name}.",
                suffix=".tmp",
                dir=path.parent,
                delete=False,
            ) as stream:
                temporary = Path(stream.name)
            with ZipFile(temporary, "w", ZIP_DEFLATED) as archive:
                for name in _FILES:
                    archive.writestr(
                        name,
                        json.dumps(
                            payloads[name],
                            ensure_ascii=False,
                            indent=2,
                            sort_keys=True,
                        ),
                    )
            temporary.replace(path)
        finally:
            if temporary is not None and temporary.exists():
                temporary.unlink()
        return payloads["metadata.json"]

    def load(self, source: str | Path) -> ProjectSnapshot:
        try:
            return self._load_validated(source)
        except InvalidProjectFileError:
            raise
        except (KeyError, TypeError, ValueError) as exc:
            raise InvalidProjectFileError(
                "conteúdo do projeto .pdop inválido."
            ) from exc

    def _load_validated(self, source: str | Path) -> ProjectSnapshot:
        payloads = self.validate(source)
        activities = tuple(
            ActivitySerializer.load(value)
            for value in payloads["activities.json"]["items"]
        )
        activity_map = self._unique_map(activities, "atividade")
        documents = tuple(
            DocumentSerializer.load(value)
            for value in payloads["documents.json"]["items"]
        )
        evidence = tuple(
            EvidenceSerializer.load(value)
            for value in payloads["evidence.json"]["items"]
        )
        processes = tuple(
            ProcessSerializer.load(value, activity_map)
            for value in payloads["process.json"]["items"]
        )
        self._verify_graph(processes, documents, evidence)
        project = payloads["project.json"]
        process_ids = tuple(value.id for value in processes)
        if tuple(project.get("process_ids", ())) != process_ids:
            raise InvalidProjectFileError("project.json não corresponde aos processos.")
        catalog = project.get("catalog")
        if not isinstance(catalog, dict):
            raise InvalidProjectFileError("catálogo do projeto inválido.")
        return ProjectSnapshot(
            processes,
            documents,
            evidence,
            tuple(catalog.get("criterion_ids", ())),
        )

    def validate(self, source: str | Path) -> dict[str, Any]:
        path = Path(source)
        if not path.exists():
            raise FileNotFoundError(path)
        if not path.is_file():
            raise InvalidProjectFileError("o projeto .pdop deve ser um arquivo.")
        try:
            with ZipFile(path, "r") as archive:
                names = set(archive.namelist())
                missing = set(_FILES) - names
                if missing:
                    raise InvalidProjectFileError(
                        "arquivos obrigatórios ausentes: "
                        + ", ".join(sorted(missing))
                    )
                payloads = {
                    name: json.loads(archive.read(name).decode("utf-8"))
                    for name in _FILES
                }
        except (BadZipFile, OSError, UnicodeError, json.JSONDecodeError) as exc:
            raise InvalidProjectFileError("arquivo .pdop inválido.") from exc
        metadata = payloads["metadata.json"]
        if not isinstance(metadata, dict):
            raise InvalidProjectFileError("metadata.json inválido.")
        payloads = self._migration_pipeline.migrate(
            payloads, metadata.get("schema_version")
        )
        if payloads["project.json"].get("schema") != ProjectSerializer.schema:
            raise InvalidProjectFileError("schema de project.json incompatível.")
        for name, schema in _SCHEMAS.items():
            value = payloads[name]
            if (
                not isinstance(value, dict)
                or value.get("schema") != schema
                or not isinstance(value.get("items"), list)
            ):
                raise InvalidProjectFileError(f"schema de {name} incompatível.")
        return payloads

    @staticmethod
    def _collection(schema: str, items: list[dict[str, Any]]) -> dict[str, Any]:
        return {"schema": schema, "items": items}

    @staticmethod
    def _save_path(destination: str | Path) -> Path:
        path = Path(destination)
        if path.suffix.lower() != ".pdop":
            raise ValueError("o destino deve possuir extensão .pdop.")
        if not path.parent.exists() or not path.parent.is_dir():
            raise FileNotFoundError(path.parent)
        if path.exists() and not path.is_file():
            raise ValueError("o destino deve ser um arquivo.")
        return path

    def _existing_created_at(self, path: Path) -> datetime | None:
        if not path.exists():
            return None
        try:
            metadata = self.validate(path)["metadata.json"]
            value = datetime.fromisoformat(metadata["created_at"])
            return value if value.tzinfo is not None else None
        except (InvalidProjectFileError, KeyError, TypeError, ValueError):
            return None

    @staticmethod
    def _unique_map(values: tuple[Any, ...], label: str) -> dict[str, Any]:
        result = {value.id: value for value in values}
        if len(result) != len(values):
            raise InvalidProjectFileError(f"IDs de {label} duplicados.")
        return result

    def _verify_graph(
        self,
        processes: tuple[RscProcess, ...],
        documents: tuple[RscDocument, ...],
        evidence: tuple[RscEvidence, ...],
    ) -> None:
        self._unique_map(processes, "processo")
        document_map = self._unique_map(documents, "documento")
        evidence_map = self._unique_map(evidence, "evidência")
        activity_ids = {
            activity.id for process in processes for activity in process.activities
        }
        if len(activity_ids) != sum(len(value.activities) for value in processes):
            raise InvalidProjectFileError("IDs de atividade duplicados.")
        for process in processes:
            missing = set(process.document_ids) - document_map.keys()
            if missing:
                raise InvalidProjectFileError("processo referencia documento ausente.")
            for activity in process.activities:
                if set(activity.evidence_ids) - evidence_map.keys():
                    raise InvalidProjectFileError(
                        "atividade referencia evidência ausente."
                    )
        for item in evidence:
            if item.activity_id not in activity_ids:
                raise InvalidProjectFileError("evidência referencia atividade ausente.")
            if set(item.document_ids) - document_map.keys():
                raise InvalidProjectFileError("evidência referencia documento ausente.")
