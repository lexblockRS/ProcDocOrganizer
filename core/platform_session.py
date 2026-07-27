"""Agregado neutro da futura sessão da plataforma."""

from dataclasses import dataclass

from .application_runtime import ApplicationRuntime
from .project_context import ProjectContext
from .session_context import SessionContext


@dataclass(frozen=True, slots=True)
class PlatformSession:
    """Compõe contexto permanente, recursos e runtime da Application."""

    project_context: ProjectContext
    session_context: SessionContext
    application_runtime: ApplicationRuntime

    def __post_init__(self) -> None:
        if not isinstance(self.project_context, ProjectContext):
            raise TypeError(
                "project_context deve ser um ProjectContext."
            )
        if not isinstance(self.session_context, SessionContext):
            raise TypeError(
                "session_context deve ser um SessionContext."
            )
        if not isinstance(
            self.application_runtime,
            ApplicationRuntime,
        ):
            raise TypeError(
                "application_runtime deve ser um ApplicationRuntime."
            )
