"""Registro explícito e resolução de Applications do host."""

from collections.abc import Iterable

from contracts import Application
from models import Project


class ApplicationRegistryError(RuntimeError):
    """Erro neutro de registro ou resolução de Application."""


class DuplicateApplicationError(ApplicationRegistryError):
    """Indica que duas Applications declararam a mesma identidade."""


class ApplicationNotRegisteredError(ApplicationRegistryError):
    """Indica que o projeto referencia uma Application desconhecida."""


class IncompatibleApplicationError(ApplicationRegistryError):
    """Indica que a Application registrada recusou o projeto."""


class ApplicationRegistry:
    """Mantém e resolve um conjunto explícito de Applications."""

    LEGACY_APPLICATION_IDS = frozenset({"ProcDocOrganizer"})

    def __init__(
        self, applications: Iterable[Application] = ()
    ) -> None:
        self._applications: dict[str, Application] = {}
        for application in applications:
            self.register(application)

    @property
    def applications(self) -> tuple[Application, ...]:
        return tuple(self._applications.values())

    def register(self, application: Application) -> None:
        application_id = self._required_id(
            getattr(application, "application_id", None)
        )
        if application_id in self._applications:
            raise DuplicateApplicationError(
                f"Application já registrada: {application_id}."
            )
        if not callable(getattr(application, "can_open", None)):
            raise TypeError("Application deve implementar can_open(project).")
        if not callable(getattr(application, "contributions", None)):
            raise TypeError("Application deve implementar contributions().")
        self._applications[application_id] = application

    def get(self, application_id: str) -> Application | None:
        normalized = (
            application_id.strip()
            if isinstance(application_id, str)
            else ""
        )
        return self._applications.get(normalized)

    def resolve(self, project: Project) -> Application | None:
        if not isinstance(project, Project):
            raise TypeError("project deve ser uma instância de Project.")
        application_id = (
            project.application.strip()
            if isinstance(project.application, str)
            else ""
        )
        if not application_id:
            return None

        application = self.get(application_id)
        if application is None:
            if application_id in self.LEGACY_APPLICATION_IDS:
                return None
            raise ApplicationNotRegisteredError(
                f"Application não registrada: {application_id}."
            )
        if not application.can_open(project):
            raise IncompatibleApplicationError(
                f"Application incompatível com o projeto: {application_id}."
            )
        return application

    @staticmethod
    def _required_id(value: object) -> str:
        if not isinstance(value, str) or not value.strip():
            raise ValueError(
                "application_id deve ser um texto não vazio."
            )
        return value.strip()
