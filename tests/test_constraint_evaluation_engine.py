from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
import unittest

from applications.rsc.constraint_evaluation import (
    ConditionClassification,
    ConstraintAnalysisState,
    ConstraintEvaluationEngine,
    ConstraintEvaluationError,
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
    EvaluationFunctionalExercise,
    EvaluationProject,
)
from applications.rsc.evidence_qualification import (
    QualifiedCriterionCandidate,
    QualifiedCriterionCandidateCollection,
)


@dataclass(frozen=True)
class ConditionRecord:
    id: str
    criterion_id: str
    classification: str
    description: str
    operation: str | None
    fact_key: str | None
    expected_value: object
    document_id: str = "BR-DEC-13048-2026"
    legal_reference: str = "Art. 5º"
    hierarchy: tuple[str, ...] = ("decree", "article:5")
    validation_questions: tuple[str, ...] = (
        "A conclusão preliminar está correta?",
    )


class NormativeModelStub:
    def __init__(self, conditions) -> None:
        self.conditions = conditions

    def conditions_of_criterion(self, criterion_id):
        return self.conditions


def source_candidate(index: int = 1) -> CriterionCandidate:
    activity = EvaluationActivity(
        activity_id=f"activity-{index}",
        description="Activity",
        state="lembrada",
        functional_assignment_evidence_ids=(),
        functional_exercise_ids=(),
    )
    exercise = EvaluationFunctionalExercise(
        id=f"exercise-{index}",
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
        functional_assignment_evidence_ids=(),
    )
    origin = NormativeOrigin(
        document_id="BR-DEC-13048-2026",
        legal_reference="Anexo I, item 1",
        hierarchy=("decree", "annex:I", "item:1"),
    )
    return CriterionCandidate(
        criterion_id=f"criterion-{index}",
        requirement_id="requirement-1",
        normative_origin=origin,
        activity=activity,
        functional_exercise=exercise,
        confidence=StructuralConfidence.EXPLICIT_CHAIN,
        technical_justification="Vínculo explícito.",
        factual_traceability=FactualTraceability(
            activity_id=activity.activity_id,
            functional_exercise_id=exercise.id,
            functional_assignment_evidence_id=f"assignment-{index}",
            evidence_id=f"evidence-{index}",
            document_id=f"document-{index}",
            document_identity=str(index) * 64,
            accepted_document_id=None,
        ),
    )


def qualified_candidate(index: int = 1) -> QualifiedCriterionCandidate:
    candidate = source_candidate(index)
    return QualifiedCriterionCandidate(
        source_candidate=candidate,
        presented_documents=(),
        accepted_documents=(),
        missing_documents=(),
        satisfied_categories=(),
        pending_categories=(),
        documentary_justification="Qualificação documental.",
        normative_traceability=candidate.normative_origin,
    )


def context(facts=()) -> EvaluationContext:
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
        activities=(),
        functional_exercises=(),
        functional_assignment_evidences=(),
        evidences=(),
        documents=(),
        metadata=MappingProxyType({
            "constraint_facts": tuple(
                MappingProxyType(dict(item)) for item in facts
            )
        }),
    )


def fact(
    condition_id: str,
    *,
    index: int = 1,
    value=...,
    applicable: bool | None = None,
    **extra,
):
    result = {
        "condition_id": condition_id,
        "criterion_id": f"criterion-{index}",
        "activity_id": f"activity-{index}",
        "functional_exercise_id": f"exercise-{index}",
        "fact_key": "fact",
        "source": "EvaluationContext.metadata",
        **extra,
    }
    if value is not ...:
        result["value"] = value
    if applicable is not None:
        result["applicable"] = applicable
    return result


def condition(
    condition_id: str,
    classification: ConditionClassification,
    *,
    operation: str | None = None,
    expected=True,
) -> ConditionRecord:
    return ConditionRecord(
        id=condition_id,
        criterion_id="criterion-1",
        classification=classification.value,
        description=f"Condition {condition_id}",
        operation=operation,
        fact_key="fact",
        expected_value=expected,
    )


