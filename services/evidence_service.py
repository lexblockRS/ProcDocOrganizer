"""Regras de aplicação e porta de entrada para evidências."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Callable
from uuid import uuid4

from models import CreateEvidenceRequest, Evidence, UpdateEvidenceRequest
from .evidence_repository_errors import (
    DuplicateEvidenceError,
    EvidenceDocumentNotFoundError as RepositoryDocumentNotFoundError,
    EvidenceNotFoundError as RepositoryNotFoundError,
    EvidenceRepositoryError,
)
from .evidence_repository_port import EvidenceRepository
from .document_source_resolver import DocumentSourceResolver


class EvidenceServiceError(RuntimeError):
    """Erro compreensível pela camada de apresentação."""


class EvidenceValidationError(EvidenceServiceError):
    pass


class EvidenceNotFoundError(EvidenceServiceError):
    pass


class EvidenceDocumentUnavailableError(EvidenceServiceError):
    pass


class EvidenceClockError(EvidenceServiceError):
    pass


class EvidenceSourceStatus(str, Enum):
    AVAILABLE = "available"
    UNAVAILABLE = "unavailable"


class EvidenceService:
    """Controla identidade, tempo e regras de aplicação das evidências."""

    def __init__(
        self,
        repository: EvidenceRepository,
        source_resolver: DocumentSourceResolver,
        id_factory: Callable[[], str] | None = None,
        now_factory: Callable[[], str] | None = None,
    ) -> None:
        self._repository = repository
        self._source_resolver = source_resolver
        self._id_factory = id_factory or (lambda: str(uuid4()))
        self._now_factory = now_factory or Evidence.now

    def create(self, request: CreateEvidenceRequest) -> Evidence:
        if not isinstance(request, CreateEvidenceRequest):
            raise EvidenceValidationError("request deve ser CreateEvidenceRequest.")
        try:
            self._require_document_available(request.document_identity)
            instant = Evidence._timestamp(self._now_factory(), "now")
            evidence = Evidence(
                id=self._id_factory(), created_at=instant, updated_at=instant,
                **self._request_values(request),
            )
            return self._repository.add(evidence)
        except Exception as exc:
            self._raise_mapped(exc)

    def get(self, evidence_id: str) -> Evidence | None:
        return self._execute(lambda: self._repository.get_by_id(evidence_id))

    def get_required(self, evidence_id: str) -> Evidence:
        evidence = self.get(evidence_id)
        if evidence is None:
            raise EvidenceNotFoundError("Evidência não encontrada.")
        return evidence

    def list_all(self) -> tuple[Evidence, ...]:
        return tuple(self._execute(self._repository.list_all))

    def list_by_document(self, document_identity: str) -> tuple[Evidence, ...]:
        return tuple(
            self._execute(
                lambda: self._repository.list_by_document(document_identity)
            )
        )

    def update(self, request: UpdateEvidenceRequest) -> Evidence:
        if not isinstance(request, UpdateEvidenceRequest):
            raise EvidenceValidationError("request deve ser UpdateEvidenceRequest.")
        current = self.get_required(request.evidence_id)
        try:
            if request.document_identity != current.document_identity:
                self._require_document_available(request.document_identity)
            instant = Evidence._timestamp(self._now_factory(), "now")
            self._require_non_regressing_clock(current.created_at, instant)
            updated = Evidence(
                id=current.id,
                created_at=current.created_at,
                updated_at=instant,
                **self._request_values(request),
            )
            return self._repository.update(updated)
        except Exception as exc:
            self._raise_mapped(exc)

    def delete(self, evidence_id: str) -> bool:
        return bool(self._execute(lambda: self._repository.delete(evidence_id)))

    def exists(self, evidence_id: str) -> bool:
        return bool(self._execute(lambda: self._repository.exists(evidence_id)))

    def count(self) -> int:
        return int(self._execute(self._repository.count))

    def get_source_status(self, evidence_id: str) -> EvidenceSourceStatus:
        evidence = self.get_required(evidence_id)
        available = self._execute(
            lambda: self._source_resolver.is_document_available(
                evidence.document_identity
            )
        )
        return (
            EvidenceSourceStatus.AVAILABLE
            if available
            else EvidenceSourceStatus.UNAVAILABLE
        )

    def is_source_available(self, evidence_or_id: Evidence | str) -> bool:
        evidence = (
            evidence_or_id
            if isinstance(evidence_or_id, Evidence)
            else self.get_required(evidence_or_id)
        )
        return bool(self._execute(
            lambda: self._source_resolver.is_document_available(
                evidence.document_identity
            )
        ))

    def is_document_available(self, document_identity: str) -> bool:
        """Consulta uma fonte candidata ainda sem Evidence persistida."""
        try:
            identity = Evidence._identity(document_identity)
        except (ValueError, TypeError) as exc:
            raise EvidenceValidationError(
                "Identidade documental inválida."
            ) from exc
        return bool(self._execute(
            lambda: self._source_resolver.is_document_available(identity)
        ))

    def _require_document_available(self, document_identity: str) -> None:
        if not self._source_resolver.is_document_available(document_identity):
            raise RepositoryDocumentNotFoundError(
                "O documento vinculado não existe no índice."
            )

    def find_potential_duplicates(
        self,
        document_identity: str,
        page_number: int | None,
        title: str,
    ) -> tuple[Evidence, ...]:
        probe = CreateEvidenceRequest(
            document_identity=document_identity,
            page_number=page_number,
            title=title,
        )
        normalized_title = probe.title.casefold()
        return tuple(
            evidence
            for evidence in self.list_by_document(probe.document_identity)
            if evidence.page_number == probe.page_number
            and evidence.title.casefold() == normalized_title
        )

    @staticmethod
    def _request_values(request) -> dict:
        return {
            field: getattr(request, field)
            for field in (
                "document_identity", "page_number", "title", "source_snippet",
                "user_notes", "category", "start_date", "end_date",
            )
        }

    @staticmethod
    def _require_non_regressing_clock(created_at: str, updated_at: str) -> None:
        try:
            if datetime.fromisoformat(updated_at) < datetime.fromisoformat(created_at):
                raise EvidenceClockError(
                    "O relógio atual é anterior à criação da evidência."
                )
        except TypeError as exc:
            raise EvidenceClockError(
                "O relógio atual usa um padrão de timezone incompatível."
            ) from exc

    def _execute(self, operation):
        try:
            return operation()
        except Exception as exc:
            self._raise_mapped(exc)

    @staticmethod
    def _raise_mapped(exc: Exception):
        if isinstance(exc, EvidenceServiceError):
            raise exc
        if isinstance(exc, RepositoryNotFoundError):
            raise EvidenceNotFoundError("Evidência não encontrada.") from exc
        if isinstance(exc, RepositoryDocumentNotFoundError):
            raise EvidenceDocumentUnavailableError(
                "O documento vinculado não está disponível."
            ) from exc
        if isinstance(exc, DuplicateEvidenceError):
            raise EvidenceValidationError(
                "O identificador gerado já está em uso."
            ) from exc
        if isinstance(exc, (ValueError, TypeError)):
            raise EvidenceValidationError("Dados de evidência inválidos.") from exc
        if isinstance(exc, EvidenceRepositoryError):
            raise EvidenceServiceError(
                "Não foi possível concluir a operação de evidência."
            ) from exc
        raise EvidenceServiceError(
            "Não foi possível concluir a operação de evidência."
        ) from exc
