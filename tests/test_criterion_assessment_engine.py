from __future__ import annotations

from dataclasses import dataclass, replace
from types import MappingProxyType
import unittest

from applications.rsc.constraint_evaluation import (
    AssistedFramingProposal,
    ConditionClassification,
    ConstraintAnalysisState,
    ConstraintEvaluatedCandidateCollection,
    ConstraintEvaluationEngine,
)
from applications.rsc.criterion_assessment import (
    ConsolidatedConstraintStatus,
    CriterionAssessmentCollection,
    CriterionAssessmentEngine,
    CriterionAssessmentStatus,
    DocumentationStatus,
)
from applications.rsc.criterion_candidates import CriterionCandidateEngine
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
    EvidenceQualificationEngine,
    MissingDocument,
    OfficialDocumentCategory,
    QualifiedCriterionCandidateCollection,
)


@dataclass(frozen=True)
class CriterionRecord:
    id: str
    requirement_id: str = "requirement-1"
    document_id: str = "BR-DEC-13048-2026"
    legal_reference: str = "Anexo I, item 1"
    hierarchy: tuple[str, ...] = ("decree", "annex:I", "item:1")


@dataclass(frozen=True)
class RequirementRecord:
    id: str


@dataclass(frozen=True)
class DocumentCategoryRecord:
    id: str
    legal_reference: str


@dataclass(frozen=True)
class ConditionRecord:
    id: str = "condition-1"
    criterion_id: str = "criterion-1"
    classification: str = ConditionClassification.STRUCTURED.value
    description: str = "Condição objetiva"
    operation: str | None = "is_true"
    fact_key: str | None = "confirmed"
    expected_value: object = True
    document_id: str = "BR-DEC-13048-2026"
    legal_reference: str = "Art. 5º"
    hierarchy: tuple[str, ...] = ("decree", "article:5")
    validation_questions: tuple[str, ...] = ()


class NormativeModelStub:
    def __init__(self, conditions=(ConditionRecord(),)) -> None:
        self.conditions = conditions

    def find_criterion(self, criterion_id):
        if criterion_id.startswith("criterion-"):
            return CriterionRecord(criterion_id)
        return None

    def find_requirement(self, requirement_id):
        if requirement_id == "requirement-1":
            return RequirementRecord(requirement_id)
        return None

    def find_accepted_document(self, document_type_id):
        if document_type_id == "document-category-1":
            return DocumentCategoryRecord(
                document_type_id,
                "Art. 4º, parágrafo único, inciso I",
            )
        return None

    def conditions_of_criterion(self, criterion_id):
        if self.conditions is None:
            return None
        return tuple(
            replace(item, criterion_id=criterion_id)
            for item in self.conditions
        )


def complete_context() -> EvaluationContext:
    document_identity = "a" * 64
    activity = EvaluationActivity(
        activity_id="activity-1",
        description="Activity",
        state="lembrada",
        functional_assignment_evidence_ids=("assignment-1",),
        functional_exercise_ids=("exercise-1",),
    )
    exercise = EvaluationFunctionalExercise(
        id="exercise-1",
        person_id="person-1",
        exercise_type_code="explicit",
        exercise_type_label="Explicit",
        role="Role",
        organization="Institution",
        unit=None,
        administrative_reference=None,
        start_date="2020-01-01",
        end_date=None,
        status="active",
        functional_assignment_evidence_ids=("assignment-1",),
    )
    assignment = EvaluationFunctionalAssignmentEvidence(
        id="assignment-1",
        person_id="person-1",
        source_evidence_id="evidence-1",
        exercise_type_code="explicit",
        exercise_type_label="Explicit",
        role="Role",
        organization="Institution",
        start_date="2020-01-01",
        end_date=None,
        unit=None,
        administrative_reference=None,
        status="linked",
    )
    evidence = EvaluationEvidence(
        id="evidence-1",
        document_identity=document_identity,
        page_number=1,
        title="Evidence",
        source_snippet="Source",
        user_notes=None,
        category=None,
        start_date=None,
        end_date=None,
        created_at="2026-07-01T10:00:00",
        updated_at="2026-07-01T10:00:00",
    )
    document = EvaluationDocument(
        id="document-1",
        document_identity=document_identity,
        name="Document",
        relative_path="documents/one.pdf",
        imported_at="2026-07-01T10:00:00",
        pages=1,
        status="imported",
        document_type="portaria",
        processed_at=None,
        processing_status="not_processed",
        original_filename="one.pdf",
        stored_filename="one.pdf",
        file_size=1,
        extension=".pdf",
        mime_type="application/pdf",
        created_at="2026-07-01T10:00:00",
        updated_at="2026-07-01T10:00:00",
    )
    link = MappingProxyType({
        "criterion_id": "criterion-1",
        "activity_id": "activity-1",
        "functional_exercise_id": "exercise-1",
        "functional_assignment_evidence_id": "assignment-1",
        "evidence_id": "evidence-1",
        "document_identity": document_identity,
        "accepted_document_id": "document-category-1",
    })
    fact = MappingProxyType({
        "condition_id": "condition-1",
        "criterion_id": "criterion-1",
        "activity_id": "activity-1",
        "functional_exercise_id": "exercise-1",
        "fact_key": "confirmed",
        "value": True,
        "source": "EvaluationContext.metadata",
    })
    return EvaluationContext(
        project=EvaluationProject(
            project_name="Project",
            project_path="C:/project",
            created_at="2026-07-01T09:00:00",
            last_opened_at="2026-07-01T09:00:00",
            application="rsc",
            format_version=1,
            database="database.db",
        ),
        activities=(activity,),
        functional_exercises=(exercise,),
        functional_assignment_evidences=(assignment,),
        evidences=(evidence,),
        documents=(document,),
        metadata=MappingProxyType({
            "criterion_candidate_links": (link,),
            "constraint_facts": (fact,),
        }),
    )