class ConstraintEvaluationEngineTests(unittest.TestCase):
    def evaluate(self, conditions, facts=(), candidates=None):
        source = QualifiedCriterionCandidateCollection(
            tuple(candidates or (qualified_candidate(),))
        )
        return ConstraintEvaluationEngine(
            context(facts),
            NormativeModelStub(conditions),
        ).evaluate(source)

    def test_structured_condition_verified(self):
        conditions = (
            condition(
                "condition-1",
                ConditionClassification.STRUCTURED,
                operation="equals",
            ),
        )

        result = self.evaluate(
            conditions,
            (fact("condition-1", value=True),),
        ).candidates[0].verifications[0]

        self.assertIs(result.state, ConstraintAnalysisState.VERIFIED)
        self.assertFalse(result.human_review_required)
        self.assertEqual(result.facts_used[0].value, True)

    def test_structured_condition_not_verified(self):
        conditions = (
            condition(
                "condition-1",
                ConditionClassification.STRUCTURED,
                operation="equals",
            ),
        )

        result = self.evaluate(
            conditions,
            (fact("condition-1", value=False),),
        ).candidates[0].verifications[0]

        self.assertIs(
            result.state,
            ConstraintAnalysisState.NOT_VERIFIED,
        )
        self.assertNotIn("critério", result.explanation.lower())

    def test_condition_explicitly_not_applicable(self):
        conditions = (
            condition(
                "condition-1",
                ConditionClassification.STRUCTURED,
                operation="equals",
            ),
        )

        result = self.evaluate(
            conditions,
            (fact("condition-1", applicable=False),),
        ).candidates[0].verifications[0]

        self.assertIs(
            result.state,
            ConstraintAnalysisState.NOT_APPLICABLE,
        )

    def test_assisted_condition_produces_non_definitive_proposal(self):
        conditions = (
            condition(
                "condition-1",
                ConditionClassification.ASSISTED,
            ),
        )
        assisted_fact = fact(
            "condition-1",
            value="documented",
            preliminary_conclusion="Há elementos para revisão.",
            favorable_facts=("Documento presente.",),
            contrary_facts=("Período não confirmado.",),
            missing_information=("Confirmar período.",),
        )

        result = self.evaluate(
            conditions,
            (assisted_fact,),
        ).candidates[0].verifications[0]

        self.assertIs(
            result.state,
            ConstraintAnalysisState.REVIEW_RECOMMENDED,
        )
        self.assertTrue(result.human_review_required)
        self.assertFalse(result.proposal.definitive)
        self.assertEqual(
            result.proposal.validation_questions,
            ("A conclusão preliminar está correta?",),
        )

    def test_assisted_condition_without_information_is_insufficient(self):
        conditions = (
            condition(
                "condition-1",
                ConditionClassification.ASSISTED,
            ),
        )

        result = self.evaluate(
            conditions,
        ).candidates[0].verifications[0]

        self.assertIs(
            result.state,
            ConstraintAnalysisState.INSUFFICIENT_INFORMATION,
        )
        self.assertTrue(result.human_review_required)
        self.assertIsNone(result.proposal)

    def test_human_only_condition_requires_human_decision(self):
        conditions = (
            condition(
                "condition-1",
                ConditionClassification.HUMAN_ONLY,
            ),
        )

        result = self.evaluate(
            conditions,
        ).candidates[0].verifications[0]

        self.assertIs(
            result.state,
            ConstraintAnalysisState.HUMAN_DECISION_REQUIRED,
        )
        self.assertTrue(result.human_review_required)

    def test_missing_normative_conditions_is_visible_gap(self):
        result = self.evaluate(
            None,
        ).candidates[0]

        self.assertIs(
            result.verifications[0].state,
            ConstraintAnalysisState.NORMATIVE_GAP,
        )
        self.assertIn("Lacuna normativa explícita.", result.alerts)

    def test_unknown_structured_operation_is_normative_gap(self):
        conditions = (
            condition(
                "condition-1",
                ConditionClassification.STRUCTURED,
                operation="subjective_match",
            ),
        )

        result = self.evaluate(
            conditions,
            (fact("condition-1", value=True),),
        ).candidates[0].verifications[0]

        self.assertIs(
            result.state,
            ConstraintAnalysisState.NORMATIVE_GAP,
        )

    def test_multiple_conditions_preserve_order_and_traceability(self):
        conditions = (
            condition(
                "condition-1",
                ConditionClassification.STRUCTURED,
                operation="is_true",
            ),
            condition(
                "condition-2",
                ConditionClassification.HUMAN_ONLY,
            ),
        )

        result = self.evaluate(
            conditions,
            (fact("condition-1", value=True),),
        ).candidates[0]

        self.assertEqual(
            tuple(
                item.condition.condition_id
                for item in result.verifications
            ),
            ("condition-1", "condition-2"),
        )
        self.assertEqual(
            result.normative_devices[0].document_id,
            "BR-DEC-13048-2026",
        )
        self.assertIs(
            result.qualified_candidate.source_candidate,
            result.source_candidate,
        )

    def test_duplicate_conditions_are_rejected(self):
        duplicate = condition(
            "condition-1",
            ConditionClassification.HUMAN_ONLY,
        )

        with self.assertRaises(ConstraintEvaluationError):
            self.evaluate((duplicate, duplicate))

    def test_candidate_order_determinism_and_repeatability(self):
        first = qualified_candidate(1)
        second = qualified_candidate(2)
        model = NormativeModelStub(None)
        source = QualifiedCriterionCandidateCollection((second, first))
        engine = ConstraintEvaluationEngine(context(), model)

        initial = engine.evaluate(source)
        repeated = engine.evaluate(source)

        self.assertEqual(initial, repeated)
        self.assertEqual(
            tuple(
                item.source_candidate.criterion_id for item in initial
            ),
            ("criterion-2", "criterion-1"),
        )


if __name__ == "__main__":
    unittest.main()
