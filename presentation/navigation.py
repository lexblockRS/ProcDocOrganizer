"""Serviço lógico de navegação da camada de apresentação."""

from contextlib import nullcontext
from collections.abc import Mapping
from dataclasses import dataclass

from .navigation_contracts import NavigationIntent, NavigationIntentType
from .perspectives import PerspectiveId, PerspectiveStore
from .presentation_context import PresentationContextStore
from .selection import (
    SelectionContext,
    SelectionIdentity,
    SelectionKind,
    SelectionStore,
)
from .workspace import WorkspaceSnapshot, WorkspaceStore

__all__ = ["NavigationController", "NavigationHistoryEntry"]


@dataclass(frozen=True, slots=True)
class NavigationHistoryEntry:
    intent: NavigationIntent
    snapshot: WorkspaceSnapshot

    def __post_init__(self) -> None:
        if not isinstance(self.intent, NavigationIntent):
            raise TypeError("intent deve ser NavigationIntent.")
        if not isinstance(self.snapshot, WorkspaceSnapshot):
            raise TypeError("snapshot deve ser WorkspaceSnapshot.")


class NavigationController:
    """Navigation Service oficial; coordena sem possuir Workspace state."""

    __slots__ = (
        "_perspective_store",
        "_workspace_store",
        "_selection_store",
        "_presentation_context",
        "_clear_selection_on_navigation",
        "_history",
        "_history_cursor",
        "_routes",
    )

    def __init__(
        self,
        perspective_store: PerspectiveStore,
        workspace_store: WorkspaceStore,
        selection_store: SelectionStore,
        *,
        presentation_context: PresentationContextStore | None = None,
        clear_selection_on_navigation: bool = True,
        routes: Mapping[NavigationIntentType, PerspectiveId] | None = None,
    ) -> None:
        if not isinstance(perspective_store, PerspectiveStore):
            raise TypeError("perspective_store deve ser PerspectiveStore.")
        if not isinstance(workspace_store, WorkspaceStore):
            raise TypeError("workspace_store deve ser WorkspaceStore.")
        if not isinstance(selection_store, SelectionStore):
            raise TypeError("selection_store deve ser SelectionStore.")
        if presentation_context is not None and not isinstance(
            presentation_context, PresentationContextStore
        ):
            raise TypeError(
                "presentation_context deve ser PresentationContextStore ou None."
            )
        if not isinstance(clear_selection_on_navigation, bool):
            raise TypeError(
                "clear_selection_on_navigation deve ser booleano."
            )
        self._perspective_store = perspective_store
        self._workspace_store = workspace_store
        self._selection_store = selection_store
        self._presentation_context = presentation_context
        self._clear_selection_on_navigation = clear_selection_on_navigation
        self._history: list[NavigationHistoryEntry] = []
        self._history_cursor: int | None = None
        self._routes: dict[NavigationIntentType, PerspectiveId] = {}
        if routes is not None:
            for intent_type, perspective_id in routes.items():
                self.register_route(intent_type, perspective_id)

    @property
    def history(self) -> tuple[NavigationHistoryEntry, ...]:
        return tuple(self._history)

    @property
    def history_position(self) -> int | None:
        """Posição segura da entrada restaurada atualmente."""
        return self._history_cursor

    @property
    def current_history_entry(self) -> NavigationHistoryEntry | None:
        if self._history_cursor is None:
            return None
        return self._history[self._history_cursor]

    @property
    def can_go_back(self) -> bool:
        return self._history_cursor is not None and self._history_cursor > 0

    @property
    def can_go_forward(self) -> bool:
        return (
            self._history_cursor is not None
            and self._history_cursor < len(self._history) - 1
        )

    def navigate(self, intent: NavigationIntent) -> WorkspaceSnapshot:
        """Valida e aplica uma intenção como uma transição coordenada."""
        if not isinstance(intent, NavigationIntent):
            raise TypeError("intent deve ser NavigationIntent.")
        transaction = (
            nullcontext()
            if self._presentation_context is None
            else self._presentation_context.batch()
        )
        with transaction:
            if intent.intent_type is NavigationIntentType.OPEN_PERSPECTIVE:
                self._navigate_perspective(PerspectiveId(intent.target_id))
                selection = self._selection_store.snapshot.selection
            else:
                route = self._routes.get(intent.intent_type)
                if route is not None:
                    self._navigate_perspective(route)
                if intent.intent_type is NavigationIntentType.OPEN_DASHBOARD:
                    selection = self._selection_store.snapshot.selection
                else:
                    selection = self._selection_for(intent)
                    self._selection_store.select(selection)
            snapshot = self._workspace_store.apply(
                intent, selection=selection
            )
            if self._history_cursor is not None:
                del self._history[self._history_cursor + 1 :]
            entry = NavigationHistoryEntry(intent, snapshot)
            if not self._history or self._history[-1] != entry:
                self._history.append(entry)
            self._history_cursor = len(self._history) - 1
        return snapshot

    def go_back(self) -> WorkspaceSnapshot | bool:
        """Restaura a entrada anterior sem executar novamente sua Intent."""
        if not self.can_go_back:
            return False
        self._history_cursor -= 1
        return self._restore_current_entry()

    def go_forward(self) -> WorkspaceSnapshot | bool:
        """Restaura a entrada posterior sem executar novamente sua Intent."""
        if not self.can_go_forward:
            return False
        self._history_cursor += 1
        return self._restore_current_entry()

    def restore_current(self) -> WorkspaceSnapshot | bool:
        """Restaura novamente a entrada apontada pelo cursor."""
        if self._history_cursor is None:
            return False
        return self._restore_current_entry()

    def clear_history(self) -> None:
        """Descarta o histórico ao encerrar ou trocar de Project."""
        self._history.clear()
        self._history_cursor = None

    def register_route(
        self,
        intent_type: NavigationIntentType,
        perspective_id: PerspectiveId,
    ) -> None:
        """Associa uma Intent tipada a uma perspectiva já registrada."""
        if not isinstance(intent_type, NavigationIntentType):
            raise TypeError("intent_type deve ser NavigationIntentType.")
        if intent_type is NavigationIntentType.OPEN_PERSPECTIVE:
            raise ValueError("OPEN_PERSPECTIVE já informa seu destino.")
        if not isinstance(perspective_id, PerspectiveId):
            raise TypeError("perspective_id deve ser PerspectiveId.")
        if not self._perspective_store.contains(perspective_id):
            raise ValueError(
                "Rota exige perspectiva registrada: "
                f"{perspective_id.value}."
            )
        self._routes[intent_type] = perspective_id

    def _restore_current_entry(self) -> WorkspaceSnapshot:
        entry = self._history[self._history_cursor]
        transaction = (
            nullcontext()
            if self._presentation_context is None
            else self._presentation_context.batch()
        )
        with transaction:
            snapshot = entry.snapshot
            self._perspective_store.restore(snapshot.active_perspective)
            self._selection_store.restore(snapshot.selection)
            restored = self._workspace_store.restore(snapshot)
        return restored

    def navigate_to(self, perspective_id: PerspectiveId) -> None:
        """Adaptador compatível para a navegação por perspectiva existente."""
        if not isinstance(perspective_id, PerspectiveId):
            raise TypeError("perspective_id deve ser PerspectiveId.")
        intent = NavigationIntent(
            NavigationIntentType.OPEN_PERSPECTIVE,
            target_id=perspective_id.value,
        )
        self.navigate(intent)

    def _navigate_perspective(self, perspective_id: PerspectiveId) -> None:
        self._perspective_store.activate(perspective_id)
        self._workspace_store.mount(perspective_id)
        if self._clear_selection_on_navigation:
            self._selection_store.clear()

    @staticmethod
    def _selection_for(intent: NavigationIntent) -> SelectionContext:
        kind_by_intent = {
            NavigationIntentType.OPEN_DOCUMENT: SelectionKind.DOCUMENT,
            NavigationIntentType.OPEN_EVIDENCE: SelectionKind.EVIDENCE,
            NavigationIntentType.OPEN_EXECUTION_FACT: SelectionKind.EXECUTION_FACT,
            NavigationIntentType.OPEN_REQUIREMENT: SelectionKind.REQUIREMENT,
            NavigationIntentType.OPEN_CRITERION: SelectionKind.CRITERION,
            NavigationIntentType.OPEN_EVALUATION: SelectionKind.EVALUATION,
            NavigationIntentType.OPEN_REPORT: SelectionKind.REPORT,
        }
        kind = kind_by_intent[intent.intent_type]
        return SelectionContext(
            SelectionIdentity(kind, intent.target_id),
            metadata=intent.metadata,
        )