class CriterionAssessmentEngineTests(unittest.TestCase):
    def setUp(self) -> None:
        self.context = complete_context()
        self.model = NormativeModelStub()
        candidates = CriterionCandidateEngine(self.model).generate(
            self.context
        )
        qualified = EvidenceQualificationEngine(
            self.context,
            self.model,
        ).qualify(candidates)
        self.evaluated = ConstraintEvaluationEngine(
            self.context,
            self.model,
        ).evaluate(qualified).candidates[0]

    def assess(self, *evaluated, model=None):
        return CriterionAssessmentEngine(
            self.context,
            model or self.model,
        ).assess(
            ConstraintEvaluatedCandidateCollection(tuple(evaluated))
        )

    def test_complete_pipeline_reaches_ready_stage_without_approval(self):
        assessment = self.assess(self.evaluated).assessments[0]

        self.assertIs(
            assessment.assessment_status,
            CriterionAssessmentStatus.READY_FOR_SCORING,
        )
        self.assertIs(
            assessment.documentation_status,
            DocumentationStatus.COMPATIBLE,
        )
        self.assertIs(
            assessment.constraint_status,
            ConsolidatedConstraintStatus.COMPLETE,
        )
        self.assertIn(
            "não representa aprovação",
            assessment.assessment_summary,
        )

    def test_insufficient_documentation_is_consolidated(self):
        qualified = replace(
            self.evaluated.qualified_candidate,
            accepted_documents=(),
        )
        evaluated = replace(
            self.evaluated,
            qualified_candidate=qualified,
        )

        assessment = self.assess(evaluated).assessments[0]

        self.assertIs(
            assessment.documentation_status,
            DocumentationStatus.INSUFFICIENT,
        )
        self.assertIs(
            assessment.assessment_status,
            CriterionAssessmentStatus.INSUFFICIENT_INFORMATION,
        )

    def test_partial_documentation_preserves_pending_warning(self):
        category = OfficialDocumentCategory(
            "document-category-2",
            "Art. 4º, parágrafo único, inciso II",
        )
        qualified = replace(
            self.evaluated.qualified_candidate,
            missing_documents=(MissingDocument("missing", "b" * 64),),
            pending_categories=(category,),
        )
        evaluated = replace(
            self.evaluated,
            qualified_candidate=qualified,
        )

        assessment = self.assess(evaluated).assessments[0]

        self.assertIs(
            assessment.documentation_status,
            DocumentationStatus.PARTIAL,
        )
        self.assertEqual(len(assessment.warnings), 2)

    def test_human_review_is_consolidated(self):
        verification = replace(
            self.evaluated.verifications[0],
            state=ConstraintAnalysisState.HUMAN_DECISION_REQUIRED,
            human_review_required=True,
            alerts=("Decisão humana obrigatória.",),
        )
        evaluated = replace(
            self.evaluated,
            verifications=(verification,),
            alerts=("Decisão humana obrigatória.",),
            human_review_required=True,
        )

        assessment = self.assess(evaluated).assessments[0]

        self.assertIs(
            assessment.assessment_status,
            CriterionAssessmentStatus.REVIEW_REQUIRED,
        )
        self.assertTrue(assessment.human_review_required)

    def test_assisted_proposal_is_preserved_without_becoming_decision(self):
        proposal = AssistedFramingProposal(
            preliminary_conclusion="Proposta para conferência.",
            favorable_facts=("Documento presente.",),
            contrary_facts=(),
            missing_information=("Validar conteúdo.",),
            normative_reference="Art. 5º",
            validation_questions=("A proposta é adequada?",),
            review_justification="Revisão humana necessária.",
        )
        evaluated = replace(
            self.evaluated,
            framing_proposals=(proposal,),
            human_review_required=True,
        )

        assessment = self.assess(evaluated).assessments[0]

        self.assertEqual(assessment.assisted_proposals, (proposal,))
        self.assertFalse(assessment.assisted_proposals[0].definitive)
        self.assertTrue(assessment.human_review_required)

    def test_normative_gap_has_highest_precedence(self):
        verification = replace(
            self.evaluated.verifications[0],
            state=ConstraintAnalysisState.NORMATIVE_GAP,
            human_review_required=True,
            alerts=("Lacuna normativa explícita.",),
        )
        evaluated = replace(
            self.evaluated,
            verifications=(verification,),
            alerts=("Lacuna normativa explícita.",),
            human_review_required=True,
        )

        assessment = self.assess(evaluated).assessments[0]

        self.assertIs(
            assessment.assessment_status,
            CriterionAssessmentStatus.NORMATIVE_GAP,
        )
        self.assertEqual(
            assessment.normative_gaps,
            ("condition-1",),
        )

    def test_all_not_applicable_conditions_produce_not_applicable(self):
        verification = replace(
            self.evaluated.verifications[0],
            state=ConstraintAnalysisState.NOT_APPLICABLE,
            facts_used=(),
        )
        evaluated = replace(
            self.evaluated,
            verifications=(verification,),
            facts_used=(),
        )

        assessment = self.assess(evaluated).assessments[0]

        self.assertIs(
            assessment.assessment_status,
            CriterionAssessmentStatus.NOT_APPLICABLE,
        )

    def test_multiple_conditions_alerts_and_facts_are_not_discarded(self):
        first = self.evaluated.verifications[0]
        second_condition = replace(
            first.condition,
            condition_id="condition-2",
        )
        second = replace(
            first,
            condition=second_condition,
            state=ConstraintAnalysisState.HUMAN_DECISION_REQUIRED,
            alerts=("Segundo alerta.",),
            human_review_required=True,
        )
        evaluated = replace(
            self.evaluated,
            identified_conditions=(first.condition, second_condition),
            verifications=(first, second),
            alerts=("Primeiro alerta.", "Segundo alerta."),
            human_review_required=True,
        )

        assessment = self.assess(evaluated).assessments[0]

        self.assertEqual(len(assessment.traceability.conditions), 2)
        self.assertEqual(len(assessment.traceability.verifications), 2)
        self.assertEqual(
            assessment.warnings,
            ("Primeiro alerta.", "Segundo alerta."),
        )
        self.assertIs(assessment.source_evaluation, evaluated)

    def test_assessment_is_deterministic_and_repeatable(self):
        engine = CriterionAssessmentEngine(self.context, self.model)
        source = ConstraintEvaluatedCandidateCollection((self.evaluated,))

        self.assertEqual(engine.assess(source), engine.assess(source))

    def test_collection_preserves_order(self):
        first = self.evaluated
        source_candidate = replace(
            first.source_candidate,
            criterion_id="criterion-2",
        )
        qualified = replace(
            first.qualified_candidate,
            source_candidate=source_candidate,
        )
        second = replace(
            first,
            qualified_candidate=qualified,
        )

        result = self.assess(second, first)

        self.assertEqual(
            tuple(item.criterion_id for item in result),
            ("criterion-2", "criterion-1"),
        )

    def test_assessment_collection_rejects_duplicates(self):
        assessment = self.assess(self.evaluated).assessments[0]

        with self.assertRaises(ValueError):
            CriterionAssessmentCollection(
                (assessment, assessment)
            )


if __name__ == "__main__":
    unittest.main()
