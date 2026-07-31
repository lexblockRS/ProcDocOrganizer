"""Projecao passiva do Workspace Dashboard 2.0."""

from __future__ import annotations

from dataclasses import dataclass

from applications.rsc.services.workspace_dashboard_service import WorkspaceDashboardSnapshot
from applications.rsc.operational_actions import ExecuteEvaluationAction
from presentation import NavigationIntent
from presentation.insights import InsightAction, InsightSeverity
from presentation.resources import ResourceIdentity, ResourceType


@dataclass(frozen=True, slots=True)
class WorkspaceSummaryView:
    project_name: str
    status: str
    score: str
    maturity: str
    last_evaluation: str


@dataclass(frozen=True, slots=True)
class PendingItemView:
    category: str
    severity: str
    title: str
    description: str
    action_label: str | None
    intent: NavigationIntent | None
    operational_action: ExecuteEvaluationAction | None = None

    @property
    def critical(self) -> bool:
        return self.severity == InsightSeverity.ERROR.value


@dataclass(frozen=True, slots=True)
class QuickStatisticView:
    label: str
    value: str


@dataclass(frozen=True, slots=True)
class CoverageSummaryView:
    state: str
    covered: int
    total: int
    ratio: str


@dataclass(frozen=True, slots=True)
class DocumentStatusView:
    total_documents: int
    used_documents: int
    unused_documents: int
    evidences_with_documents: int
    evidences_without_documents: int
    evidences_with_facts: int
    evidences_without_facts: int
    execution_facts: int
    pending_execution_facts: int
    normative_state: str


@dataclass(frozen=True, slots=True)
class InsightSummaryView:
    total: int
    errors: int
    warnings: int
    information: int
    success: int


@dataclass(frozen=True, slots=True)
class WorkspaceDashboardViewData:
    summary: WorkspaceSummaryView
    coverage: CoverageSummaryView
    insights: InsightSummaryView
    priority_actions: tuple[PendingItemView, ...]
    statistics: tuple[QuickStatisticView, ...]
    document_status: DocumentStatusView
    empty_message: str | None


class WorkspaceDashboardViewModel:
    """Adapta apenas WorkspaceSnapshot, CoverageResult e InsightCollection."""

    def __init__(self, snapshot: WorkspaceDashboardSnapshot) -> None:
        if not isinstance(snapshot, WorkspaceDashboardSnapshot):
            raise TypeError("snapshot deve ser WorkspaceDashboardSnapshot.")
        self._dashboard = self._project(snapshot)

    @property
    def dashboard(self) -> WorkspaceDashboardViewData:
        return self._dashboard

    @classmethod
    def _project(cls, snapshot: WorkspaceDashboardSnapshot) -> WorkspaceDashboardViewData:
        workspace, coverage, collection = snapshot.workspace, snapshot.coverage, snapshot.insights
        metadata = workspace.metadata
        document, evidence = coverage.document_coverage, coverage.evidence_coverage
        factual, normative, overall = coverage.factual_coverage, coverage.normative_coverage, coverage.overall_coverage
        actions = tuple(cls._insight(item) for item in collection.insights)
        counts = {severity.value: 0 for severity in InsightSeverity}
        for item in collection.insights:
            counts[item.severity.value] += 1
        return WorkspaceDashboardViewData(
            summary=WorkspaceSummaryView(
                str(metadata.get("project_name", workspace.project_id or "Nenhum projeto")),
                str(metadata.get("project_status", "indisponivel")),
                str(metadata.get("score", "0")),
                overall.state.value,
                str(metadata.get("last_evaluation", "Ainda nao executada")),
            ),
            coverage=CoverageSummaryView(overall.state.value, overall.covered, overall.total, f"{overall.covered}/{overall.total}"),
            insights=InsightSummaryView(collection.total, counts["error"], counts["warning"], counts["info"], counts["success"]),
            priority_actions=actions,
            statistics=(
                QuickStatisticView("Documents", str(document.total)),
                QuickStatisticView("Evidence", str(evidence.total)),
                QuickStatisticView("ExecutionFacts", str(factual.total)),
                QuickStatisticView("Bindings", str(factual.bound)),
                QuickStatisticView("Requirements", str(normative.requirements_total)),
                QuickStatisticView("Criteria", str(normative.criteria_total)),
                QuickStatisticView("Insights", str(collection.total)),
            ),
            document_status=DocumentStatusView(
                document.total, document.used, document.unused,
                evidence.with_documents, evidence.without_documents,
                evidence.with_execution_facts, evidence.without_execution_facts,
                factual.total, factual.unbound, normative.state.value,
            ),
            empty_message="Nenhum dado operacional disponivel." if overall.total == 0 else None,
        )

    @staticmethod
    def _insight(insight) -> PendingItemView:
        reference = insight.related_resources[0].identity if insight.related_resources else None
        action = insight.available_actions[0] if insight.available_actions else None
        intent = WorkspaceDashboardViewModel._intent(action, reference)
        operational = (
            ExecuteEvaluationAction(insight.identity.discriminator)
            if action is InsightAction.EXECUTE_EVALUATION
            and insight.identity.discriminator is not None
            else None
        )
        return PendingItemView(
            insight.category.value, insight.severity.value, insight.title,
            insight.message, None if action is None else action.value.replace("_", " ").title(), intent, operational,
        )

    @staticmethod
    def _intent(action: InsightAction | None, identity: ResourceIdentity | None) -> NavigationIntent | None:
        if action is InsightAction.EXECUTE_EVALUATION:
            return None
        if identity is None:
            return None
        factories = {
            ResourceType.DOCUMENT: NavigationIntent.open_document,
            ResourceType.EVIDENCE: NavigationIntent.open_evidence,
            ResourceType.EXECUTION_FACT: NavigationIntent.open_execution_fact,
            ResourceType.REQUIREMENT: NavigationIntent.open_requirement,
            ResourceType.CRITERION: NavigationIntent.open_criterion,
            ResourceType.EVALUATION: NavigationIntent.open_evaluation,
            ResourceType.REPORT: NavigationIntent.open_report,
        }
        return factories[identity.resource_type](identity.resource_id, origin="workspace_dashboard", metadata={"insight_action": action.value if action else ""})


__all__ = ["CoverageSummaryView", "DocumentStatusView", "InsightSummaryView", "PendingItemView", "QuickStatisticView", "WorkspaceDashboardViewData", "WorkspaceDashboardViewModel", "WorkspaceSummaryView"]
