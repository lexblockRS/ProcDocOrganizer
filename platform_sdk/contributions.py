"""Contratos declarativos de apresentação, independentes de toolkit gráfico."""

from collections.abc import Callable
from dataclasses import dataclass


def _required_text(value: object, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} deve ser um texto não vazio.")
    return value.strip()


@dataclass(frozen=True, slots=True)
class MenuContribution:
    menu_id: str
    title: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "menu_id", _required_text(self.menu_id, "menu_id")
        )
        object.__setattr__(
            self, "title", _required_text(self.title, "title")
        )


@dataclass(frozen=True, slots=True)
class ActionContribution:
    attribute_name: str
    text: str
    menu_id: str
    visible: bool = True
    enabled: bool = True
    tooltip: str | None = None
    object_name: str | None = None
    disable_on_project_close: bool = False
    callback: Callable[[], object] | None = None
    navigation_target: str | None = None
    controller: object | None = None
    command_id: str | None = None

    def __post_init__(self) -> None:
        for name in ("attribute_name", "text", "menu_id"):
            object.__setattr__(
                self, name, _required_text(getattr(self, name), name)
            )
        for name in ("visible", "enabled", "disable_on_project_close"):
            if not isinstance(getattr(self, name), bool):
                raise TypeError(f"{name} deve ser bool.")
        for name in ("tooltip", "object_name"):
            value = getattr(self, name)
            if value is not None:
                object.__setattr__(
                    self, name, _required_text(value, name)
                )
        if self.callback is not None and not callable(self.callback):
            raise TypeError("callback deve ser chamável ou None.")
        if self.navigation_target is not None:
            object.__setattr__(
                self,
                "navigation_target",
                _required_text(
                    self.navigation_target,
                    "navigation_target",
                ),
            )
        if self.controller is not None:
            execute = getattr(self.controller, "execute", None)
            if not callable(execute):
                raise TypeError(
                    "controller deve implementar execute()."
                )
            object.__setattr__(
                self,
                "command_id",
                _required_text(self.command_id, "command_id"),
            )
        elif self.command_id is not None:
            raise ValueError("command_id exige controller.")


@dataclass(frozen=True, slots=True)
class ViewContribution:
    view_id: str
    attribute_name: str
    factory: Callable[[], object]
    show_method_name: str
    open_project_action: str | None = None

    def __post_init__(self) -> None:
        for name in ("view_id", "attribute_name", "show_method_name"):
            object.__setattr__(
                self, name, _required_text(getattr(self, name), name)
            )
        if not callable(self.factory):
            raise TypeError("factory deve ser chamável.")
        if self.open_project_action is not None:
            object.__setattr__(
                self,
                "open_project_action",
                _required_text(
                    self.open_project_action,
                    "open_project_action",
                ),
            )


@dataclass(frozen=True, slots=True)
class ToolbarContribution:
    toolbar_id: str
    action_attribute: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "toolbar_id",
            _required_text(self.toolbar_id, "toolbar_id"),
        )
        object.__setattr__(
            self,
            "action_attribute",
            _required_text(self.action_attribute, "action_attribute"),
        )
