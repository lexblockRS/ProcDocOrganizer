"""Provider neutro que projeta Findings relevantes como Insights."""

from presentation.coverage import CoverageFinding, CoverageResult, CoverageScope, CoverageState
from presentation.insights import (
    Insight, InsightAction, InsightCategory, InsightIdentity,
    InsightResourceReference, InsightResourceRole, InsightSeverity,
)
from presentation.workspace import WorkspaceSnapshot


class CoverageFindingInsightProvider:
    provider_id = "coverage_analysis"
    _ATTENTION_STATES = frozenset({CoverageState.ABSENT, CoverageState.INSUFFICIENT, CoverageState.INCONSISTENT})

    def __init__(self, coverage: CoverageResult) -> None:
        if not isinstance(coverage, CoverageResult):
            raise TypeError("coverage deve ser CoverageResult.")
        self._coverage = coverage

    def provide(self, workspace_snapshot: WorkspaceSnapshot) -> tuple[Insight, ...]:
        return tuple(self._project(item, workspace_snapshot) for item in self._coverage.findings if item.state in self._ATTENTION_STATES)

    def _project(self, finding: CoverageFinding, workspace: WorkspaceSnapshot) -> Insight:
        code = finding.reason_codes[0]
        categories = {
            CoverageScope.DOCUMENT: InsightCategory.ORGANIZATION,
            CoverageScope.EVIDENCE: InsightCategory.COMPLETENESS,
            CoverageScope.FACTUAL: InsightCategory.COMPLETENESS,
            CoverageScope.NORMATIVE: InsightCategory.COVERAGE,
            CoverageScope.OVERALL: InsightCategory.COVERAGE,
        }
        references = (InsightResourceReference(finding.subject, InsightResourceRole.SUBJECT),) + tuple(
            InsightResourceReference(item, InsightResourceRole.RELATED) for item in finding.related_resources
        )
        return Insight(
            InsightIdentity(self.provider_id, code, f"{finding.subject.resource_type.value}:{finding.subject.resource_id}"),
            categories[finding.scope],
            InsightSeverity.ERROR if finding.state is CoverageState.INCONSISTENT else InsightSeverity.WARNING,
            code.replace("_", " ").title(), finding.explanation, finding.explanation,
            references, (InsightAction.OPEN_RESOURCE,), workspace.revision,
        )


__all__ = ["CoverageFindingInsightProvider"]
