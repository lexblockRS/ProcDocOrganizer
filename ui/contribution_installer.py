"""Materialização desktop de contribuições de ação."""

from collections.abc import Callable, Iterable
from dataclasses import dataclass
from typing import Protocol

from PySide6.QtGui import QAction
from PySide6.QtWidgets import QMenu

from contracts import ActionContribution

__all__ = [
    "ContributionInstallationError",
    "DesktopContributionInstaller",
]


class ContributionInstallationError(RuntimeError):
    """Indica falha ao instalar ou desmontar contribuições no Qt."""


class _MenuHost(Protocol):
    def get_menu(self, menu_id: str) -> QMenu:
        """Retorna um menu registrado pelo identificador estável."""


@dataclass(slots=True)
class _InstalledAction:
    contribution: ActionContribution
    action: QAction
    menu: QMenu
    connected_callback: Callable[[], None]


class DesktopContributionInstaller:
    """Instala contribuições declarativas como ações concretas do Qt."""

    def __init__(self, main_window: _MenuHost) -> None:
        self._main_window = main_window
        self._installed: list[_InstalledAction] = []

    def active(self) -> tuple[ActionContribution, ...]:
        """Retorna as contribuições que possuem instalação concreta ativa."""

        return tuple(
            installed.contribution for installed in self._installed
        )

    def install(
        self,
        contributions: Iterable[ActionContribution],
    ) -> None:
        """Instala atomicamente um conjunto quando não há ações ativas."""

        if self._installed:
            raise ContributionInstallationError(
                "Já existem contribuições desktop instaladas."
            )

        prepared = self._prepare(contributions)
        self._installed = self._install_prepared(prepared)

    def clear(self) -> None:
        """Desmonta todas as ações, tentando limpar cada handle."""

        installed = self._installed
        self._installed = []
        errors = self._cleanup_handles(installed)
        if errors:
            self._raise_cleanup_error(errors)

    def replace(
        self,
        contributions: Iterable[ActionContribution],
    ) -> None:
        """Substitui as ações e restaura as anteriores se a instalação falhar.

        A validação prévia reduz o risco de falha depois da alteração visual,
        mas o Qt não oferece uma transação nativa para tornar essa troca
        visualmente atômica.
        """

        prepared = self._prepare(contributions)
        previous = self.active()

        self.clear()

        try:
            self._installed = self._install_prepared(prepared)
        except ContributionInstallationError as install_error:
            try:
                rollback_prepared = self._prepare(previous)
                self._installed = self._install_prepared(
                    rollback_prepared
                )
            except Exception as rollback_error:
                raise ContributionInstallationError(
                    "Falha ao substituir contribuições e ao restaurar "
                    f"o conjunto anterior: {rollback_error}"
                ) from install_error
            raise ContributionInstallationError(
                "Falha ao substituir contribuições; o conjunto anterior "
                "foi restaurado."
            ) from install_error

    def _prepare(
        self,
        contributions: Iterable[ActionContribution],
    ) -> tuple[tuple[ActionContribution, QMenu], ...]:
        try:
            candidates = tuple(contributions)
        except Exception as exc:
            raise ContributionInstallationError(
                "Não foi possível preparar as contribuições."
            ) from exc

        contribution_ids: set[str] = set()
        prepared: list[tuple[ActionContribution, QMenu]] = []

        for contribution in candidates:
            if not isinstance(contribution, ActionContribution):
                raise ContributionInstallationError(
                    "Todas as contribuições devem ser ActionContribution."
                )
            if contribution.contribution_id in contribution_ids:
                raise ContributionInstallationError(
                    "ID de contribuição duplicado: "
                    f"{contribution.contribution_id}."
                )
            if contribution.menu_id is None:
                raise ContributionInstallationError(
                    "ActionContribution deve informar menu_id."
                )

            contribution_ids.add(contribution.contribution_id)
            try:
                menu = self._main_window.get_menu(contribution.menu_id)
            except Exception as exc:
                raise ContributionInstallationError(
                    "Não foi possível localizar o menu "
                    f"{contribution.menu_id}."
                ) from exc
            if not isinstance(menu, QMenu):
                raise ContributionInstallationError(
                    "get_menu() deve retornar uma instância de QMenu."
                )
            prepared.append((contribution, menu))

        return tuple(prepared)

    def _install_prepared(
        self,
        prepared: tuple[tuple[ActionContribution, QMenu], ...],
    ) -> list[_InstalledAction]:
        installed: list[_InstalledAction] = []
        try:
            for contribution, menu in prepared:
                installed.append(
                    self._materialize(contribution, menu)
                )
        except Exception as exc:
            cleanup_errors = self._cleanup_handles(installed)
            message = "Não foi possível instalar as contribuições."
            if cleanup_errors:
                message += (
                    f" A limpeza parcial também falhou "
                    f"({len(cleanup_errors)} erro(s))."
                )
            if isinstance(exc, ContributionInstallationError):
                raise ContributionInstallationError(message) from exc
            raise ContributionInstallationError(message) from exc

        return installed

    @staticmethod
    def _materialize(
        contribution: ActionContribution,
        menu: QMenu,
    ) -> _InstalledAction:
        action = QAction(contribution.text, menu)

        def connected_callback(_checked: bool = False) -> None:
            contribution.callback()

        connected = False
        try:
            action.triggered.connect(connected_callback)
            connected = True
            menu.addAction(action)
        except Exception as exc:
            cleanup_errors: list[Exception] = []
            if connected:
                try:
                    action.triggered.disconnect(connected_callback)
                except Exception as cleanup_error:
                    cleanup_errors.append(cleanup_error)
            try:
                menu.removeAction(action)
            except Exception as cleanup_error:
                cleanup_errors.append(cleanup_error)
            try:
                action.deleteLater()
            except Exception as cleanup_error:
                cleanup_errors.append(cleanup_error)

            message = "Não foi possível materializar a contribuição "
            message += f"{contribution.contribution_id}."
            if cleanup_errors:
                message += (
                    f" A limpeza parcial falhou "
                    f"({len(cleanup_errors)} erro(s))."
                )
            raise ContributionInstallationError(message) from exc

        return _InstalledAction(
            contribution=contribution,
            action=action,
            menu=menu,
            connected_callback=connected_callback,
        )

    @staticmethod
    def _cleanup_handles(
        installed: Iterable[_InstalledAction],
    ) -> list[Exception]:
        errors: list[Exception] = []
        for handle in reversed(tuple(installed)):
            try:
                handle.action.triggered.disconnect(
                    handle.connected_callback
                )
            except Exception as exc:
                errors.append(exc)
            try:
                handle.menu.removeAction(handle.action)
            except Exception as exc:
                errors.append(exc)
            try:
                handle.action.deleteLater()
            except Exception as exc:
                errors.append(exc)
        return errors

    @staticmethod
    def _raise_cleanup_error(errors: list[Exception]) -> None:
        raise ContributionInstallationError(
            "Falha ao limpar contribuições desktop "
            f"({len(errors)} erro(s)); todos os handles foram processados."
        ) from errors[0]
