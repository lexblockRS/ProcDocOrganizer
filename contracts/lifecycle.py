"""Estados e transições do lifecycle de uma Application."""

from dataclasses import dataclass
from enum import Enum


class ApplicationLifecycleState(str, Enum):
    DISCOVERED = "discovered"
    REGISTERED = "registered"
    PROJECT_PREPARED = "project_prepared"
    SESSION_CREATED = "session_created"
    PRESENTATION_MOUNTED = "presentation_mounted"
    ACTIVE = "active"
    DEACTIVATING = "deactivating"
    DISPOSED = "disposed"


VALID_APPLICATION_LIFECYCLE_TRANSITIONS = frozenset({
    (
        ApplicationLifecycleState.DISCOVERED,
        ApplicationLifecycleState.REGISTERED,
    ),
    (
        ApplicationLifecycleState.REGISTERED,
        ApplicationLifecycleState.PROJECT_PREPARED,
    ),
    (
        ApplicationLifecycleState.PROJECT_PREPARED,
        ApplicationLifecycleState.SESSION_CREATED,
    ),
    (
        ApplicationLifecycleState.SESSION_CREATED,
        ApplicationLifecycleState.PRESENTATION_MOUNTED,
    ),
    (
        ApplicationLifecycleState.PRESENTATION_MOUNTED,
        ApplicationLifecycleState.ACTIVE,
    ),
    (
        ApplicationLifecycleState.ACTIVE,
        ApplicationLifecycleState.DEACTIVATING,
    ),
    (
        ApplicationLifecycleState.DEACTIVATING,
        ApplicationLifecycleState.DISPOSED,
    ),
    (
        ApplicationLifecycleState.REGISTERED,
        ApplicationLifecycleState.DISPOSED,
    ),
    (
        ApplicationLifecycleState.PROJECT_PREPARED,
        ApplicationLifecycleState.DISPOSED,
    ),
    (
        ApplicationLifecycleState.SESSION_CREATED,
        ApplicationLifecycleState.DISPOSED,
    ),
    (
        ApplicationLifecycleState.PRESENTATION_MOUNTED,
        ApplicationLifecycleState.DISPOSED,
    ),
})


@dataclass(frozen=True, slots=True)
class ApplicationLifecycleTransition:
    """Representa uma transição válida, sem executá-la."""

    source: ApplicationLifecycleState
    target: ApplicationLifecycleState

    def __post_init__(self) -> None:
        if not isinstance(self.source, ApplicationLifecycleState):
            raise TypeError(
                "source deve ser um ApplicationLifecycleState."
            )
        if not isinstance(self.target, ApplicationLifecycleState):
            raise TypeError(
                "target deve ser um ApplicationLifecycleState."
            )
        if (
            self.source,
            self.target,
        ) not in VALID_APPLICATION_LIFECYCLE_TRANSITIONS:
            raise ValueError(
                f"Transição de lifecycle inválida: "
                f"{self.source.value} -> {self.target.value}."
            )
