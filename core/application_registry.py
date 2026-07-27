"""Catálogo explícito e neutro de Applications da plataforma."""

from collections.abc import Iterable
from dataclasses import dataclass, replace

from contracts import (
    Application,
    ApplicationDescriptor,
    ApplicationModule,
    Version,
    create_transitional_application_descriptor,
)
from models import Project
from models.project import PROJECT_FORMAT_VERSION


class ApplicationRegistryError(RuntimeError):
    """Erro neutro de registro ou resolução de Application."""


class DuplicateApplicationError(ApplicationRegistryError):
    """Indica colisão entre identidades ou aliases do catálogo."""


class ApplicationNotRegisteredError(ApplicationRegistryError):
    """Indica que o projeto referencia uma Application desconhecida."""


class IncompatibleApplicationError(ApplicationRegistryError):
    """Indica incompatibilidade da Application com a plataforma ou projeto."""


@dataclass(frozen=True, slots=True)
class _CatalogEntry:
    canonical_id: str
    descriptor: ApplicationDescriptor
    registered_object: object
    application: Application | None
    module: ApplicationModule | None
    aliases: frozenset[str]


class ApplicationRegistry:
    """Mantém uma entrada lógica por Application legada ou módulo."""

    LEGACY_APPLICATION_IDS = frozenset({"ProcDocOrganizer"})
    DEFAULT_PLATFORM_VERSION = Version(1, 0, 0)

    def __init__(
        self,
        applications: Iterable[Application | ApplicationModule] = (),
        *,
        platform_version: Version = DEFAULT_PLATFORM_VERSION,
        project_schema_version: int = PROJECT_FORMAT_VERSION,
    ) -> None:
        if not isinstance(platform_version, Version):
            raise TypeError("platform_version deve ser uma Version.")
        if (
            isinstance(project_schema_version, bool)
            or not isinstance(project_schema_version, int)
            or project_schema_version < 1
        ):
            raise ValueError(
                "project_schema_version deve ser um inteiro positivo."
            )
        self._platform_version = platform_version
        self._project_schema_version = project_schema_version
        self._entries: dict[str, _CatalogEntry] = {}
        self._aliases: dict[str, str] = {}
        for application in applications:
            self.register(application)

    @property
    def applications(self) -> tuple[Application, ...]:
        """Preserva a coleção pública das Applications legadas."""

        return tuple(
            entry.application
            for entry in self._ordered_entries()
            if entry.application is not None
        )

    @property
    def modules(self) -> tuple[ApplicationModule, ...]:
        """Retorna módulos na ordem determinística dos IDs canônicos."""

        return tuple(
            entry.module
            for entry in self._ordered_entries()
            if entry.module is not None
        )

    @property
    def descriptors(self) -> tuple[ApplicationDescriptor, ...]:
        """Retorna um descriptor por entrada lógica do catálogo."""

        return tuple(
            entry.descriptor for entry in self._ordered_entries()
        )

    def register(
        self,
        application: Application | ApplicationModule,
        *,
        aliases: Iterable[str] = (),
    ) -> None:
        """Registra uma Application legada ou reconhece um módulo."""

        if isinstance(application, ApplicationModule):
            self.register_module(application, aliases=aliases)
            return
        self._register_legacy(application, aliases)

    def register_module(
        self,
        module: ApplicationModule,
        *,
        aliases: Iterable[str] = (),
    ) -> None:
        """Registra um ApplicationModule sem criar sua sessão."""

        if not isinstance(module, ApplicationModule):
            raise TypeError(
                "module deve implementar ApplicationModule."
            )
        descriptor = getattr(module, "descriptor", None)
        if not isinstance(descriptor, ApplicationDescriptor):
            raise TypeError(
                "ApplicationModule deve fornecer ApplicationDescriptor."
            )

        declared_id = getattr(module, "application_id", None)
        if (
            declared_id is not None
            and self._required_id(declared_id)
            != descriptor.application_id
        ):
            raise ValueError(
                "application_id do módulo diverge do descriptor."
            )
        declared_name = getattr(module, "display_name", None)
        if (
            declared_name is not None
            and self._required_display_name(declared_name)
            != descriptor.display_name
        ):
            raise ValueError(
                "display_name do módulo diverge do descriptor."
            )

        self._validate_descriptor(descriptor)
        legacy_application = (
            module if isinstance(module, Application) else None
        )
        self._add_entry(
            descriptor=descriptor,
            registered_object=module,
            application=legacy_application,
            module=module,
            aliases=aliases,
        )

    def get(
        self,
        application_id: str,
    ) -> Application | ApplicationModule | None:
        """Obtém o objeto registrado pela identidade ou alias."""

        entry = self._get_entry(application_id)
        return entry.registered_object if entry is not None else None

    def get_module(
        self,
        application_id: str,
    ) -> ApplicationModule | None:
        entry = self._get_entry(application_id)
        return entry.module if entry is not None else None

    def get_descriptor(
        self,
        application_id: str,
    ) -> ApplicationDescriptor | None:
        entry = self._get_entry(application_id)
        return entry.descriptor if entry is not None else None

    def resolve(
        self,
        project: Project,
    ) -> Application | ApplicationModule | None:
        """Preserva a resolução legada e aceita módulos registrados."""

        entry, requested_id = self._resolve_entry(project)
        if entry is None:
            return None
        self._validate_project_schema(entry, project)

        if entry.application is not None:
            compatibility_project = (
                project
                if requested_id == entry.canonical_id
                else replace(project, application=entry.canonical_id)
            )
            if not entry.application.can_open(compatibility_project):
                raise IncompatibleApplicationError(
                    "Application incompatível com o projeto: "
                    f"{requested_id}."
                )
        return entry.registered_object

    def resolve_module(
        self,
        project: Project,
    ) -> ApplicationModule | None:
        """Resolve somente a visão modular da entrada do projeto."""

        entry, _requested_id = self._resolve_entry(project)
        if entry is None:
            return None
        self._validate_project_schema(entry, project)
        return entry.module

    def _register_legacy(
        self,
        application: Application,
        aliases: Iterable[str],
    ) -> None:
        application_id = self._required_id(
            getattr(application, "application_id", None)
        )
        display_name = self._required_display_name(
            getattr(application, "display_name", None)
        )
        if not callable(getattr(application, "can_open", None)):
            raise TypeError("Application deve implementar can_open(project).")
        if not callable(getattr(application, "contributions", None)):
            raise TypeError("Application deve implementar contributions().")

        descriptor = create_transitional_application_descriptor(
            application_id=application_id,
            display_name=display_name,
            version=getattr(application, "version", None),
            minimum_platform_version=getattr(
                application,
                "minimum_platform_version",
                None,
            ),
            supported_project_schema_versions=tuple(
                getattr(
                    application,
                    "supported_project_schema_versions",
                    (self._project_schema_version,),
                )
            ),
            required_capabilities=getattr(
                application,
                "required_capabilities",
                frozenset(),
            ),
            provided_capabilities=getattr(
                application,
                "provided_capabilities",
                frozenset(),
            ),
            description=getattr(application, "description", ""),
        )
        self._validate_descriptor(descriptor)
        self._add_entry(
            descriptor=descriptor,
            registered_object=application,
            application=application,
            module=None,
            aliases=aliases,
        )

    def _add_entry(
        self,
        *,
        descriptor: ApplicationDescriptor,
        registered_object: object,
        application: Application | None,
        module: ApplicationModule | None,
        aliases: Iterable[str],
    ) -> None:
        canonical_id = descriptor.application_id
        normalized_aliases = frozenset(
            self._required_id(alias) for alias in aliases
        )
        protected_aliases = (
            normalized_aliases & self.LEGACY_APPLICATION_IDS
        )
        if protected_aliases:
            raise DuplicateApplicationError(
                "Alias colide com identidade histórica: "
                f"{sorted(protected_aliases)[0]}."
            )
        if canonical_id in normalized_aliases:
            raise DuplicateApplicationError(
                f"Alias repete o ID canônico: {canonical_id}."
            )

        claimed_ids = {canonical_id, *normalized_aliases}
        for claimed_id in claimed_ids:
            if (
                claimed_id in self._entries
                or claimed_id in self._aliases
            ):
                raise DuplicateApplicationError(
                    f"Identidade ou alias já registrado: {claimed_id}."
                )

        entry = _CatalogEntry(
            canonical_id=canonical_id,
            descriptor=descriptor,
            registered_object=registered_object,
            application=application,
            module=module,
            aliases=normalized_aliases,
        )
        self._entries[canonical_id] = entry
        for alias in normalized_aliases:
            self._aliases[alias] = canonical_id

    def _get_entry(self, application_id: str) -> _CatalogEntry | None:
        normalized = (
            application_id.strip()
            if isinstance(application_id, str)
            else ""
        )
        canonical_id = self._aliases.get(normalized, normalized)
        return self._entries.get(canonical_id)

    def _resolve_entry(
        self,
        project: Project,
    ) -> tuple[_CatalogEntry | None, str]:
        if not isinstance(project, Project):
            raise TypeError("project deve ser uma instância de Project.")
        application_id = (
            project.application.strip()
            if isinstance(project.application, str)
            else ""
        )
        if not application_id:
            return None, application_id

        entry = self._get_entry(application_id)
        if entry is None:
            if application_id in self.LEGACY_APPLICATION_IDS:
                return None, application_id
            raise ApplicationNotRegisteredError(
                f"Application não registrada: {application_id}."
            )
        return entry, application_id

    def _validate_descriptor(
        self,
        descriptor: ApplicationDescriptor,
    ) -> None:
        if descriptor.minimum_platform_version > self._platform_version:
            raise IncompatibleApplicationError(
                "Application requer plataforma "
                f"{descriptor.minimum_platform_version} ou superior; "
                f"versão disponível: {self._platform_version}."
            )
        for schema_version in descriptor.supported_project_schema_versions:
            if (
                isinstance(schema_version, bool)
                or not isinstance(schema_version, int)
                or schema_version < 1
            ):
                raise ValueError(
                    "Descriptor contém versão de schema inválida."
                )
        if not isinstance(descriptor.required_capabilities, frozenset):
            raise TypeError(
                "required_capabilities deve ser imutável."
            )
        if not isinstance(descriptor.provided_capabilities, frozenset):
            raise TypeError(
                "provided_capabilities deve ser imutável."
            )

    @staticmethod
    def _validate_project_schema(
        entry: _CatalogEntry,
        project: Project,
    ) -> None:
        supported = entry.descriptor.supported_project_schema_versions
        if supported and project.format_version not in supported:
            raise IncompatibleApplicationError(
                "Application incompatível com a versão do projeto: "
                f"{project.format_version}."
            )

    def _ordered_entries(self) -> tuple[_CatalogEntry, ...]:
        return tuple(
            self._entries[application_id]
            for application_id in sorted(self._entries)
        )

    @staticmethod
    def _required_id(value: object) -> str:
        if not isinstance(value, str) or not value.strip():
            raise ValueError(
                "application_id deve ser um texto não vazio."
            )
        return value.strip()

    @staticmethod
    def _required_display_name(value: object) -> str:
        if not isinstance(value, str) or not value.strip():
            raise ValueError(
                "display_name deve ser um texto não vazio."
            )
        return value.strip()
