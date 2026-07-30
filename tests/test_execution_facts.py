from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
from pathlib import Path
from types import MappingProxyType
import unittest

from applications.rsc.constraint_evaluation import (
    ConstraintEvaluatedCandidate,
    FactUsed,
)
from applications.rsc.criterion_assessment import (
    AssessmentTraceability,
    CandidateStatus,
    ConsolidatedConstraintStatus,
    CriterionAssessment,
    CriterionAssessmentCollection,
    CriterionAssessmentStatus,
    DocumentationStatus,
)
from applications.rsc.criterion_candidates import (
    CriterionCandidate,
    FactualTraceability,
    NormativeOrigin,
    StructuralConfidence,
)
from applications.rsc.evaluation_context import (
    EvaluationActivity,
    EvaluationContext,
    EvaluationDocument,
    EvaluationEvidence,
    EvaluationFunctionalAssignmentEvidence,
    EvaluationFunctionalExercise,
    EvaluationProject,
)
from applications.rsc.evidence_qualification import (
    PresentedDocument,
    QualifiedCriterionCandidate,
)
from applications.rsc.execution_facts import (
    CanonicalFactType,
    ConfidenceOrigin,
    DuplicateExecutionFactError,
    ExecutionFactBuilder,
    ExecutionFactCollection,
    MeasurementValidationState,
    OverlapStatus,
    UnknownExecutionRuleError,
)


ROOT = Path(__file__).resolve().parents[1]
RULES = ROOT / "docs" / "normative" / "criterion_execution_rules.json"
MANIFEST = ROOT / "docs" / "normative" / "execution_rules_manifest.json"


def context(
    *,
    role: str = "titular",
    end_date: str | None = "2021-12-31",
) -> EvaluationContext:
    identity = "a" * 64
    return EvaluationContext(
        project=EvaluationProject(
            project_name="Project",
            project_path="project.pdop",
            created_at="2020-01-01T00:00:00",
            last_opened_at="2020-01-01T00:00:00",
            application="rsc",
            format_version=1,
            database="project.sqlite",
        ),
        activities=(
            EvaluationActivity(
                activity_id="activity-1",
                description="Activity",
                state="consolidated",
                functional_assignment_evidence_ids=("assignment-1",),
                functional_exercise_ids=("exercise-1",),
            ),
        ),
        functional_exercises=(
            EvaluationFunctionalExercise(
                id="exercise-1",
                person_id="person-1",
                exercise_type_code="explicit",
                exercise_type_label="Explicit",
                role=role,
                organization="Institution",
                unit=None,
                administrative_reference=None,
                start_date="2020-01-01",
                end_date=end_date,
                status="active",
                functional_assignment_evidence_ids=("assignment-1",),
            ),
        ),
        functional_assignment_evidences=(
            EvaluationFunctionalAssignmentEvidence(
                id="assignment-1",
                person_id="person-1",
                source_evidence_id="evidence-1",
                exercise_type_code="explicit",
                exercise_type_label="Explicit",
                role=role,
                organization="Institution",
                start_date="2020-01-01",
                end_date=end_date,
                unit=None,
                administrative_reference=None,
                status="linked",
            ),
        ),
        evidences=(
            EvaluationEvidence(
                id="evidence-1",
                document_identity=identity,
                page_number=1,
                title="Evidence",
                source_snippet="Snippet",
                user_notes=None,
                category=None,
                start_date=None,
                end_date=None,
                created_at="2020-01-01T00:00:00",
                updated_at="2020-01-01T00:00:00",
            ),
        ),
        documents=(
            EvaluationDocument(
                id="document-1",
                document_identity=identity,
                name="Document",
                relative_path="document.pdf",
                imported_at="2020-01-01T00:00:00",
                pages=1,
                status="available",
                document_type="pdf",
                processed_at=None,
                processing_status="ready",
                original_filename="document.pdf",
                stored_filename="document.pdf",
                file_size=1,
                extension=".pdf",
                mime_type="application/pdf",
                created_at="2020-01-01T00:00:00",
                updated_at="2020-01-01T00:00:00",
            ),
        ),
        metadata=MappingProxyType({}),
    )


