"""Coordenação puramente lógica da navegação da apresentação."""

from .perspectives import PerspectiveId, PerspectiveStore
from .selection import SelectionStore
from .workspace import WorkspaceStore

__all__ = ["NavigationController"]


class NavigationController:
    """Coordena stores sem possuir ou duplicar estado de navegação."""

    __slots__ = (
        "_perspective_store",
        "_workspace_store",
        "_selection_store",
        "_clear_selection_on_navigation",
    )

    def __init__(
        self,
        perspective_store: PerspectiveStore,
        workspace_store: WorkspaceStore,
        selection_store: SelectionStore,
        *,
        clear_selection_on_navigation: bool = True,
    ) -> None:
        if not isinstance(perspective_store, PerspectiveStore):
            raise TypeError(
                "perspective_store deve ser PerspectiveStore."
            )
        if not isinstance(workspace_store, WorkspaceStore):
            raise TypeError("workspace_store deve ser WorkspaceStore.")
        if not isinstance(selection_store, SelectionStore):
            raise TypeError("selection_store deve ser SelectionStore.")
        if not isinstance(clear_selection_on_navigation, bool):
            raise TypeError(
                "clear_selection_on_navigation deve ser booleano."
            )
        self._perspective_store = perspective_store
        self._workspace_store = workspace_store
        self._selection_store = selection_store
        self._clear_selection_on_navigation = (
            clear_selection_on_navigation
        )

    def navigate_to(self, perspective_id: PerspectiveId) -> None:
        if not isinstance(perspective_id, PerspectiveId):
            raise TypeError("perspective_id deve ser PerspectiveId.")

        self._perspective_store.activate(perspective_id)
        self._workspace_store.mount(perspective_id)
        if self._clear_selection_on_navigation:
            self._selection_store.clear()
