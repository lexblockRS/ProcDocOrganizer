"""Snapshot factual imutável destinado a futuros consumidores normativos."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import asdict, dataclass
from datetime import date, datetime
from enum import Enum
from pathlib import Path
from types import MappingProxyType
from typing import Any, Protocol

from applications.rsc.models import (
    Activity,
    FunctionalAssignmentEvidence,
    FunctionalExercise,
)
from models import Document, Evidence, Project


class EvaluationContextError(ValueError):
    """Falha estrutural ao construir um snapshot factual."""


class DuplicateEvaluationObjectError(EvaluationContextError):
    """Duas projeções factuais possuem a mesma identidade."""


class InvalidEvaluationReferenceError(EvaluationContextError):
    """Uma relação factual aponta para uma identidade ausente."""


class IncompleteEvaluationTraceabilityError(EvaluationContextError):
    """A cadeia factual não alcança sua origem documental."""


class _ListAllRepository(Protocol):
    def list_all(self) -> object: ...


@dataclass(frozen=True, slots=True)
class EvaluationProject:
    project_name: str
    project_path: str
    created_at: str
    last_opened_at: str
    application: str
    format_version: int
    database: str


@dataclass(frozen=True, slots=True)
class EvaluationActivity:
    activity_id: str
    description: str
    state: str
    functional_assignment_evidence_ids: tuple[str, ...]
    functional_exercise_ids: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class EvaluationFunctionalExercise:
    id: str
    person_id: str
    exercise_type_code: str
    exercise_type_label: str
    role: str
    organization: str
    unit: str | None
    administrative_reference: str | None
    start_date: str
    end_date: str | None
    status: str
    functional_assignment_evidence_ids: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class EvaluationFunctionalAssignmentEvidence:
    id: str
    person_id: str
    source_evidence_id: str
    exercise_type_code: str
    exercise_type_label: str
    role: str
    organization: str
    start_date: str | None
    end_date: str | None
    unit: str | None
    administrative_reference: str | None
    status: str


@dataclass(frozen=True, slots=True)
class EvaluationEvidence:
    id: str
    document_identity: str
    page_number: int | None
    title: str
    source_snippet: str | None
    user_notes: str | None
    category: str | None
    start_date: str | None
    end_date: str | None
    created_at: str
    updated_at: str


@dataclass(frozen=True, slots=True)
class EvaluationDocument:
    id: str
    document_identity: str
    name: str
    relative_path: str
    imported_at: str
    pages: int
    status: str
    document_type: str
    processed_at: str | None
    processing_status: str
    original_filename: str
    stored_filename: str
    file_size: int
    extension: str
    mime_type: str
    created_at: str
    updated_at: str


@dataclass(frozen=True, slots=True)
class EvaluationContext:
    """Snapshot factual completo, sem acesso a serviços ou repositories."""

    project: EvaluationProject
    activities: tuple[EvaluationActivity, ...]
    functional_exercises: tuple[EvaluationFunctionalExercise, ...]
    functional_assignment_evidences: tuple[
        EvaluationFunctionalAssignmentEvidence, ...
    ]
    evidences: tuple[EvaluationEvidence, ...]
    documents: tuple[EvaluationDocument, ...]
    metadata: Mapping[str, Any]

    def __post_init__(self) -> None:
        if not isinstance(self.project, EvaluationProject):
            raise TypeError("project deve ser EvaluationProject.")
        collections = (
            ("activities", self.activities, EvaluationActivity),
            (
                "functional_exercises",
                self.functional_exercises,
                EvaluationFunctionalExercise,
            ),
            (
                "functional_assignment_evidences",
                self.functional_assignment_evidences,
                EvaluationFunctionalAssignmentEvidence,
            ),
            ("evidences", self.evidences, EvaluationEvidence),
            ("documents", self.documents, EvaluationDocument),
        )
        for name, values, expected_type in collections:
            if not isinstance(values, tuple):
                raise TypeError(f"{name} deve ser uma tupla.")
            if any(
                not isinstance(value, expected_type)
                for value in values
            ):
                raise TypeError(
                    f"{name} contém projeção de tipo inválido."
                )
        if not isinstance(self.metadata, MappingProxyType):
            raise TypeError("metadata deve ser um snapshot imutável.")
        EvaluationContextBuilder._validate(
            self.activities,
            self.functional_exercises,
            self.functional_assignment_evidences,
            self.evidences,
            self.documents,
        )

    def to_dict(self) -> dict[str, Any]:
        """Produz uma cópia serializável sem expor o estado do snapshot."""

        return {
            "project": asdict(self.project),
            "activities": [asdict(item) for item in self.activities],
            "functional_exercises": [
                asdict(item) for item in self.functional_exercises
            ],
            "functional_assignment_evidences": [
                asdict(item)
                for item in self.functional_assignment_evidences
            ],
            "evidences": [asdict(item) for item in self.evidences],
            "documents": [asdict(item) for item in self.documents],
            "metadata": _thaw(self.metadata),
        }


class EvaluationContextBuilder:
    """Lê fontes factuais e encerra o acesso a elas antes da entrega."""

    def __init__(
        self,
        activity_repository: _ListAllRepository,
        functional_exercise_repository: _ListAllRepository,
        functional_assignment_evidence_repository: _ListAllRepository,
        evidence_repository: _ListAllRepository,
        document_repository: _ListAllRepository,
    ) -> None:
        self._activity_repository = activity_repository
        self._functional_exercise_repository = (
            functional_exercise_repository
        )
        self._functional_assignment_evidence_repository = (
            functional_assignment_evidence_repository
        )
        self._evidence_repository = evidence_repository
        self._document_repository = document_repository

    def build(
        self,
        project: Project,
        metadata: Mapping[str, Any] | None = None,
    ) -> EvaluationContext:
        if not isinstance(project, Project):
            raise TypeError("project deve ser Project.")

        activities = tuple(
            self._activity(item)
            for item in self._read(
                self._activity_repository,
                Activity,
                "activities",
            )
        )
        exercises = tuple(
            self._functional_exercise(item)
            for item in self._read(
                self._functional_exercise_repository,
                FunctionalExercise,
                "functional_exercises",
            )
        )
        assignments = tuple(
            self._functional_assignment_evidence(item)
            for item in self._read(
                self._functional_assignment_evidence_repository,
                FunctionalAssignmentEvidence,
                "functional_assignment_evidences",
            )
        )
        evidences = tuple(
            self._evidence(item)
            for item in self._read(
                self._evidence_repository,
                Evidence,
                "evidences",
            )
        )
        documents = tuple(
            self._document(item)
            for item in self._read(
                self._document_repository,
                Document,
                "documents",
            )
        )

        self._validate(
            activities,
            exercises,
            assignments,
            evidences,
            documents,
        )
        return EvaluationContext(
            project=self._project(project),
            activities=activities,
            functional_exercises=exercises,
            functional_assignment_evidences=assignments,
            evidences=evidences,
            documents=documents,
            metadata=_freeze_mapping(metadata or {}),
        )

    @staticmethod
    def _read(
        repository: _ListAllRepository,
        expected_type: type,
        collection_name: str,
    ) -> tuple[object, ...]:
        values = repository.list_all()
        if not isinstance(values, (tuple, list)):
            raise EvaluationContextError(
                f"{collection_name} deve ser uma coleção ordenada."
            )
        snapshot = tuple(values)
        if any(not isinstance(value, expected_type) for value in snapshot):
            raise EvaluationContextError(
                f"{collection_name} contém objeto de tipo inválido."
            )
        return snapshot

    @staticmethod
    def _project(project: Project) -> EvaluationProject:
        return EvaluationProject(
            project_name=project.project_name,
            project_path=str(project.project_path),
            created_at=project.created_at,
            last_opened_at=project.last_opened_at,
            application=project.application,
            format_version=project.format_version,
            database=project.database,
        )

    @staticmethod
    def _activity(activity: Activity) -> EvaluationActivity:
        return EvaluationActivity(
            activity_id=activity.activity_id,
            description=activity.description,
            state=_enum_value(activity.state),
            functional_assignment_evidence_ids=tuple(
                str(item)
                for item in activity.functional_assignment_evidence_ids
            ),
            functional_exercise_ids=tuple(
                str(item) for item in activity.functional_exercise_ids
            ),
        )

    @staticmethod
    def _functional_exercise(
        exercise: FunctionalExercise,
    ) -> EvaluationFunctionalExercise:
        return EvaluationFunctionalExercise(
            id=str(exercise.id),
            person_id=exercise.person_id,
            exercise_type_code=exercise.exercise_type.code,
            exercise_type_label=exercise.exercise_type.label,
            role=exercise.role.name,
            organization=exercise.context.organization,
            unit=exercise.context.unit,
            administrative_reference=exercise.context.reference,
            start_date=exercise.period.start_date.isoformat(),
            end_date=(
                exercise.period.end_date.isoformat()
                if exercise.period.end_date is not None
                else None
            ),
            status=_enum_value(exercise.status),
            functional_assignment_evidence_ids=tuple(
                str(item)
                for item in exercise.functional_assignment_evidence_ids
            ),
        )

    @staticmethod
    def _functional_assignment_evidence(
        assignment: FunctionalAssignmentEvidence,
    ) -> EvaluationFunctionalAssignmentEvidence:
        return EvaluationFunctionalAssignmentEvidence(
            id=str(assignment.id),
            person_id=assignment.person_id,
            source_evidence_id=str(assignment.source_evidence_reference),
            exercise_type_code=assignment.exercise_type_code,
            exercise_type_label=assignment.exercise_type_label,
            role=assignment.role,
            organization=assignment.organization,
            start_date=_date_text(assignment.start_date),
            end_date=_date_text(assignment.end_date),
            unit=assignment.unit,
            administrative_reference=assignment.administrative_reference,
            status=_enum_value(assignment.status),
        )

    @staticmethod
    def _evidence(evidence: Evidence) -> EvaluationEvidence:
        return EvaluationEvidence(
            id=evidence.id,
            document_identity=evidence.document_identity,
            page_number=evidence.page_number,
            title=evidence.title,
            source_snippet=evidence.source_snippet,
            user_notes=evidence.user_notes,
            category=evidence.category,
            start_date=evidence.start_date,
            end_date=evidence.end_date,
            created_at=evidence.created_at,
            updated_at=evidence.updated_at,
        )

    @staticmethod
    def _document(document: Document) -> EvaluationDocument:
        return EvaluationDocument(
            id=document.id,
            document_identity=document.sha256,
            name=document.name,
            relative_path=document.relative_path,
            imported_at=document.imported_at,
            pages=document.pages,
            status=_enum_value(document.status),
            document_type=_enum_value(document.document_type),
            processed_at=document.processed_at,
            processing_status=_enum_value(document.processing_status),
            original_filename=document.original_filename,
            stored_filename=document.stored_filename,
            file_size=document.file_size,
            extension=document.extension,
            mime_type=document.mime_type,
            created_at=document.created_at,
            updated_at=document.updated_at,
        )

    @classmethod
    def _validate(
        cls,
        activities: tuple[EvaluationActivity, ...],
        exercises: tuple[EvaluationFunctionalExercise, ...],
        assignments: tuple[EvaluationFunctionalAssignmentEvidence, ...],
        evidences: tuple[EvaluationEvidence, ...],
        documents: tuple[EvaluationDocument, ...],
    ) -> None:
        activity_ids = cls._unique(
            (item.activity_id for item in activities),
            "Activity",
        )
        exercise_ids = cls._unique(
            (item.id for item in exercises),
            "FunctionalExercise",
        )
        assignment_ids = cls._unique(
            (item.id for item in assignments),
            "FunctionalAssignmentEvidence",
        )
        evidence_ids = cls._unique(
            (item.id for item in evidences),
            "Evidence",
        )
        cls._unique((item.id for item in documents), "Document")
        document_identities = cls._unique(
            (
                item.document_identity.lower()
                for item in documents
            ),
            "Document.document_identity",
        )
        del activity_ids

        for activity in activities:
            cls._require_references(
                activity.functional_exercise_ids,
                exercise_ids,
                f"Activity {activity.activity_id} -> FunctionalExercise",
            )
            cls._require_references(
                activity.functional_assignment_evidence_ids,
                assignment_ids,
                (
                    f"Activity {activity.activity_id} -> "
                    "FunctionalAssignmentEvidence"
                ),
            )
        for exercise in exercises:
            cls._require_references(
                exercise.functional_assignment_evidence_ids,
                assignment_ids,
                f"FunctionalExercise {exercise.id} -> "
                "FunctionalAssignmentEvidence",
            )
        for assignment in assignments:
            cls._require_references(
                (assignment.source_evidence_id,),
                evidence_ids,
                f"FunctionalAssignmentEvidence {assignment.id} -> Evidence",
            )
        for evidence in evidences:
            if evidence.document_identity.lower() not in document_identities:
                raise IncompleteEvaluationTraceabilityError(
                    f"Evidence {evidence.id} referencia Document ausente: "
                    f"{evidence.document_identity}."
                )

    @staticmethod
    def _unique(values: object, label: str) -> set[str]:
        result: set[str] = set()
        for value in values:
            if not isinstance(value, str) or not value:
                raise EvaluationContextError(
                    f"{label} possui identidade vazia ou inválida."
                )
            if value in result:
                raise DuplicateEvaluationObjectError(
                    f"{label} duplicado: {value}."
                )
            result.add(value)
        return result

    @staticmethod
    def _require_references(
        references: tuple[str, ...],
        available: set[str],
        relation: str,
    ) -> None:
        if len(references) != len(set(references)):
            raise DuplicateEvaluationObjectError(
                f"{relation} contém referência duplicada."
            )
        missing = tuple(
            reference
            for reference in references
            if reference not in available
        )
        if missing:
            raise InvalidEvaluationReferenceError(
                f"{relation} referencia identidade ausente: "
                f"{', '.join(missing)}."
            )


def _enum_value(value: object) -> str:
    return str(value.value) if isinstance(value, Enum) else str(value)


def _date_text(value: date | None) -> str | None:
    return value.isoformat() if value is not None else None


def _freeze_mapping(values: Mapping[str, Any]) -> Mapping[str, Any]:
    if not isinstance(values, Mapping):
        raise TypeError("metadata deve ser um mapeamento.")
    frozen: dict[str, Any] = {}
    for key, value in values.items():
        if not isinstance(key, str) or not key:
            raise TypeError("metadata aceita somente chaves textuais.")
        frozen[key] = _freeze(value)
    return MappingProxyType(frozen)


def _freeze(value: Any) -> Any:
    if isinstance(value, Mapping):
        return _freeze_mapping(value)
    if isinstance(value, (list, tuple)):
        return tuple(_freeze(item) for item in value)
    if isinstance(value, (set, frozenset)):
        return frozenset(_freeze(item) for item in value)
    if isinstance(value, Enum):
        return _freeze(value.value)
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    raise TypeError(
        f"metadata contém valor não serializável: {type(value).__name__}."
    )


def _thaw(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {key: _thaw(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_thaw(item) for item in value]
    if isinstance(value, frozenset):
        return sorted((_thaw(item) for item in value), key=repr)
    return value


__all__ = [
    "DuplicateEvaluationObjectError",
    "EvaluationActivity",
    "EvaluationContext",
    "EvaluationContextBuilder",
    "EvaluationContextError",
    "EvaluationDocument",
    "EvaluationEvidence",
    "EvaluationFunctionalAssignmentEvidence",
    "EvaluationFunctionalExercise",
    "EvaluationProject",
    "IncompleteEvaluationTraceabilityError",
    "InvalidEvaluationReferenceError",
]