def assessment(
    ctx: EvaluationContext,
    criterion_id: str = "DEC13048-ANX-I-ITEM-01",
    requirement_id: str = "DEC13048-ART3-I",
    *,
    facts: tuple[FactUsed, ...] = (),
    human_review_required: bool = False,
) -> CriterionAssessment:
    activity = ctx.activities[0]
    exercise = ctx.functional_exercises[0]
    document = ctx.documents[0]
    origin = NormativeOrigin(
        document_id="BR-DEC-13048-2026",
        legal_reference="Anexo",
        hierarchy=("decree", "annex"),
    )
    factual = FactualTraceability(
        activity_id=activity.activity_id,
        functional_exercise_id=exercise.id,
        functional_assignment_evidence_id="assignment-1",
        evidence_id="evidence-1",
        document_id=document.id,
        document_identity=document.document_identity,
        accepted_document_id=None,
    )
    candidate = CriterionCandidate(
        criterion_id=criterion_id,
        requirement_id=requirement_id,
        normative_origin=origin,
        activity=activity,
        functional_exercise=exercise,
        confidence=StructuralConfidence.EXPLICIT_CHAIN,
        technical_justification="Explicit.",
        factual_traceability=factual,
    )
    presented = PresentedDocument(
        document_id=document.id,
        document_identity=document.document_identity,
        name=document.name,
    )
    qualified = QualifiedCriterionCandidate(
        source_candidate=candidate,
        presented_documents=(presented,),
        accepted_documents=(),
        missing_documents=(),
        satisfied_categories=(),
        pending_categories=(),
        documentary_justification="Documented.",
        normative_traceability=origin,
    )
    evaluated = ConstraintEvaluatedCandidate(
        qualified_candidate=qualified,
        identified_conditions=(),
        verifications=(),
        facts_used=facts,
        normative_devices=(),
        pending_items=(),
        alerts=(),
        human_review_required=human_review_required,
        framing_proposals=(),
    )
    traceability = AssessmentTraceability(
        normative_origin=origin,
        factual_origin=factual,
        documents=(presented,),
        conditions=(),
        verifications=(),
        facts=facts,
    )
    return CriterionAssessment(
        criterion_id=criterion_id,
        requirement_id=requirement_id,
        candidate_status=CandidateStatus.IDENTIFIED,
        documentation_status=DocumentationStatus.COMPATIBLE,
        constraint_status=ConsolidatedConstraintStatus.COMPLETE,
        assessment_status=CriterionAssessmentStatus.READY_FOR_SCORING,
        human_review_required=human_review_required,
        normative_gaps=(),
        warnings=(),
        assisted_proposals=(),
        traceability=traceability,
        assessment_summary="Ready.",
        source_evaluation=evaluated,
    )


