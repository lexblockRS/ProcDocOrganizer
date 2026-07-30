"""Dependências com lifetime associado a um projeto aberto."""

from dataclasses import dataclass, field

from applications.rsc import RscProjectSession
from contracts import (
    Application,
    ApplicationDescriptor,
    ApplicationLifecycleState,
    ApplicationModule,
    create_transitional_application_descriptor,
)
from models import Project
from services import (
    DocumentImportService,
    DocumentMetadataService,
    DocumentRepository,
    DocumentService,
    EvidenceService,
)
from services.search import SearchService
from services.indexing import DocumentIndexer
from services.processing import DocumentProcessor

from .application_runtime import ApplicationRuntime
from .platform_session import PlatformSession
from .project_context import ProjectContext
from .session_context import SessionContext


@dataclass(frozen=True)
class ProjectSession:
    """Contexto já composto de uma sessão ativa de projeto."""

    project: Project
    document_repository: DocumentRepository
    document_service: DocumentService
    document_import_service: DocumentImportService
    document_processor: DocumentProcessor
    document_indexer: DocumentIndexer
    search_service: SearchService
    evidence_service: EvidenceService
    application: Application | None = None
    rsc_session: RscProjectSession | None = None
    platform_session: PlatformSession = field(init=False)

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "platform_session",
            self._create_platform_session(),
        )

    def _create_platform_session(self) -> PlatformSession:
        module = (
            self.application
            if isinstance(self.application, ApplicationModule)
            else None
        )
        descriptor = self._application_descriptor(module)
        project_context = ProjectContext(
            project=self.project,
            application_id=self.project.application,
            project_path=self.project.project_path,
            project_version=self.project.format_version,
            permanent_metadata={
                "project_name": self.project.project_name,
                "created_at": self.project.created_at,
                "database": self.project.database,
            },
        )
        session_context = SessionContext(
            document_engine=self.document_service,
            knowledge_engine=self.evidence_service,
            shared_services={
                "document_repository": self.document_repository,
                "document_service": self.document_service,
                "document_import_service": self.document_import_service,
                "document_processor": self.document_processor,
                "document_indexer": self.document_indexer,
                "search_service": self.search_service,
                "evidence_service": self.evidence_service,
                "database_path": (
                    self.project.project_path / self.project.database
                ),
            },
        )
        runtime = ApplicationRuntime(
            descriptor=descriptor,
            module=module,
            lifecycle_state=ApplicationLifecycleState.REGISTERED,
            application_session=None,
        )
        return PlatformSession(
            project_context=project_context,
            session_context=session_context,
            application_runtime=runtime,
        )

    def bind_application_session(
        self,
        application_session: object,
    ) -> None:
        """Publica a sessão modular e sincroniza aliases transitórios."""

        self.platform_session.application_runtime.application_session = (
            application_session
        )
        if isinstance(application_session, RscProjectSession):
            object.__setattr__(
                self,
                "rsc_session",
                application_session,
            )

    @property
    def document_metadata_service(self) -> DocumentMetadataService | None:
        return getattr(self, "_document_metadata_service", None)

    def bind_document_metadata_service(
        self,
        service: DocumentMetadataService,
    ) -> None:
        object.__setattr__(self, "_document_metadata_service", service)

    def _application_descriptor(
        self,
        module: ApplicationModule | None,
    ) -> ApplicationDescriptor:
        if module is not None:
            descriptor = module.descriptor
            if descriptor.application_id != self.project.application:
                raise ValueError(
                    "O descriptor da Application não corresponde ao projeto."
                )
            return descriptor

        display_name = getattr(self.application, "display_name", None)
        if not isinstance(display_name, str) or not display_name.strip():
            display_name = self.project.application
        return create_transitional_application_descriptor(
            application_id=self.project.application,
            display_name=display_name,
            supported_project_schema_versions=(
                self.project.format_version,
            ),
        )
