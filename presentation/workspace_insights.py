"""Providers e coordenação da infraestrutura de Workspace Insights."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from .insights import (
    Insight,
    InsightAction,
    InsightCategory,
    InsightCollection,
    InsightIdentity,
    InsightSeverity,
)
from .workspace import WorkspaceSnapshot


class WorkspaceInsightError(ValueError):
    """Falha contratual ao consolidar Insights do Workspace."""


class DuplicateInsightProvider(WorkspaceInsightError):
    """Dois Providers reivindicam a mesma identidade de origem."""


class DuplicateInsightIdentity(WorkspaceInsightError):
    """Providers produziram a mesma identidade derivada."""


class InvalidInsightProviderResult(WorkspaceInsightError):
    """Um Provider retornou resultado fora do contrato."""


@runtime_checkable
class WorkspaceInsightProvider(Protocol):
    def provide(
        self, workspace_snapshot: WorkspaceSnapshot
    ) -> tuple[Insight, ...]: ...


class WorkspaceInsightService:
    """Executa Providers e consolida seus DTOs sem reinterpretá-los."""

    def __init__(
        self, providers: tuple[WorkspaceInsightProvider, ...]
    ) -> None:
        if not isinstance(providers, tuple):
            raise TypeError(
                "providers deve ser tuple de WorkspaceInsightProvider."
            )
        provider_ids: set[str] = set()
        for provider in providers:
            if not isinstance(provider, WorkspaceInsightProvider):
                raise TypeError(
                    "providers deve conter WorkspaceInsightProvider."
                )
            provider_id = getattr(provider, "provider_id", None)
            if not isinstance(provider_id, str) or not provider_id.strip():
                raise TypeError(
                    "Todo Provider deve declarar provider_id textual."
                )
            normalized = provider_id.strip()
            if normalized in provider_ids:
                raise DuplicateInsightProvider(
                    f"Provider duplicado: {normalized}."
                )
            provider_ids.add(normalized)
        self._providers = providers

    @property
    def providers(self) -> tuple[WorkspaceInsightProvider, ...]:
        return self._providers

    def collect(
        self, workspace_snapshot: WorkspaceSnapshot
    ) -> InsightCollection:
        if not isinstance(workspace_snapshot, WorkspaceSnapshot):
            raise TypeError(
                "workspace_snapshot deve ser WorkspaceSnapshot."
            )
        collected: list[Insight] = []
        identities = set()
        for provider in self._providers:
            produced = provider.provide(workspace_snapshot)
            if not isinstance(produced, tuple) or any(
                not isinstance(item, Insight) for item in produced
            ):
                raise InvalidInsightProviderResult(
                    f"{provider.provider_id} deve retornar tuple de Insight."
                )
            for insight in produced:
                if insight.identity.provider_id != provider.provider_id.strip():
                    raise InvalidInsightProviderResult(
                        f"{provider.provider_id} produziu origem divergente."
                    )
                if insight.source_revision != workspace_snapshot.revision:
                    raise InvalidInsightProviderResult(
                        f"{provider.provider_id} produziu revisão divergente."
                    )
                if insight.identity in identities:
                    raise DuplicateInsightIdentity(
                        "Insight duplicado: "
                        f"{insight.identity.provider_id}/"
                        f"{insight.identity.insight_code}."
                    )
                identities.add(insight.identity)
                collected.append(insight)
        return InsightCollection(
            insights=tuple(collected),
            total=len(collected),
            workspace_revision=workspace_snapshot.revision,
        )


class ProjectEvaluationInsightProvider:
    """Projeta a ausência operacional de avaliação no Workspace."""

    provider_id = "project_evaluation"
    insight_code = "project.not_evaluated"

    def provide(
        self, workspace_snapshot: WorkspaceSnapshot
    ) -> tuple[Insight, ...]:
        if not isinstance(workspace_snapshot, WorkspaceSnapshot):
            raise TypeError(
                "workspace_snapshot deve ser WorkspaceSnapshot."
            )
        if (
            workspace_snapshot.project_id is None
            or workspace_snapshot.current_evaluation is not None
        ):
            return ()
        return (Insight(
            identity=InsightIdentity(
                self.provider_id,
                self.insight_code,
                workspace_snapshot.project_id,
            ),
            category=InsightCategory.COMPLETENESS,
            severity=InsightSeverity.WARNING,
            title="Avaliação pendente",
            message="Projeto ainda não avaliado.",
            explanation=(
                "O Workspace atual não possui uma avaliação selecionada."
            ),
            related_resources=(),
            available_actions=(InsightAction.EXECUTE_EVALUATION,),
            source_revision=workspace_snapshot.revision,
        ),)


__all__ = [
    "DuplicateInsightIdentity",
    "DuplicateInsightProvider",
    "InvalidInsightProviderResult",
    "ProjectEvaluationInsightProvider",
    "WorkspaceInsightError",
    "WorkspaceInsightProvider",
    "WorkspaceInsightService",
]
