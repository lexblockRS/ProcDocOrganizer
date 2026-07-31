"""Visão consolidada e observável do estado global da apresentação."""

from collections.abc import Callable
from contextlib import contextmanager
from dataclasses import dataclass, field, replace
import logging

from .application_state import (
    ApplicationStateSnapshot,
    ApplicationStateStore,
)
from .perspectives import PerspectiveSnapshot, PerspectiveStore
from .selection import SelectionSnapshot, SelectionStore
from .workspace import WorkspaceSnapshot, WorkspaceStore

logger = logging.getLogger(__name__)

__all__ = [
    "PresentationContextStore",
    "PresentationSnapshot",
]


@dataclass(frozen=True, slots=True)
class PresentationSnapshot:
    application_state: ApplicationStateSnapshot
    selection: SelectionSnapshot
    perspective: PerspectiveSnapshot
    revision: int = 0
    workspace: WorkspaceSnapshot = field(default_factory=WorkspaceSnapshot)

    def __post_init__(self) -> None:
        if not isinstance(
            self.application_state, ApplicationStateSnapshot
        ):
            raise TypeError(
                "application_state deve ser ApplicationStateSnapshot."
            )
        if not isinstance(self.selection, SelectionSnapshot):
            raise TypeError("selection deve ser SelectionSnapshot.")
        if not isinstance(self.perspective, PerspectiveSnapshot):
            raise TypeError(
                "perspective deve ser PerspectiveSnapshot."
            )
        if isinstance(self.revision, bool) or not isinstance(
            self.revision, int
        ):
            raise TypeError("revision deve ser inteiro.")
        if self.revision < 0:
            raise ValueError("revision não pode ser negativa.")
        if not isinstance(self.workspace, WorkspaceSnapshot):
            raise TypeError("workspace deve ser WorkspaceSnapshot.")


PresentationObserver = Callable[[PresentationSnapshot], None]


class PresentationContextStore:
    """Proprietário da projeção derivada, nunca dos estados de origem."""

    def __init__(
        self,
        application_state_store: ApplicationStateStore,
        selection_store: SelectionStore,
        perspective_store: PerspectiveStore,
        workspace_store: WorkspaceStore | None = None,
    ) -> None:
        if not isinstance(application_state_store, ApplicationStateStore):
            raise TypeError(
                "application_state_store deve ser ApplicationStateStore."
            )
        if not isinstance(selection_store, SelectionStore):
            raise TypeError(
                "selection_store deve ser SelectionStore."
            )
        if not isinstance(perspective_store, PerspectiveStore):
            raise TypeError(
                "perspective_store deve ser PerspectiveStore."
            )
        if workspace_store is not None and not isinstance(
            workspace_store, WorkspaceStore
        ):
            raise TypeError("workspace_store deve ser WorkspaceStore ou None.")

        self._snapshot = PresentationSnapshot(
            application_state=application_state_store.snapshot,
            selection=selection_store.snapshot,
            perspective=perspective_store.snapshot,
            workspace=(
                WorkspaceSnapshot()
                if workspace_store is None
                else workspace_store.snapshot
            ),
        )
        self._observers: list[PresentationObserver] = []
        self._batch_depth = 0
        self._pending_changes: dict[str, object] = {}

        application_state_store.subscribe(
            self._on_application_state_changed
        )
        selection_store.subscribe(self._on_selection_changed)
        perspective_store.subscribe(self._on_perspective_changed)
        if workspace_store is not None:
            workspace_store.subscribe(self._on_workspace_changed)

    @property
    def snapshot(self) -> PresentationSnapshot:
        return self._snapshot

    def subscribe(
        self, observer: PresentationObserver
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

    def _on_application_state_changed(
        self, snapshot: ApplicationStateSnapshot
    ) -> None:
        self._update(application_state=snapshot)

    def _on_selection_changed(self, snapshot: SelectionSnapshot) -> None:
        self._update(selection=snapshot)

    def _on_perspective_changed(
        self, snapshot: PerspectiveSnapshot
    ) -> None:
        self._update(perspective=snapshot)

    def _on_workspace_changed(self, snapshot: WorkspaceSnapshot) -> None:
        self._update(workspace=snapshot)

    @contextmanager
    def batch(self):
        """Publica uma transição coordenada como uma única revisão."""
        self._batch_depth += 1
        try:
            yield
        finally:
            self._batch_depth -= 1
            if self._batch_depth == 0 and self._pending_changes:
                changes = self._pending_changes
                self._pending_changes = {}
                self._commit_changes(changes)

    def _update(self, **changes: object) -> None:
        if self._batch_depth:
            self._pending_changes.update(changes)
            return
        self._commit_changes(changes)

    def _commit_changes(self, changes: dict[str, object]) -> None:
        if all(
            getattr(self._snapshot, field) == value
            for field, value in changes.items()
        ):
            return
        candidate = replace(
            self._snapshot,
            **changes,
            revision=self._snapshot.revision + 1,
        )
        self._snapshot = candidate
        logger.info(
            "Contexto consolidado da UI alterado; revisão %d.",
            candidate.revision,
        )
        for observer in tuple(self._observers):
            try:
                observer(candidate)
            except Exception:
                logger.exception(
                    "Observer do contexto da apresentação falhou."
                )
