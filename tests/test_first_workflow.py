from __future__ import annotations

from datetime import date
from decimal import Decimal
from pathlib import Path
import unittest

from applications import RscApplication
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
    ExecutionFact,
    ExecutionFactCollection,
    ExecutionNormativeTraceability,
    ExecutionOccurrence,
    FactTraceability,
    Measurement,
    MeasurementValidationState,
    OverlapStatus,
)
from applications.rsc.execution_validation import (
    ExecutionValidator,
    ValidationState,
)
from applications.rsc.requirement_scoring import RequirementScoreAggregator
from applications.rsc.rsc_process import (
    IntendedRSCLevel,
    RSCInstitution,
    RSCProcess,
    RSCProcessEvidence,
    RSCProcessResult,
    RSCProcessStage,
    RSCServer,
)
from applications.rsc.scoring_kernel import (
    CriterionScoringKernel,
    ScoringState,
)
from applications.rsc.temporal_attention import TemporalAttentionCollection
from applications.rsc.constraint_evaluation import FactUsed
from platform_sdk import Project
from test_execution_facts import assessment, context


ROOT = Path(__file__).resolve().parents[1]
RULES = ROOT / "docs" / "normative" / "criterion_execution_rules.json"
MANIFEST = ROOT / "docs" / "normative" / "execution_rules_manifest.json"
CRITERIA = ROOT / "docs" / "normative" / "decree_criteria.json"

CRITERION_ID = "DEC13048-ANX-II-ITEM-07"
REQUIREMENT_ID = "DEC13048-ART3-II"
RULE_ID = "DEC13048-RULE-ANX-II-ITEM-07"


