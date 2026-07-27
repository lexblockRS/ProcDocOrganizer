"""Gerenciamento isolado do conjunto ativo de contribuições."""

from collections.abc import Iterable

from contracts import (
    ActionContribution,
    ApplicationModule,
    ContributionCategory,
    ContributionRegistration,
    DashboardContribution,
)

from .exceptions import ContributionError


class ContributionManager:
    """Instala e substitui snapshots validados de contribuições."""

    def __init__(self) -> None:
        self._active: tuple[ActionContribution, ...] = ()
        self._registered: list[ContributionRegistration] = []
        self._by_category: dict[
            ContributionCategory,
            list[ContributionRegistration],
        ] = {}
        self._by_application: dict[
            str,
            list[ContributionRegistration],
        ] = {}

    def active(self) -> tuple[ActionContribution, ...]:
        """Retorna um snapshot imutável das contribuições ativas."""

        return self._active

    def clear(self) -> None:
        """Remove todas as contribuições ativas."""

        self._active = ()

    def register(
        self,
        registration: ContributionRegistration,
    ) -> None:
        """Registra uma contribuição neutra sem instalá-la."""

        self.register_many((registration,))

    def register_many(
        self,
        registrations: Iterable[ContributionRegistration],
    ) -> None:
        """Registra atomicamente um conjunto de contribuições."""

        try:
            prepared = tuple(registrations)
        except Exception as exc:
            raise ContributionError(
                "Não foi possível preparar as contribuições."
            ) from exc
        if any(
            not isinstance(item, ContributionRegistration)
            for item in prepared
        ):
            raise ContributionError(
                "Todas as contribuições devem ser "
                "ContributionRegistration."
            )

        seen: set[tuple[str, object]] = set()
        for item in (*self._registered, *prepared):
            key = self._registration_key(item)
            if key in seen:
                raise ContributionError(
                    "Contribuição duplicada para a Application: "
                    f"{item.application_id}."
                )
            seen.add(key)
        self._registered.extend(prepared)
        for item in prepared:
            self._by_category.setdefault(item.category, []).append(item)
            self._by_application.setdefault(
                item.application_id,
                [],
            ).append(item)

    def register_application(
        self,
        application,
        contributions: Iterable[object],
        *,
        category: ContributionCategory = ContributionCategory.ACTION,
        priority: int = 0,
    ) -> None:
        """Registra contribuições de módulo ou Application legada."""

        application_id = self._application_id(application)
        if not isinstance(category, ContributionCategory):
            raise ContributionError(
                "Categoria de contribuição desconhecida."
            )
        if isinstance(priority, bool) or not isinstance(priority, int):
            raise ContributionError("priority deve ser um inteiro.")
        try:
            provided = tuple(contributions)
        except Exception as exc:
            raise ContributionError(
                "Não foi possível obter as contribuições da Application."
            ) from exc

        registrations = []
        for contribution in provided:
            if isinstance(contribution, ContributionRegistration):
                if contribution.application_id != application_id:
                    raise ContributionError(
                        "A origem da contribuição diverge da Application."
                    )
                registrations.append(contribution)
            else:
                try:
                    registrations.append(ContributionRegistration(
                        category=category,
                        application_id=application_id,
                        priority=priority,
                        contribution=contribution,
                    ))
                except (TypeError, ValueError) as exc:
                    raise ContributionError(str(exc)) from exc
        self.register_many(registrations)

    def all_contributions(self) -> tuple[ContributionRegistration, ...]:
        """Retorna todas as contribuições em ordem determinística."""

        return self._ordered(self._registered)

    def by_category(
        self,
        category: ContributionCategory,
    ) -> tuple[ContributionRegistration, ...]:
        """Consulta contribuições de uma categoria reconhecida."""

        if not isinstance(category, ContributionCategory):
            raise ContributionError(
                "Categoria de contribuição desconhecida."
            )
        return self._ordered(self._by_category.get(category, ()))

    def by_application(
        self,
        application_id: str,
    ) -> tuple[ContributionRegistration, ...]:
        """Consulta contribuições pertencentes a uma Application."""

        if (
            not isinstance(application_id, str)
            or not application_id.strip()
        ):
            raise ContributionError(
                "application_id deve ser um texto não vazio."
            )
        normalized = application_id.strip()
        return self._ordered(self._by_application.get(normalized, ()))

    def categories(self) -> tuple[ContributionCategory, ...]:
        """Lista somente categorias que possuem contribuições."""

        return tuple(sorted(
            self._by_category,
            key=lambda category: category.value,
        ))

    def dashboard_contributions(
        self,
    ) -> tuple[DashboardContribution, ...]:
        """Retorna somente payloads válidos da categoria Dashboard."""

        registrations = self.by_category(
            ContributionCategory.DASHBOARD
        )
        invalid = tuple(
            item for item in registrations
            if not isinstance(item.contribution, DashboardContribution)
        )
        if invalid:
            raise ContributionError(
                "A categoria Dashboard aceita apenas "
                "DashboardContribution."
            )
        return tuple(item.contribution for item in registrations)

    def applications(self) -> tuple[str, ...]:
        """Lista Applications que possuem contribuições."""

        return tuple(sorted(self._by_application))

    def clear_registered(self) -> None:
        """Limpa o catálogo neutro sem afetar o snapshot legado."""

        self._registered.clear()
        self._by_category.clear()
        self._by_application.clear()

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

    @staticmethod
    def _ordered(
        registrations: Iterable[ContributionRegistration],
    ) -> tuple[ContributionRegistration, ...]:
        prepared = tuple(registrations)
        positions = {id(item): index for index, item in enumerate(prepared)}
        return tuple(sorted(
            prepared,
            key=lambda item: (
                -item.priority,
                item.application_id,
                item.category.value,
                positions[id(item)],
            ),
        ))

    @staticmethod
    def _registration_key(
        registration: ContributionRegistration,
    ) -> tuple[str, object]:
        declared_id = getattr(
            registration.contribution,
            "contribution_id",
            None,
        )
        identity = (
            ("declared", declared_id.strip())
            if isinstance(declared_id, str) and declared_id.strip()
            else ("object", id(registration.contribution))
        )
        return registration.application_id, identity

    @staticmethod
    def _application_id(application) -> str:
        if isinstance(application, ApplicationModule):
            application_id = application.descriptor.application_id
        else:
            application_id = getattr(application, "application_id", None)
        if (
            not isinstance(application_id, str)
            or not application_id.strip()
        ):
            raise ContributionError(
                "Application deve possuir application_id válido."
            )
        return application_id.strip()
