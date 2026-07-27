"""Materialização interna dos contratos públicos de apresentação."""

from PySide6.QtGui import QAction

from contracts import ContributionCategory
from platform_sdk import (
    ActionContribution,
    MenuContribution,
    ToolbarContribution,
    ViewContribution,
)

from .main_window import MainWindow
from .platform_sdk_materializer import materialize_application_view


class PlatformMainWindow(MainWindow):
    """MainWindow produtiva capaz de materializar o Platform SDK."""

    def _install_contributions(self) -> None:
        for registration in self.contribution_manager.by_category(
            ContributionCategory.MENU
        ):
            contribution = registration.contribution
            if isinstance(contribution, MenuContribution):
                self.create_application_menu(
                    contribution.menu_id,
                    contribution.title,
                )

        self._installed_window_actions = []
        for registration in self.contribution_manager.by_category(
            ContributionCategory.ACTION
        ):
            contribution = registration.contribution
            if not isinstance(contribution, ActionContribution):
                continue
            if hasattr(self, contribution.attribute_name):
                raise ValueError(
                    "Atributo de action duplicado: "
                    f"{contribution.attribute_name}."
                )
            action = QAction(contribution.text, self)
            action.setVisible(contribution.visible)
            action.setEnabled(contribution.enabled)
            if contribution.tooltip is not None:
                action.setToolTip(contribution.tooltip)
            if contribution.object_name is not None:
                action.setObjectName(contribution.object_name)
            self.get_menu(contribution.menu_id).addAction(action)
            if contribution.callback is not None:
                action.triggered.connect(
                    lambda _checked=False, callback=contribution.callback:
                    callback()
                )
            if contribution.navigation_target is not None:
                action.triggered.connect(
                    lambda _checked=False,
                    view_id=contribution.navigation_target:
                    self.show_view(view_id)
                )
            if contribution.controller is not None:
                action.triggered.connect(
                    lambda _checked=False,
                    controller=contribution.controller,
                    command_id=contribution.command_id:
                    controller.execute(command_id)
                )
            setattr(self, contribution.attribute_name, action)
            self._installed_window_actions.append(
                (action, contribution)
            )

        for registration in self.contribution_manager.by_category(
            ContributionCategory.VIEW
        ):
            contribution = registration.contribution
            if not isinstance(contribution, ViewContribution):
                continue
            if contribution.view_id in self.views:
                raise ValueError(
                    f"View duplicada: {contribution.view_id}."
                )
            view = materialize_application_view(
                contribution.factory()
            )
            self.view_manager.register(contribution.view_id, view)
            setattr(self, contribution.attribute_name, view)
            setattr(
                self,
                contribution.show_method_name,
                lambda view_id=contribution.view_id: self.show_view(view_id),
            )
            if contribution.open_project_action is not None:
                view.open_project_requested.connect(
                    getattr(
                        self,
                        contribution.open_project_action,
                    ).trigger
                )

        for registration in self.contribution_manager.by_category(
            ContributionCategory.TOOLBAR
        ):
            contribution = registration.contribution
            if not isinstance(contribution, ToolbarContribution):
                continue
            toolbar = self._toolbars_by_id.get(contribution.toolbar_id)
            if toolbar is None:
                raise KeyError(
                    f"Toolbar não registrada: {contribution.toolbar_id}."
                )
            toolbar.addAction(
                getattr(self, contribution.action_attribute)
            )