class FirstEndToEndWorkflowTests(unittest.TestCase):
    def test_complete_manual_rsc_workflow(self):
        # 1–2. Project genérico associado à Application RSC.
        project = Project.create(
            name="Primeiro fluxo RSC",
            application_id=RscApplication.descriptor.application_id,
        )
        project_snapshot = project.rename("Primeiro fluxo RSC validado")

        # 3. Evidence manual preservada como referência do processo.
        evidence = RSCProcessEvidence(
            evidence_id="evidence-1",
            document_id="document-1",
            description="Ata de participação como avaliador.",
            criterion_codes=(CRITERION_ID,),
        )
        rsc_process = RSCProcess.create(
            process_id="rsc-process-1",
            server=RSCServer(
                server_id="server-1",
                name="Servidor Exemplo",
                functional_registration="12345",
            ),
            institution=RSCInstitution(
                institution_id="institution-1",
                name="Instituição Exemplo",
            ),
            intended_level=IntendedRSCLevel.RSC_II,
            process_date=date(2026, 7, 30),
        ).add_evidence(evidence)
        evidence_snapshot = rsc_process

        # 4. ExecutionFact criado manualmente, com origem documental completa.
        source_assessment = assessment(
            context(),
            criterion_id=CRITERION_ID,
            requirement_id=REQUIREMENT_ID,
            facts=(
                FactUsed(
                    key="event_count",
                    value=3,
                    source="manual-workflow",
                ),
            ),
        )
        factual_origin = source_assessment.traceability.factual_origin
        document = CanonicalDocument(
            document_id="document-1",
            document_identity=factual_origin.document_identity,
            name="ata.pdf",
        )
        activity = CanonicalActivity(
            activity_id=factual_origin.activity_id,
            description="Participação em banca avaliadora.",
        )
        exercise = CanonicalFunctionalExercise(
            functional_exercise_id=(
                factual_origin.functional_exercise_id
            ),
            exercise_type_code="event_evaluation",
            role="avaliador",
        )
        interval = CanonicalTimeInterval(
            start=None,
            end=None,
            start_source_field="not_applicable",
            end_source_field="not_applicable",
        )
        fact_trace = FactTraceability(
            source_object="manual_input",
            source_field="event_count",
            source_identity=evidence.evidence_id,
            normative_reference=CRITERION_ID,
        )
        fact = ExecutionFact(
            execution_fact_id="execution-fact-1",
            criterion_id=CRITERION_ID,
            requirement_id=REQUIREMENT_ID,
            execution_rule_id=RULE_ID,
            assessment_state="ready_for_scoring",
            computability_level="TEXT_DEPENDENT",
            measurement=Measurement(
                amount=3,
                unit="Por evento",
                measurement_type="COUNT",
                source="manual-workflow",
                validation_state=MeasurementValidationState.AVAILABLE,
            ),
            quantified_occurrences=(
                ExecutionOccurrence(
                    occurrence_id="occurrence-1",
                    criterion_id=CRITERION_ID,
                    origin=factual_origin,
                    quantity=3,
                    unit="Por evento",
                    period=interval,
                    related_documents=(document,),
                    related_activity=activity,
                    related_functional_exercise=exercise,
                    overlap_status=OverlapStatus.NONE,
                    explanation="Três eventos informados manualmente.",
                ),
            ),
            canonical_facts=(
                CanonicalFact(
                    fact_id="fact-event-count",
                    fact_type=CanonicalFactType.EVENT_COUNT,
                    value=3,
                    unit="Por evento",
                    source="manual-workflow",
                    confidence_origin=ConfidenceOrigin.DECLARED,
                    traceability=fact_trace,
                ),
            ),
            canonical_documents=(document,),
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
                execution_rule_id=RULE_ID,
                criterion_id=CRITERION_ID,
                requirement_id=REQUIREMENT_ID,
                article_reference="DEC13048-ART-03",
                annex_reference="II",
                scoring_table="DEC13048-TABLE-ANEXO-II",
                assessment_origin=(
                    source_assessment.traceability.normative_origin
                ),
            ),
            factual_traceability=factual_origin,
            explanation="Fato quantitativo criado manualmente.",
            source_assessment=source_assessment,
        )
        facts = ExecutionFactCollection((fact,))

        # 5. Pipeline existente: Validation → Compatibility → contrato
        # → Kernel → Requirement aggregation.
        validations = ExecutionValidator.from_files(
            RULES,
            MANIFEST,
        ).validate(facts)
        compatibilities = ExecutionCompatibilityEvaluator.from_catalog(
            rsc_process.catalog
        ).evaluate(facts, validations)
        contracts = ExecutionContractResolver.from_files(
            RULES,
            MANIFEST,
            CRITERIA,
        ).resolve(facts, validations, compatibilities)
        criterion_scores = CriterionScoringKernel().score(contracts)
        requirement_scores = RequirementScoreAggregator().aggregate(
            criterion_scores
        )

        aggregated = (
            rsc_process.record_execution_facts(facts)
            .record_validations(validations)
            .record_compatibilities(compatibilities)
            .record_criterion_scores(criterion_scores)
            .record_requirement_scores(requirement_scores)
        )
        consolidated = aggregated.consolidate(RSCProcessResult(
            total_score=requirement_scores.requirement_scores[0].total_score,
            computable_criterion_ids=(CRITERION_ID,),
            non_computable_criterion_ids=(),
            pending_items=(),
            temporal_attentions=TemporalAttentionCollection(),
            used_evidence_ids=(evidence.evidence_id,),
            explanation="Resultado consolidado do primeiro fluxo completo.",
        ))

        # Resultado e requisito.
        score = consolidated.criterion_score(CRITERION_ID)
        requirement = consolidated.requirement_score(REQUIREMENT_ID)
        self.assertEqual(validations.validations[0].validation_state,
                         ValidationState.TEXT_DEPENDENT)
        self.assertEqual(
            compatibilities.compatibilities[0].compatibility_state,
            CompatibilityState.COMPATIBLE,
        )
        self.assertEqual(score.scoring_state, ScoringState.EXECUTED)
        self.assertEqual(score.normalized_quantity, Decimal(3))
        self.assertEqual(score.normative_operand, Decimal(3))
        self.assertEqual(score.calculated_score, Decimal(9))
        self.assertEqual(requirement.total_score, Decimal(9))
        self.assertEqual(consolidated.total_score, Decimal(9))
        self.assertEqual(
            consolidated.stage,
            RSCProcessStage.CONSOLIDATED,
        )

        # Rastreabilidade completa.
        self.assertIs(score.source_contract.source_execution_fact, fact)
        self.assertIs(
            score.source_contract.source_validation,
            validations.validations[0],
        )
        self.assertIs(
            score.source_contract.source_compatibility,
            compatibilities.compatibilities[0],
        )
        self.assertEqual(
            score.execution_trace.normative_value_traceability.criterion_id,
            CRITERION_ID,
        )
        self.assertEqual(
            fact.factual_traceability.evidence_id,
            evidence.evidence_id,
        )
        self.assertEqual(
            consolidated.result.used_evidence_ids,
            (evidence.evidence_id,),
        )

        # Snapshots e identidades dos dois Aggregates.
        self.assertTrue(project.same_project(project_snapshot))
        self.assertEqual(project.aggregate_id, project_snapshot.aggregate_id)
        self.assertEqual((project.revision, project_snapshot.revision), (0, 1))
        self.assertTrue(evidence_snapshot.same_process(consolidated))
        self.assertEqual(
            evidence_snapshot.aggregate_id,
            consolidated.aggregate_id,
        )
        self.assertLess(
            evidence_snapshot.revision,
            consolidated.revision,
        )
        self.assertEqual(
            evidence_snapshot.stage,
            RSCProcessStage.EVIDENCE,
        )


if __name__ == "__main__":
    unittest.main()
