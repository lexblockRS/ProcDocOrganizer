"""Composição das dependências associadas a um projeto."""

from models import Project
from services import (
    DocumentRepository,
    DocumentImportService,
    DocumentService,
    EvidenceService,
    SearchDocumentSourceResolver,
    SQLiteEvidenceRepository,
)
from services.processing import ProcessingRepository
from services.processing import DocumentProcessor
from services.indexing import DocumentIndexer
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
        application_module = self._application_registry.resolve_module(
            project
        )
        database_path = project.project_path / project.database
        document_repository = DocumentRepository(project)
        document_repository.load()
        document_indexer = DocumentIndexer(database_path)
        document_processor = DocumentProcessor(
            document_indexer=document_indexer
        )
        document_service = DocumentService(
            document_repository,
            ProcessingRepository(project),
        )
        search_service = SearchService(
            SqliteFtsSearchIndex(database_path)
        )
        evidence_service = EvidenceService(
            SQLiteEvidenceRepository(project),
            SearchDocumentSourceResolver(project),
        )
        document_import_service = DocumentImportService(
            project, document_repository
        )
        session = ProjectSession(
            project=project,
            document_repository=document_repository,
            document_service=document_service,
            document_import_service=document_import_service,
            document_processor=document_processor,
            document_indexer=document_indexer,
            search_service=search_service,
            evidence_service=evidence_service,
            application=application,
            rsc_session=None,
        )
        runtime = session.platform_session.application_runtime
        runtime.prepare(session.platform_session.session_context)
        application_session = runtime.create_session(
            session.platform_session.session_context
        )
        if application_session is not None:
            session.bind_application_session(application_session)
        return session
