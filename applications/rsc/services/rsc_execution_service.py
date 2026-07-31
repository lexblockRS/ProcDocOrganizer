"""Orquestração de aplicação do pipeline normativo existente."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
import json
from pathlib import Path
from time import perf_counter
from typing import Protocol

from applications.rsc.constraint_evaluation import FactUsed
from applications.rsc.criterion_assessment import (
    AssessmentTraceability,
    CandidateStatus,
    ConsolidatedConstraintStatus,
    CriterionAssessment,
    CriterionAssessmentStatus,
    DocumentationStatus,
)
from applications.rsc.criterion_candidates import (
    FactualTraceability,
    NormativeOrigin,
)
from applications.rsc.execution_compatibility import (
    CompatibilityState,
    ExecutionCompatibilityEvaluator,
)
from applications.rsc.execution_contracts import ExecutionContractResolver
from applications.rsc.execution_facts import (
    CanonicalActivity,
    CanonicalDocument,
    CanonicalFact,
    CanonicalFactType,
    CanonicalFunctionalExercise,
    CanonicalTimeInterval,
    ConfidenceOrigin,
    ExecutionFact as NormativeExecutionFact,
    ExecutionFactCollection,
    ExecutionNormativeTraceability,
    ExecutionOccurrence,
    FactTraceability,
    Measurement,
    MeasurementValidationState,
    OverlapStatus,
)
from applications.rsc.execution_validation import ExecutionValidator
from applications.rsc.normative_catalog import OFFICIAL_NORMATIVE_CATALOG
from applications.rsc.requirement_scoring import RequirementScoreAggregator
from applications.rsc.rsc_process import (
    IntendedRSCLevel,
    RSCInstitution,
    RSCProcess,
    RSCProcessDocument,
    RSCProcessEvidence,
    RSCProcessPendingFact,
    RSCProcessResult,
    RSCServer,
)
from applications.rsc.scoring_kernel import (
    CriterionScoringKernel,
    ScoringState,
)
from applications.rsc.temporal_attention import TemporalAttentionCollection
from platform_sdk import (
    Evidence,
    ExecutionBinding,
    ExecutionFact,
    Project,
)


class _EvidenceSource(Protocol):
    def list_for_project(self, project_id: str) -> tuple[Evidence, ...]: ...


class _FactSource(Protocol):
    def list_for_evidence(
        self, evidence_id: str
    ) -> tuple[ExecutionFact, ...]: ...


class _BindingSource(Protocol):
    def get_for_fact(
        self, execution_fact_id: str
    ) -> ExecutionBinding | None: ...


class RSCExecutionError(RuntimeError):
    """Os dados cadastrados não permitem executar o pipeline."""


@dataclass(frozen=True, slots=True)
class RSCExecutionResult:
    process: RSCProcess
    execution_fact_count: int
    valid_binding_count: int
    criterion_score_count: int
    requirement_score_count: int
    incompatibility_count: int
    total_score: Decimal
    elapsed_seconds: float


class RSCExecutionService:
    """Localiza fatos e orquestra componentes normativos sem criar regras."""

    def __init__(
        self,
        evidence_source: _EvidenceSource,
        fact_source: _FactSource,
        binding_source: _BindingSource,
        *,
        normative_directory: str | Path | None = None,
    ) -> None:
        self._evidences = evidence_source
        self._facts = fact_source
        self._bindings = binding_source
        root = Path(__file__).resolve().parents[3]
        directory = (
            Path(normative_directory)
            if normative_directory is not None
            else root / "docs" / "normative"
        )
        self._rules_path = directory / "criterion_execution_rules.json"
        self._manifest_path = directory / "execution_rules_manifest.json"
        self._criteria_path = directory / "decree_criteria.json"
        self._rules = _rules_by_criterion(self._rules_path)

    def execute(self, project: Project) -> RSCExecutionResult:
        if not isinstance(project, Project):
            raise TypeError("project deve ser platform_sdk.Project.")
        started = perf_counter()
        evidences = self._evidences.list_for_project(project.aggregate_id)
        facts = tuple(
            fact
            for evidence in evidences
            for fact in self._facts.list_for_evidence(evidence.aggregate_id)
        )
        evidence_ids = {item.aggregate_id for item in evidences}
        for fact in facts:
            if (
                fact.project_id != project.aggregate_id
                or fact.evidence_id not in evidence_ids
            ):
                raise RSCExecutionError(
                    f"ExecutionFact inconsistente: {fact.aggregate_id}."
                )
        bindings, unbound_facts = self._classify_bindings(facts)
        evidence_index = {
            evidence.aggregate_id: evidence for evidence in evidences
        }
        normative_facts = ExecutionFactCollection(tuple(
            self._project_fact(
                fact,
                bindings[fact.aggregate_id],
                evidence_index[fact.evidence_id],
            )
            for fact in facts
            if fact.aggregate_id in bindings
        ))

        validations = ExecutionValidator.from_files(
            self._rules_path, self._manifest_path
        ).validate(normative_facts)
        compatibilities = ExecutionCompatibilityEvaluator.from_catalog(
            OFFICIAL_NORMATIVE_CATALOG
        ).evaluate(normative_facts, validations)
        contracts = ExecutionContractResolver.from_files(
            self._rules_path,
            self._manifest_path,
            self._criteria_path,
        ).resolve(normative_facts, validations, compatibilities)
        criterion_scores = CriterionScoringKernel().score(contracts)
        requirement_scores = RequirementScoreAggregator().aggregate(
            criterion_scores
        )

        process = self._create_process(
            project, evidences, facts, bindings
        )
        process = (
            process.record_execution_facts(
                normative_facts,
                tuple(
                    RSCProcessPendingFact(
                        execution_fact_id=fact.aggregate_id,
                        evidence_id=fact.evidence_id,
                        description=fact.description,
                        reason="ExecutionFact aguardando enquadramento.",
                    )
                    for fact in unbound_facts
                ),
            )
            .record_validations(validations)
            .record_compatibilities(compatibilities)
            .record_criterion_scores(criterion_scores)
            .record_requirement_scores(requirement_scores)
        )
        total = sum(
            (
                item.total_score
                for item in requirement_scores.requirement_scores
            ),
            Decimal(0),
        )
        executed = tuple(
            score.criterion_id
            for score in criterion_scores
            if score.scoring_state is ScoringState.EXECUTED
        )
        non_computable = tuple(
            score.criterion_id
            for score in criterion_scores
            if score.scoring_state is not ScoringState.EXECUTED
        )
        process = process.consolidate(RSCProcessResult(
            total_score=total,
            computable_criterion_ids=executed,
            non_computable_criterion_ids=non_computable,
            pending_items=tuple(
                item
                for score in criterion_scores
                for item in score.source_contract.unresolved_items
            ) + tuple(
                f"ExecutionFact aguardando enquadramento: {fact.aggregate_id}."
                for fact in unbound_facts
            ),
            temporal_attentions=TemporalAttentionCollection(),
            used_evidence_ids=tuple(
                dict.fromkeys(
                    fact.evidence_id
                    for fact in facts
                    if fact.aggregate_id in bindings
                )
            ),
            explanation="Pipeline normativo executado por solicitação.",
        ))
        return RSCExecutionResult(
            process=process,
            execution_fact_count=len(facts),
            valid_binding_count=len(bindings),
            criterion_score_count=len(criterion_scores),
            requirement_score_count=len(requirement_scores),
            incompatibility_count=sum(
                item.compatibility_state is CompatibilityState.INCOMPATIBLE
                for item in compatibilities
            ),
            total_score=total,
            elapsed_seconds=perf_counter() - started,
        )

    def _classify_bindings(
        self, facts: tuple[ExecutionFact, ...]
    ) -> tuple[
        dict[str, ExecutionBinding], tuple[ExecutionFact, ...]
    ]:
        result = {}
        pending = []
        for fact in facts:
            binding = self._bindings.get_for_fact(fact.aggregate_id)
            if binding is None:
                pending.append(fact)
                continue
            definition = OFFICIAL_NORMATIVE_CATALOG.find(
                binding.criterion_id
            )
            if (
                definition is None
                or definition.requirement_id != binding.requirement_id
                or definition.execution_rule_id
                != binding.execution_rule_id
            ):
                raise RSCExecutionError(
                    f"Binding inconsistente: {binding.aggregate_id}."
                )
            result[fact.aggregate_id] = binding
        return result, tuple(pending)

    def _project_fact(
        self,
        fact: ExecutionFact,
        binding: ExecutionBinding,
        evidence: Evidence,
    ) -> NormativeExecutionFact:
        rule = self._rules[binding.criterion_id]
        definition = OFFICIAL_NORMATIVE_CATALOG.find(binding.criterion_id)
        origin = FactualTraceability(
            activity_id=fact.aggregate_id,
            functional_exercise_id=fact.aggregate_id,
            functional_assignment_evidence_id=binding.aggregate_id,
            evidence_id=evidence.aggregate_id,
            document_id=(
                evidence.documents[0].document_id
                if evidence.documents
                else evidence.aggregate_id
            ),
            document_identity=(
                evidence.documents[0].document_id
                if evidence.documents
                else evidence.aggregate_id
            ),
            accepted_document_id=None,
        )
        normative_origin = NormativeOrigin(
            document_id="DEC13048",
            legal_reference=rule["article_reference"],
            hierarchy=tuple(rule["traceability"]),
        )
        assessment = CriterionAssessment(
            criterion_id=binding.criterion_id,
            requirement_id=binding.requirement_id,
            candidate_status=CandidateStatus.IDENTIFIED,
            documentation_status=DocumentationStatus.COMPATIBLE,
            constraint_status=ConsolidatedConstraintStatus.NO_CONDITIONS,
            assessment_status=CriterionAssessmentStatus.READY_FOR_SCORING,
            human_review_required=False,
            normative_gaps=(),
            warnings=(),
            assisted_proposals=(),
            traceability=AssessmentTraceability(
                normative_origin=normative_origin,
                factual_origin=origin,
                documents=(),
                conditions=(),
                verifications=(),
                facts=(FactUsed(
                    key="measurement",
                    value=fact.quantity,
                    source=fact.aggregate_id,
                ),),
            ),
            assessment_summary="Enquadramento manual explícito.",
            source_evaluation=None,
        )
        interval = CanonicalTimeInterval(
            start=(
                None
                if fact.period_start is None
                else fact.period_start.isoformat()
            ),
            end=(
                None if fact.period_end is None else fact.period_end.isoformat()
            ),
            start_source_field="period_start",
            end_source_field="period_end",
        )
        documents = tuple(
            CanonicalDocument(
                document_id=item.document_id,
                document_identity=item.document_id,
                name=item.name,
            )
            for item in evidence.documents
        )
        activity = CanonicalActivity(
            activity_id=fact.aggregate_id,
            description=fact.description,
        )
        exercise = CanonicalFunctionalExercise(
            functional_exercise_id=fact.aggregate_id,
            exercise_type_code=fact.fact_type,
            role="manual",
        )
        canonical_facts = self._canonical_facts(
            fact, binding, rule
        )
        return NormativeExecutionFact(
            execution_fact_id=fact.aggregate_id,
            criterion_id=binding.criterion_id,
            requirement_id=binding.requirement_id,
            execution_rule_id=binding.execution_rule_id,
            assessment_state="ready_for_scoring",
            computability_level=rule["computability_level"],
            measurement=Measurement(
                amount=fact.quantity,
                unit=fact.unit,
                measurement_type=definition.required_measurement.value,
                source=fact.aggregate_id,
                validation_state=MeasurementValidationState.AVAILABLE,
            ),
            quantified_occurrences=(ExecutionOccurrence(
                occurrence_id=f"{fact.aggregate_id}:occurrence",
                criterion_id=binding.criterion_id,
                origin=origin,
                quantity=fact.quantity,
                unit=fact.unit,
                period=interval,
                related_documents=documents,
                related_activity=activity,
                related_functional_exercise=exercise,
                overlap_status=OverlapStatus.NONE,
                explanation="Ocorrência informada pelo usuário.",
            ),),
            canonical_facts=canonical_facts,
            canonical_documents=documents,
            canonical_activities=(activity,),
            canonical_functional_exercises=(exercise,),
            canonical_time_interval=interval,
            selected_variant=None,
            possible_variants=(),
            variant_fact_available=False,
            variant_review_required=False,
            overlap_candidates=(),
            unresolved_items=(),
            human_review_required=False,
            normative_traceability=ExecutionNormativeTraceability(
                execution_rule_id=binding.execution_rule_id,
                criterion_id=binding.criterion_id,
                requirement_id=binding.requirement_id,
                article_reference=rule["article_reference"],
                annex_reference=rule["annex_reference"],
                scoring_table=rule["scoring_table"],
                assessment_origin=normative_origin,
            ),
            factual_traceability=origin,
            explanation="Fato editorial projetado por Binding manual.",
            source_assessment=assessment,
        )

    @staticmethod
    def _canonical_facts(fact, binding, rule):
        trace = FactTraceability(
            source_object="platform_execution_fact",
            source_field="quantity",
            source_identity=fact.aggregate_id,
            normative_reference=binding.criterion_id,
        )
        values = {
            "period_start": fact.period_start.isoformat()
            if fact.period_start else None,
            "period_end": fact.period_end.isoformat()
            if fact.period_end else None,
        }
        result = []
        for key in rule["required_facts"]:
            value = values.get(key, fact.quantity)
            if value is None:
                continue
            try:
                fact_type = CanonicalFactType(key)
            except ValueError:
                fact_type = CanonicalFactType.CONSTRAINT_FACT
            result.append(CanonicalFact(
                fact_id=f"{fact.aggregate_id}:{key}",
                fact_type=fact_type,
                value=value,
                unit=fact.unit,
                source=fact.aggregate_id,
                confidence_origin=ConfidenceOrigin.DECLARED,
                traceability=trace,
            ))
        return tuple(result)

    @staticmethod
    def _create_process(project, evidences, facts, bindings):
        process = RSCProcess.create(
            process_id=project.aggregate_id,
            server=RSCServer(
                server_id=project.aggregate_id,
                name=project.name,
                functional_registration="não informado",
            ),
            institution=RSCInstitution(
                institution_id=project.application_id,
                name=project.application_id,
            ),
            intended_level=IntendedRSCLevel.RSC_I,
            process_date=date.today(),
        )
        evidence_by_fact = {
            fact.aggregate_id: fact.evidence_id for fact in facts
        }
        for evidence in evidences:
            codes = tuple(
                binding.criterion_id
                for binding in bindings.values()
                if evidence_by_fact[binding.execution_fact_id]
                == evidence.aggregate_id
            )
            process = process.add_evidence(RSCProcessEvidence(
                evidence_id=evidence.aggregate_id,
                document_id=(
                    evidence.documents[0].document_id
                    if evidence.documents else evidence.aggregate_id
                ),
                description=evidence.description or evidence.title,
                criterion_codes=tuple(dict.fromkeys(codes)),
                documents=tuple(
                    RSCProcessDocument(
                        document_id=document.document_id,
                        name=document.name,
                    )
                    for document in evidence.documents
                ),
            ))
        return process


def _rules_by_criterion(path: Path) -> dict[str, dict]:
    document = json.loads(path.read_text(encoding="utf-8"))
    return {
        item["criterion_id"]: item for item in document["rules"]
    }


__all__ = [
    "RSCExecutionError",
    "RSCExecutionResult",
    "RSCExecutionService",
]
