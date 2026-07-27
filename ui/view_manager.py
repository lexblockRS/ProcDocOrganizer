"""Registro, navegação e lifecycle das views centrais."""

from types import MappingProxyType

from PySide6.QtWidgets import QStackedWidget, QWidget


class ViewManager:
    """Gerencia views persistentes sem conhecer seus detalhes internos."""

    def __init__(self, stack: QStackedWidget) -> None:
        if not isinstance(stack, QStackedWidget):
            raise TypeError("stack deve ser QStackedWidget.")
        self._stack = stack
        self._views: dict[str, QWidget] = {}

    @property
    def views(self):
        return MappingProxyType(self._views)

    def register(self, view_id: str, view: QWidget) -> QWidget:
        self._validate_id(view_id)
        if not isinstance(view, QWidget):
            raise TypeError("view deve ser QWidget.")
        if view_id in self._views:
            raise ValueError(f"View já registrada: {view_id}.")
        if view in self._views.values():
            raise ValueError("A mesma instância de View já foi registrada.")
        self._views[view_id] = view
        self._stack.addWidget(view)
        return view

    def get(self, view_id: str) -> QWidget | None:
        self._validate_id(view_id)
        return self._views.get(view_id)

    def show(self, view_id: str) -> bool:
        view = self.get(view_id)
        if view is None:
            return False
        self._stack.setCurrentWidget(view)
        return True

    def active_view(self) -> QWidget | None:
        current = self._stack.currentWidget()
        return current if current in self._views.values() else None

    def active_view_id(self) -> str | None:
        current = self.active_view()
        return next(
            (
                view_id
                for view_id, view in self._views.items()
                if view is current
            ),
            None,
        )

    def notify_project_opened(self, project) -> None:
        self._notify("on_project_open", "on_project_opened", project)

    def notify_project_changed(self, project) -> None:
        self._notify(
            "on_project_changed", "on_project_opened", project
        )

    def notify_project_closed(self, *, exclude=()) -> None:
        excluded = set(exclude)
        self._notify(
            "on_project_close",
            "on_project_closed",
            excluded=excluded,
        )

    def _notify(
        self,
        preferred_name,
        legacy_name,
        *args,
        excluded=frozenset(),
    ) -> None:
        for view in self._views.values():
            if view in excluded:
                continue
            callback = getattr(view, preferred_name, None)
            if callable(callback):
                callback(*args)
                continue
            callback = getattr(view, legacy_name, None)
            if callable(callback):
                callback(*args)

    @staticmethod
    def _validate_id(view_id: str) -> None:
        if not isinstance(view_id, str):
            raise TypeError("view_id deve ser uma string.")
        if not view_id.strip():
            raise ValueError("view_id não pode ser vazio.")