class ExecutionFactBuilderTests(unittest.TestCase):
    def setUp(self) -> None:
        self.builder = ExecutionFactBuilder.from_files(RULES, MANIFEST)

    def test_normalizes_dates_role_and_normative_unit_reversibly(self):
        ctx = context()

        result = self.builder.build(
            CriterionAssessmentCollection((assessment(ctx),)),
            ctx,
        )

        fact = result.facts[0]
        by_type = {item.fact_type: item for item in fact.canonical_facts}
        self.assertEqual(
            by_type[CanonicalFactType.PERIOD_START].value,
            "2020-01-01",
        )
        self.assertEqual(
            by_type[CanonicalFactType.PERIOD_START]
            .traceability.source_field,
            "start_date",
        )
        self.assertEqual(
            by_type[CanonicalFactType.EXECUTION_ROLE].value,
            "titular",
        )
        self.assertEqual(
            by_type[CanonicalFactType.MEASUREMENT_UNIT]
            .confidence_origin,
            ConfidenceOrigin.DECLARED,
        )
        self.assertEqual(
            fact.canonical_time_interval.start_source_field,
            "start_date",
        )

    def test_preserves_explicit_quantity_without_multiplication(self):
        ctx = context()
        source = assessment(
            ctx,
            criterion_id="DEC13048-ANX-I-ITEM-02",
            requirement_id="DEC13048-ART3-I",
            facts=(
                FactUsed(
                    key="designation_count",
                    value=3,
                    source="user-declared",
                ),
            ),
        )

        fact = self.builder.build(
            CriterionAssessmentCollection((source,)),
            ctx,
        ).facts[0]

        self.assertEqual(fact.measurement.amount, 3)
        self.assertEqual(
            fact.measurement.validation_state,
            MeasurementValidationState.AVAILABLE,
        )
        self.assertEqual(fact.quantified_occurrences[0].quantity, 3)
        self.assertNotIn("designation_count", fact.unresolved_items)

    def test_missing_required_fact_remains_unresolved(self):
        ctx = context()
        source = assessment(
            ctx,
            criterion_id="DEC13048-ANX-I-ITEM-02",
            requirement_id="DEC13048-ART3-I",
        )

        fact = self.builder.build(
            CriterionAssessmentCollection((source,)),
            ctx,
        ).facts[0]

        self.assertIsNone(fact.measurement.amount)
        self.assertIn("designation_count", fact.unresolved_items)
        self.assertTrue(fact.human_review_required)

    def test_variant_is_transported_and_never_selected(self):
        ctx = context(role="substituto")
        source = assessment(
            ctx,
            criterion_id="DEC13048-ANX-V-ITEM-01",
            requirement_id="DEC13048-ART3-V",
        )

        fact = self.builder.build(
            CriterionAssessmentCollection((source,)),
            ctx,
        ).facts[0]

        self.assertEqual(fact.possible_variants, ("titular", "substituto"))
        self.assertTrue(fact.variant_fact_available)
        self.assertTrue(fact.variant_review_required)
        self.assertIsNone(fact.selected_variant)

    def test_possible_overlap_is_registered_without_resolution(self):
        ctx = context()
        first = assessment(ctx)
        second = assessment(
            ctx,
            criterion_id="DEC13048-ANX-II-ITEM-01",
            requirement_id="DEC13048-ART3-II",
        )

        result = self.builder.build(
            CriterionAssessmentCollection((first, second)),
            ctx,
        )

        self.assertEqual(len(result), 2)
        for fact in result:
            self.assertEqual(len(fact.overlap_candidates), 1)
            self.assertEqual(
                fact.quantified_occurrences[0].overlap_status,
                OverlapStatus.POSSIBLE,
            )

    def test_multiple_assessments_preserve_order_and_occurrences(self):
        ctx = context()
        sources = CriterionAssessmentCollection((
            assessment(ctx),
            assessment(
                ctx,
                criterion_id="DEC13048-ANX-II-ITEM-01",
                requirement_id="DEC13048-ART3-II",
            ),
        ))

        result = self.builder.build(sources, ctx)

        self.assertEqual(
            tuple(item.criterion_id for item in result),
            (
                "DEC13048-ANX-I-ITEM-01",
                "DEC13048-ANX-II-ITEM-01",
            ),
        )
        self.assertTrue(all(
            len(item.quantified_occurrences) == 1 for item in result
        ))

    def test_incomplete_assessment_preserves_review_and_explanation(self):
        ctx = context(end_date=None)
        source = replace(
            assessment(ctx, human_review_required=True),
            normative_gaps=("gap-1",),
            warnings=("warning-1",),
        )

        fact = self.builder.build(
            CriterionAssessmentCollection((source,)),
            ctx,
        ).facts[0]

        self.assertTrue(fact.human_review_required)
        self.assertIn("period_end", fact.unresolved_items)
        self.assertIn("gap-1", fact.unresolved_items)
        self.assertIn("warning-1", fact.unresolved_items)
        self.assertIn("fatos ausentes: period_end", fact.explanation)

    def test_traceability_reaches_rule_assessment_and_document(self):
        ctx = context()
        source = assessment(ctx)

        fact = self.builder.build(
            CriterionAssessmentCollection((source,)),
            ctx,
        ).facts[0]

        self.assertEqual(
            fact.normative_traceability.execution_rule_id,
            "DEC13048-RULE-ANX-I-ITEM-01",
        )
        self.assertIs(fact.source_assessment, source)
        self.assertEqual(
            fact.factual_traceability.document_id,
            fact.canonical_documents[0].document_id,
        )

    def test_models_and_nested_collections_are_immutable(self):
        ctx = context()
        fact = self.builder.build(
            CriterionAssessmentCollection((assessment(ctx),)),
            ctx,
        ).facts[0]

        with self.assertRaises(FrozenInstanceError):
            fact.selected_variant = "titular"
        self.assertIsInstance(fact.canonical_facts, tuple)
        self.assertIsInstance(fact.quantified_occurrences, tuple)

    def test_duplicate_collection_identity_is_rejected(self):
        ctx = context()
        fact = self.builder.build(
            CriterionAssessmentCollection((assessment(ctx),)),
            ctx,
        ).facts[0]

        with self.assertRaises(DuplicateExecutionFactError):
            ExecutionFactCollection((fact, fact))

    def test_repeated_builds_are_equal_and_deterministic(self):
        ctx = context()
        sources = CriterionAssessmentCollection((assessment(ctx),))

        first = self.builder.build(sources, ctx)
        second = self.builder.build(sources, ctx)

        self.assertEqual(first, second)
        self.assertEqual(
            first.facts[0].execution_fact_id,
            second.facts[0].execution_fact_id,
        )

    def test_unknown_assessment_rule_is_rejected(self):
        ctx = context()
        source = assessment(ctx)
        source = replace(source, criterion_id="unknown")

        with self.assertRaises(UnknownExecutionRuleError):
            self.builder.build(
                CriterionAssessmentCollection((source,)),
                ctx,
            )


if __name__ == "__main__":
    unittest.main()
