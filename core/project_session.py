"""Dependências com lifetime associado a um projeto aberto."""

from dataclasses import dataclass

from contracts import Application
from models import Project
from services import DocumentRepository, DocumentService, EvidenceService
from services.search import SearchService


@dataclass(frozen=True)
class ProjectSession:
    """Contexto já composto de uma sessão ativa de projeto."""

    project: Project
    document_repository: DocumentRepository
    document_service: DocumentService
    search_service: SearchService
    evidence_service: EvidenceService
    application: Application | None = None
