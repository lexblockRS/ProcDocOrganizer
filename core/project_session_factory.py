"""Composição das dependências associadas a um projeto."""

from models import Project
from services import (
    DocumentRepository,
    DocumentService,
    EvidenceService,
    SearchDocumentSourceResolver,
    SQLiteEvidenceRepository,
)
from services.processing import ProcessingRepository
from services.search import SearchService, SqliteFtsSearchIndex

from .application_registry import ApplicationRegistry
from .project_session import ProjectSession


class ProjectSessionFactory:
    """Cria uma sessão completa antes de sua ativação pela aplicação."""

    def __init__(
        self, application_registry: ApplicationRegistry | None = None
    ) -> None:
        self._application_registry = (
            application_registry
            if application_registry is not None
            else ApplicationRegistry()
        )

    def create(self, project: Project) -> ProjectSession:
        application = self._application_registry.resolve(project)
        document_repository = DocumentRepository(project)
        document_repository.load()
        document_service = DocumentService(
            document_repository,
            ProcessingRepository(project),
        )
        search_service = SearchService(
            SqliteFtsSearchIndex(project.project_path / project.database)
        )
        evidence_service = EvidenceService(
            SQLiteEvidenceRepository(project),
            SearchDocumentSourceResolver(project),
        )
        return ProjectSession(
            project=project,
            document_repository=document_repository,
            document_service=document_service,
            search_service=search_service,
            evidence_service=evidence_service,
            application=application,
        )
