"""Casos de uso do Project Explorer, independentes da interface concreta."""

from __future__ import annotations

from decimal import Decimal
from applications.rsc.normative_catalog import OFFICIAL_NORMATIVE_CATALOG
from applications.rsc.services.rsc_execution_service import (
    RSCExecutionResult,
    RSCExecutionService,
)
from applications.rsc.services.workspace_dashboard_service import (
    WorkspaceDashboardService,
)
from applications.rsc.services.review_workspace_service import ReviewWorkspaceService
from platform_sdk import Evidence, ExecutionBinding, ExecutionFact, Project
from presentation.coverage import (
    BindingCoverageReference, CoverageInput, DocumentCoverageReference,
    EvaluationCoverageSnapshot, EvidenceCoverageReference,
    ExecutionFactCoverageReference, NormativeCoverageReference,
)
from presentation.coverage_analyzer import CoverageAnalyzer
from presentation.coverage_insights import CoverageFindingInsightProvider
from presentation.workspace_insights import ProjectEvaluationInsightProvider, WorkspaceInsightService
from presentation.perspectives import PerspectiveId
from presentation.resources import ResourceIdentity, ResourceType
from presentation.workspace import WorkspaceSnapshot, WorkspaceState


class ProjectExplorerApplicationService:
    """Coordena Project, Workspace e dados editoriais para a interface."""

    def __init__(
        self,
        project,
        evidence_store,
        fact_store,
        binding_store,
        document_repository,
        operational_state,
        workspace_root,
    ) -> None:
        if not isinstance(project, Project):
            raise TypeError("project deve ser platform_sdk.Project.")
        self._project = project
        self._evidences = evidence_store
        self._facts = fact_store
        self._bindings = binding_store
        self._documents = document_repository
        self._operational_state = operational_state
        self._workspace_root = workspace_root
        self._dashboard = WorkspaceDashboardService()
        self._review = ReviewWorkspaceService()
        self._last_execution_result = None
        self._last_evaluation_at = None

    @property
    def project(self):
        return self._project

    @property
    def workspace_root(self):
        return self._workspace_root

    @property
    def last_execution_result(self):
        return self._last_execution_result

    @property
    def last_evaluation_at(self):
        return self._last_evaluation_at

    @property
    def operational_revision(self) -> int:
        return self._operational_state.current()

    def list_evidences(self, project_id: str):
        self._require_project(project_id)
        return self._evidences.list_for_project(project_id)

    def get_evidence(self, evidence_id: str):
        return self._evidences.get(evidence_id)

    def find_evidence_for_document(self, project_id: str, document_id: str):
        self._require_project(project_id)
        return next((
            evidence
            for evidence in self._evidences.list_for_project(project_id)
            if any(item.document_id == document_id for item in evidence.documents)
        ), None)

    def create_evidence(
        self, *, project_id: str, title: str, description: str = ""
    ) -> Evidence:
        self._require_project(project_id)
        evidence = Evidence.create(
            project_id=project_id,
            title=title,
            description=description,
        )
        self._evidences.save(evidence)
        self._changed("evidence.created")
        return evidence

    def edit_evidence(
        self,
        evidence_id: str,
        *,
        project_id: str,
        title: str,
        description: str | None = None,
    ) -> Evidence:
        self._require_project(project_id)
        evidence = self._evidences.get(evidence_id)
        if evidence.project_id != project_id:
            raise ValueError("Evidence não pertence ao Project aberto.")
        updated = evidence.edit(title=title, description=description)
        self._evidences.save(updated)
        self._changed("evidence.updated")
        return updated

    def attach_document(
        self, evidence_id: str, *, project_id: str, document
    ) -> Evidence:
        self._require_project(project_id)
        evidence = self._evidences.get(evidence_id)
        if evidence.project_id != project_id:
            raise ValueError("Evidence não pertence ao Project aberto.")
        updated = evidence.add_document(document)
        self._evidences.save(updated)
        self._changed("evidence.document_attached")
        return updated

    def delete_evidence(self, evidence_id: str, *, project_id: str) -> None:
        self._require_project(project_id)
        evidence = self._evidences.get(evidence_id)
        if evidence.project_id != project_id:
            raise ValueError("Evidence não pertence ao Project aberto.")
        self._evidences.delete(evidence_id)
        self._changed("evidence.deleted")

    def list_facts(self, evidence_id: str):
        return self._facts.list_for_evidence(evidence_id)

    def get_fact(self, execution_fact_id: str):
        return self._facts.get(execution_fact_id)

    def create_fact(
        self,
        *,
        project_id: str,
        evidence_id: str,
        fact_type: str,
        description: str,
        quantity: Decimal | None,
        unit: str,
    ) -> ExecutionFact:
        self._require_project(project_id)
        fact = ExecutionFact.create(
            project_id=project_id,
            evidence_id=evidence_id,
            fact_type=fact_type,
            description=description,
            quantity=quantity,
            unit=unit,
        )
        self._facts.save(fact)
        self._changed("execution_fact.created")
        return fact

    def edit_fact(
        self,
        execution_fact_id: str,
        *,
        project_id: str,
        evidence_id: str,
        description: str,
    ) -> ExecutionFact:
        self._require_project(project_id)
        fact = self._facts.get(execution_fact_id)
        if fact.project_id != project_id or fact.evidence_id != evidence_id:
            raise ValueError(
                "ExecutionFact não pertence à Evidence selecionada."
            )
        updated = fact.edit(description=description)
        self._facts.save(updated)
        self._changed("execution_fact.updated")
        return updated

    def delete_fact(
        self,
        execution_fact_id: str,
        *,
        project_id: str,
        evidence_id: str,
    ) -> None:
        self._require_project(project_id)
        fact = self._facts.get(execution_fact_id)
        if fact.project_id != project_id or fact.evidence_id != evidence_id:
            raise ValueError(
                "ExecutionFact não pertence à Evidence selecionada."
            )
        self._facts.delete(execution_fact_id)
        self._changed("execution_fact.deleted")

    def get_binding_for_fact(self, execution_fact_id: str):
        return self._bindings.get_for_fact(execution_fact_id)

    @staticmethod
    def criterion_definitions():
        return tuple(OFFICIAL_NORMATIVE_CATALOG)

    def create_binding(
        self, *, execution_fact_id: str, criterion_id: str
    ) -> ExecutionBinding:
        if self._bindings.get_for_fact(execution_fact_id) is not None:
            raise ValueError("ExecutionFact já possui Binding.")
        definition = self._criterion(criterion_id)
        binding = ExecutionBinding.create(
            execution_fact_id=execution_fact_id,
            criterion_id=definition.code,
            requirement_id=definition.requirement_id,
            execution_rule_id=definition.execution_rule_id,
        )
        self._bindings.save(binding)
        self._changed("binding.created")
        return binding

    def rebind(
        self, *, execution_fact_id: str, criterion_id: str
    ) -> ExecutionBinding:
        binding = self._bindings.get_for_fact(execution_fact_id)
        if binding is None:
            raise ValueError("ExecutionFact não possui Binding.")
        definition = self._criterion(criterion_id)
        updated = binding.rebind(
            criterion_id=definition.code,
            requirement_id=definition.requirement_id,
            execution_rule_id=definition.execution_rule_id,
        )
        self._bindings.save(updated)
        self._changed("binding.updated")
        return updated

    def delete_binding_for_fact(self, execution_fact_id: str) -> None:
        binding = self._bindings.get_for_fact(execution_fact_id)
        if binding is not None:
            self._bindings.delete(binding.aggregate_id)
            self._changed("binding.deleted")

    def execute(self, project: Project | None = None) -> RSCExecutionResult:
        from datetime import datetime, timezone

        target = self._project if project is None else project
        self._require_project(target.aggregate_id)
        result = RSCExecutionService(
            self._evidences, self._facts, self._bindings
        ).execute(target)
        self._last_execution_result = result
        self._last_evaluation_at = datetime.now(timezone.utc)
        return result

    def _presentation_inputs(
        self, project: Project, *, process=None, last_evaluation=None,
        workspace_snapshot=None,
    ):
        self._require_project(project.aggregate_id)
        evidences = tuple(self._evidences.list_for_project(project.aggregate_id))
        facts = tuple(fact for evidence in evidences for fact in self._facts.list_for_evidence(evidence.aggregate_id))
        bindings = tuple(binding for fact in facts if (binding := self._bindings.get_for_fact(fact.aggregate_id)) is not None)
        documents = tuple(self._documents.list_all())
        document_map = {document.id: document for document in documents}
        evidence_ids_by_document = {
            document_id: tuple(ResourceIdentity(ResourceType.EVIDENCE, evidence.aggregate_id)
                               for evidence in evidences if any(doc.document_id == document_id for doc in evidence.documents))
            for document_id in document_map
        }
        facts_by_evidence = {evidence.aggregate_id: tuple(fact for fact in facts if fact.evidence_id == evidence.aggregate_id) for evidence in evidences}
        coverage_input = CoverageInput(
            project_id=project.aggregate_id,
            project_revision=self._operational_state.current(),
            documents=tuple(DocumentCoverageReference(ResourceIdentity(ResourceType.DOCUMENT, document_id), evidence_ids_by_document[document_id]) for document_id in sorted(document_map)),
            evidences=tuple(EvidenceCoverageReference(
                ResourceIdentity(ResourceType.EVIDENCE, evidence.aggregate_id),
                tuple(ResourceIdentity(ResourceType.DOCUMENT, doc.document_id) for doc in evidence.documents),
                tuple(ResourceIdentity(ResourceType.EXECUTION_FACT, fact.aggregate_id) for fact in facts_by_evidence[evidence.aggregate_id]),
            ) for evidence in evidences),
            execution_facts=tuple(ExecutionFactCoverageReference(ResourceIdentity(ResourceType.EXECUTION_FACT, fact.aggregate_id), ResourceIdentity(ResourceType.EVIDENCE, fact.evidence_id)) for fact in facts),
            bindings=tuple(BindingCoverageReference(binding.aggregate_id, ResourceIdentity(ResourceType.EXECUTION_FACT, binding.execution_fact_id)) for binding in bindings),
            evaluation=self._coverage_evaluation(process),
        )
        workspace = WorkspaceSnapshot(
            state=WorkspaceState.READY,
            active_perspective=PerspectiveId("workspace_dashboard"),
            revision=(0 if workspace_snapshot is None else workspace_snapshot.revision),
            workspace_id=f"project:{project.aggregate_id}",
            project_id=project.aggregate_id,
            current_evaluation=None if process is None else process.process_id,
            active_filters=(() if workspace_snapshot is None else workspace_snapshot.active_filters),
            metadata={
                "project_name": project.name,
                "project_status": project.state.value,
                "score": "0" if process is None or process.total_score is None else str(process.total_score),
                "last_evaluation": "Ainda nao executada" if last_evaluation is None else last_evaluation.isoformat(),
            },
        )
        return workspace, coverage_input

    def _presentation_analysis(
        self, project: Project, *, process=None, last_evaluation=None,
        workspace_snapshot=None,
    ):
        workspace, coverage_input = self._presentation_inputs(
            project, process=process, last_evaluation=last_evaluation,
            workspace_snapshot=workspace_snapshot,
        )
        coverage = CoverageAnalyzer().analyze(coverage_input)
        insights = WorkspaceInsightService((
            ProjectEvaluationInsightProvider(),
            CoverageFindingInsightProvider(coverage),
        )).collect(workspace)
        return workspace, coverage, insights

    def dashboard_snapshot(
        self, project: Project, *, process=None, last_evaluation=None,
        workspace_snapshot=None,
    ):
        sources = self._presentation_analysis(
            project, process=process, last_evaluation=last_evaluation,
            workspace_snapshot=workspace_snapshot,
        )
        return self._dashboard.summarize(*sources)

    def presentation_snapshots(
        self, project: Project, *, process=None, last_evaluation=None,
        workspace_snapshot=None,
    ):
        workspace, coverage, insights = self._presentation_analysis(
            project, process=process, last_evaluation=last_evaluation,
            workspace_snapshot=workspace_snapshot,
        )
        return (
            self._dashboard.summarize(workspace, coverage, insights),
            self._review.compose(workspace, coverage, insights),
        )

    def review_snapshot(
        self, project: Project, *, process=None, last_evaluation=None,
        workspace_snapshot=None,
    ):
        workspace, coverage, insights = self._presentation_analysis(
            project, process=process, last_evaluation=last_evaluation,
            workspace_snapshot=workspace_snapshot,
        )
        return self._review.compose(
            workspace, coverage, insights
        )

    @staticmethod
    def _coverage_evaluation(process):
        if process is None:
            return None
        fact_identity = lambda value: ResourceIdentity(ResourceType.EXECUTION_FACT, value)
        normative = tuple(
            NormativeCoverageReference(
                ResourceIdentity(ResourceType.REQUIREMENT, item.requirement_id),
                item.aggregation_trace.operation,
            )
            for item in process.requirement_scores
        ) + tuple(
            NormativeCoverageReference(ResourceIdentity(ResourceType.CRITERION, item.criterion_id), item.scoring_state.value)
            for item in process.criterion_scores
        )
        return EvaluationCoverageSnapshot(
            process.process_id, process.revision,
            tuple(ResourceIdentity(ResourceType.EVIDENCE, value) for value in process.result.used_evidence_ids) if process.result else (),
            tuple(fact_identity(item.execution_fact_id) for item in process.execution_facts),
            tuple(fact_identity(item.execution_fact_id) for item in process.validations),
            tuple(fact_identity(item.execution_fact_id) for item in process.compatibilities),
            normative,
        )

    def close(self) -> None:
        self._bindings.close()
        self._facts.close()
        self._evidences.close()
        self._last_execution_result = None
        self._last_evaluation_at = None

    def _changed(self, reason: str) -> None:
        self._operational_state.increment(reason)

    def _require_project(self, project_id: str) -> None:
        if project_id != self._project.aggregate_id:
            raise ValueError("Operação pertence a outro Project.")

    @staticmethod
    def _criterion(criterion_id: str):
        definition = OFFICIAL_NORMATIVE_CATALOG.find(criterion_id)
        if definition is None:
            raise ValueError(f"Critério desconhecido: {criterion_id}.")
        return definition


__all__ = ["ProjectExplorerApplicationService"]
