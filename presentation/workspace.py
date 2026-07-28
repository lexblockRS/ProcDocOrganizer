"""Contrato lógico do espaço central da camada de apresentação."""

from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum
import logging

from .perspectives import PerspectiveId, PerspectiveStore

logger = logging.getLogger(__name__)

__all__ = [
    "InvalidWorkspacePerspective",
    "WorkspaceContractError",
    "WorkspaceSnapshot",
    "WorkspaceState",
    "WorkspaceStore",
]


class WorkspaceState(str, Enum):
    EMPTY = "empty"
    READY = "ready"


class WorkspaceContractError(ValueError):
    """Valor incompatível com o contrato lógico do Workspace."""


class InvalidWorkspacePerspective(WorkspaceContractError):
    """A perspectiva não pode ser montada no Workspace."""


@dataclass(frozen=True, slots=True)
class WorkspaceSnapshot:
    state: WorkspaceState = WorkspaceState.EMPTY
    active_perspective: PerspectiveId | None = None
    revision: int = 0

    def __post_init__(self) -> None:
        if not isinstance(self.state, WorkspaceState):
            raise WorkspaceContractError(
                "state deve ser WorkspaceState."
            )
        if self.active_perspective is not None and not isinstance(
            self.active_perspective, PerspectiveId
        ):
            raise WorkspaceContractError(
                "active_perspective deve ser PerspectiveId ou None."
            )
        if self.state is WorkspaceState.EMPTY:
            if self.active_perspective is not None:
                raise WorkspaceContractError(
                    "Workspace EMPTY não pode possuir perspectiva."
                )
        elif self.active_perspective is None:
            raise WorkspaceContractError(
                "Workspace READY exige perspectiva ativa."
            )
        if isinstance(self.revision, bool) or not isinstance(
            self.revision, int
        ):
            raise WorkspaceContractError("revision deve ser inteiro.")
        if self.revision < 0:
            raise WorkspaceContractError(
                "revision não pode ser negativa."
            )


WorkspaceObserver = Callable[[WorkspaceSnapshot], None]


class WorkspaceStore:
    """Proprietário da perspectiva logicamente montada no Workspace."""

    def __init__(self, perspective_store: PerspectiveStore) -> None:
        if not isinstance(perspective_store, PerspectiveStore):
            raise TypeError(
                "perspective_store deve ser PerspectiveStore."
            )
        self._perspective_store = perspective_store
        self._snapshot = WorkspaceSnapshot()
        self._observers: list[WorkspaceObserver] = []

    @property
    def snapshot(self) -> WorkspaceSnapshot:
        return self._snapshot

    def mount(self, perspective: PerspectiveId) -> WorkspaceSnapshot:
        if not isinstance(perspective, PerspectiveId):
            logger.warning("Montagem lógica recusada: ID inválido.")
            raise InvalidWorkspacePerspective(
                "perspective deve ser PerspectiveId."
            )
        if not self._perspective_store.contains(perspective):
            logger.warning(
                "Montagem lógica recusada: perspectiva não registrada."
            )
            raise InvalidWorkspacePerspective(
                f"Perspectiva não registrada: {perspective.value}."
            )
        if self._snapshot.active_perspective == perspective:
            return self._snapshot
        return self._commit(
            WorkspaceSnapshot(
                state=WorkspaceState.READY,
                active_perspective=perspective,
                revision=self._snapshot.revision + 1,
            )
        )

    def clear(self) -> WorkspaceSnapshot:
        if self._snapshot.state is WorkspaceState.EMPTY:
            return self._snapshot
        return self._commit(
            WorkspaceSnapshot(revision=self._snapshot.revision + 1)
        )

    def subscribe(
        self, observer: WorkspaceObserver
    ) -> Callable[[], None]:
        if not callable(observer):
            raise TypeError("observer deve ser chamável.")
        if observer not in self._observers:
            self._observers.append(observer)

        def unsubscribe() -> None:
            try:
                self._observers.remove(observer)
            except ValueError:
                pass

        return unsubscribe

    def _commit(self, candidate: WorkspaceSnapshot) -> WorkspaceSnapshot:
        self._snapshot = candidate
        logger.info(
            "Workspace lógico alterado: %s; revisão %d.",
            candidate.state.value,
            candidate.revision,
        )
        for observer in tuple(self._observers):
            try:
                observer(candidate)
            except Exception:
                logger.exception("Observer do Workspace lógico falhou.")
        return candidate
