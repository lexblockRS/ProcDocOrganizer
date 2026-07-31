"""Casos de uso do Project Explorer, independentes da interface concreta."""

from __future__ import annotations

from decimal import Decimal
from applications.rsc.normative_catalog import OFFICIAL_NORMATIVE_CATALOG
from applications.rsc.services.rsc_execution_service import (
    RSCExecutionResult,
    RSCExecutionService,
)
from platform_sdk import Evidence, ExecutionBinding, ExecutionFact, Project


class ProjectExplorerApplicationService:
    """Coordena Project, Workspace e dados editoriais para a interface."""

    def __init__(
        self,
        project_store,
        evidence_store,
        fact_store,
        binding_store,
        workspace_factory,
        workspace_locator,
        application_registry,
    ) -> None:
        self._projects = project_store
        self._evidences = evidence_store
        self._facts = fact_store
        self._bindings = binding_store
        self._workspace_factory = workspace_factory
        self._workspace_locator = workspace_locator
        self._applications = application_registry

    @property
    def workspace_base(self):
        return self._workspace_locator.base_directory

    def application_descriptors(self):
        return self._applications.list()

    def create_project(self, *, name: str, application_id: str):
        descriptor = self._applications.get_descriptor(application_id)
        project = Project.create(
            name=name,
            application_id=descriptor.application_id,
        )
        workspace = self._workspace_factory.create(project)
        self._projects.save(project)
        return project, workspace

    def list_projects(self):
        return self._projects.list_all()

    def open_project(self, project_id: str):
        project = self._projects.get(project_id)
        workspace = self._workspace_locator.locate(project)
        if workspace is None:
            raise FileNotFoundError(
                f"Workspace não encontrado para {project.aggregate_id}."
            )
        return project, workspace

    def list_evidences(self, project_id: str):
        return self._evidences.list_for_project(project_id)

    def get_evidence(self, evidence_id: str):
        return self._evidences.get(evidence_id)

    def create_evidence(
        self, *, project_id: str, title: str, description: str = ""
    ) -> Evidence:
        evidence = Evidence.create(
            project_id=project_id,
            title=title,
            description=description,
        )
        self._evidences.save(evidence)
        return evidence

    def edit_evidence(
        self,
        evidence_id: str,
        *,
        project_id: str,
        title: str,
        description: str | None = None,
    ) -> Evidence:
        evidence = self._evidences.get(evidence_id)
        if evidence.project_id != project_id:
            raise ValueError("Evidence não pertence ao Project aberto.")
        updated = evidence.edit(title=title, description=description)
        self._evidences.save(updated)
        return updated

    def attach_document(
        self, evidence_id: str, *, project_id: str, document
    ) -> Evidence:
        evidence = self._evidences.get(evidence_id)
        if evidence.project_id != project_id:
            raise ValueError("Evidence não pertence ao Project aberto.")
        updated = evidence.add_document(document)
        self._evidences.save(updated)
        return updated

    def delete_evidence(self, evidence_id: str, *, project_id: str) -> None:
        evidence = self._evidences.get(evidence_id)
        if evidence.project_id != project_id:
            raise ValueError("Evidence não pertence ao Project aberto.")
        self._evidences.delete(evidence_id)

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
        fact = ExecutionFact.create(
            project_id=project_id,
            evidence_id=evidence_id,
            fact_type=fact_type,
            description=description,
            quantity=quantity,
            unit=unit,
        )
        self._facts.save(fact)
        return fact

    def edit_fact(
        self,
        execution_fact_id: str,
        *,
        project_id: str,
        evidence_id: str,
        description: str,
    ) -> ExecutionFact:
        fact = self._facts.get(execution_fact_id)
        if fact.project_id != project_id or fact.evidence_id != evidence_id:
            raise ValueError(
                "ExecutionFact não pertence à Evidence selecionada."
            )
        updated = fact.edit(description=description)
        self._facts.save(updated)
        return updated

    def delete_fact(
        self,
        execution_fact_id: str,
        *,
        project_id: str,
        evidence_id: str,
    ) -> None:
        fact = self._facts.get(execution_fact_id)
        if fact.project_id != project_id or fact.evidence_id != evidence_id:
            raise ValueError(
                "ExecutionFact não pertence à Evidence selecionada."
            )
        self._facts.delete(execution_fact_id)

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
        return updated

    def delete_binding_for_fact(self, execution_fact_id: str) -> None:
        binding = self._bindings.get_for_fact(execution_fact_id)
        if binding is not None:
            self._bindings.delete(binding.aggregate_id)

    def execute(self, project: Project) -> RSCExecutionResult:
        return RSCExecutionService(
            self._evidences, self._facts, self._bindings
        ).execute(project)

    def close(self) -> None:
        self._bindings.close()
        self._facts.close()
        self._evidences.close()
        self._projects.close()

    @staticmethod
    def _criterion(criterion_id: str):
        definition = OFFICIAL_NORMATIVE_CATALOG.find(criterion_id)
        if definition is None:
            raise ValueError(f"Critério desconhecido: {criterion_id}.")
        return definition


__all__ = ["ProjectExplorerApplicationService"]
