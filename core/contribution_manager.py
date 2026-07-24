"""Gerenciamento isolado do conjunto ativo de contribuições."""

from collections.abc import Iterable

from contracts import ActionContribution

from .exceptions import ContributionError


class ContributionManager:
    """Instala e substitui snapshots validados de contribuições."""

    def __init__(self) -> None:
        self._active: tuple[ActionContribution, ...] = ()

    def active(self) -> tuple[ActionContribution, ...]:
        """Retorna um snapshot imutável das contribuições ativas."""

        return self._active

    def clear(self) -> None:
        """Remove todas as contribuições ativas."""

        self._active = ()

    def activate(
        self,
        contributions: Iterable[ActionContribution],
    ) -> None:
        """Ativa contribuições quando ainda não existe um conjunto ativo."""

        if self._active:
            raise ContributionError("Já existem contribuições ativas.")

        prepared = self._prepare(contributions)
        self._active = prepared

    def replace(
        self,
        contributions: Iterable[ActionContribution],
    ) -> None:
        """Substitui atomicamente o conjunto de contribuições ativas."""

        prepared = self._prepare(contributions)
        self._active = prepared

    @staticmethod
    def _prepare(
        contributions: Iterable[ActionContribution],
    ) -> tuple[ActionContribution, ...]:
        try:
            prepared = tuple(contributions)
        except Exception as exc:
            raise ContributionError(
                "Não foi possível preparar as contribuições."
            ) from exc

        contribution_ids: set[str] = set()
        for contribution in prepared:
            if not isinstance(contribution, ActionContribution):
                raise ContributionError(
                    "Todas as contribuições devem ser ActionContribution."
                )
            if contribution.contribution_id in contribution_ids:
                raise ContributionError(
                    "ID de contribuição duplicado: "
                    f"{contribution.contribution_id}."
                )
            contribution_ids.add(contribution.contribution_id)

        return prepared
