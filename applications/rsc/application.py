"""Implementação mínima da Application RSC."""

from pathlib import Path

from contracts import (
    ActionContribution,
    ApplicationDescriptor,
    ApplicationLifecycleTransition,
    Version,
)
from core.session_context import SessionContext
from models import Project

from .composition import (
    RscRepositoryFactory,
    create_in_memory_rsc_repositories,
    create_rsc_project_session,
    create_sqlite_rsc_repositories,
)
from .project_session import RscProjectSession


class RscApplication:
    """Identidade e compatibilidade arquitetural da Application RSC."""

    application_id = "rsc"
    display_name = "RSC"
    descriptor = ApplicationDescriptor(
        application_id=application_id,
        display_name=display_name,
        version=Version(1, 0, 0),
        minimum_platform_version=Version(1, 0, 0),
        supported_project_schema_versions=(1,),
        description=(
            "Organização de documentos e evidências para Reconhecimento "
            "de Saberes e Competências."
        ),
    )

    def __init__(
        self,
        repository_factory: RscRepositoryFactory | None = None,
    ) -> None:
        self._repository_factory = (
            repository_factory
            if repository_factory is not None
            else create_in_memory_rsc_repositories
        )

    def can_open(self, project: Project) -> bool:
        return (
            isinstance(project, Project)
            and project.application == self.application_id
        )

    def contributions(
        self,
        session: object | None = None,
    ) -> tuple[ActionContribution, ...]:
        return ()

    def prepare(self, context: object) -> None:
        """Preserva o hook de preparação sem efeitos nesta etapa."""

    def create_session(
        self,
        context: SessionContext,
    ) -> RscProjectSession:
        """Cria a sessão RSC usando apenas recursos fornecidos pelo Host."""

        if not isinstance(context, SessionContext):
            raise TypeError("context deve ser um SessionContext.")
        return self.create_project_session(
            context.knowledge_engine,
            database_path=context.shared_services["database_path"],
        )

    def transition(
        self,
        transition: ApplicationLifecycleTransition,
    ) -> None:
        """Preserva o hook de lifecycle sem efeitos nesta etapa."""

    def dispose(self) -> None:
        """Preserva o hook de descarte sem recursos próprios persistentes."""

    def create_project_session(
        self,
        source_evidence_lookup,
        database_path: str | Path | None = None,
    ) -> RscProjectSession:
        """Cria os componentes RSC pertencentes ao projeto aberto."""

        repositories = (
            create_sqlite_rsc_repositories(database_path)
            if database_path is not None
            else self._repository_factory()
        )
        return create_rsc_project_session(
            source_evidence_lookup,
            repositories,
        )
