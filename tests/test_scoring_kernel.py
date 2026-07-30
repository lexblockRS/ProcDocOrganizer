from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
from decimal import Decimal
from pathlib import Path
import unittest

from applications.rsc.constraint_evaluation import FactUsed
from applications.rsc.criterion_assessment import CriterionAssessmentCollection
from applications.rsc.execution_contracts import (
    CriterionExecutionContractCollection,
    ExecutionComputability,
    ExecutionContractResolver,
    LegalComputability,
)
from applications.rsc.execution_compatibility import (
    ExecutionCompatibilityEvaluator,
)
from applications.rsc.execution_facts import ExecutionFactBuilder
from applications.rsc.execution_validation import ExecutionValidator
from applications.rsc.scoring_kernel import (
    CriterionScoringKernel,
    ScoringState,
)
from test_execution_facts import assessment, context


ROOT = Path(__file__).resolve().parents[1]
RULES = ROOT / "docs" / "normative" / "criterion_execution_rules.json"
MANIFEST = ROOT / "docs" / "normative" / "execution_rules_manifest.json"
CRITERIA = ROOT / "docs" / "normative" / "decree_criteria.json"


def contracts(
    criterion_id: str,
    requirement_id: str,
    fact_name: str,
    value: int | Decimal | None,
):
    ctx = context()
    facts_used = (
        ()
        if value is None
        else (FactUsed(key=fact_name, value=value, source="test"),)
    )
    source = CriterionAssessmentCollection((
        assessment(
            ctx,
            criterion_id,
            requirement_id,
            facts=facts_used,
        ),
    ))
    facts = ExecutionFactBuilder.from_files(RULES, MANIFEST).build(
        source,
        ctx,
    )
    validations = ExecutionValidator.from_files(
        RULES,
        MANIFEST,
    ).validate(facts)
    compatibilities = ExecutionCompatibilityEvaluator.from_file(
        RULES
    ).evaluate(facts, validations)
    return ExecutionContractResolver.from_files(
        RULES,
        MANIFEST,
        CRITERIA,
    ).resolve(facts, validations, compatibilities)


class CriterionScoringKernelTests(unittest.TestCase):
    def setUp(self) -> None:
        self.kernel = CriterionScoringKernel()

    def score_event(self, value: int | Decimal | None):
        source = contracts(
            "DEC13048-ANX-II-ITEM-07",
            "DEC13048-ART3-II",
            "event_count",
            value,
        )
        return self.kernel.score(source).scores[0]

    def test_executes_per_event_with_decimal_multiplication(self):
        score = self.score_event(Decimal("2.5"))

        self.assertEqual(score.scoring_state, ScoringState.EXECUTED)
        self.assertEqual(score.normalized_quantity, Decimal("2.5"))
        self.assertIsInstance(score.normative_operand, Decimal)
        self.assertEqual(
            score.calculated_score,
            score.normalized_quantity * score.normative_operand,
        )
        self.assertEqual(score.arithmetic_operation, "MULTIPLY")

    def test_executes_per_publication(self):
        source = contracts(
            "DEC13048-ANX-VI-ITEM-10",
            "DEC13048-ART3-VI",
            "publication_count",
            3,
        )

        score = self.kernel.score(source).scores[0]

        self.assertEqual(score.scoring_state, ScoringState.EXECUTED)
        self.assertEqual(score.normalized_quantity, Decimal(3))
        self.assertEqual(
            score.calculated_score,
            Decimal(3) * score.normative_operand,
        )

    def test_zero_is_executed_and_preserved(self):
        score = self.score_event(0)

        self.assertEqual(score.scoring_state, ScoringState.EXECUTED)
        self.assertEqual(score.calculated_score, Decimal(0))

    def test_missing_quantity_produces_blocked_score_not_none(self):
        score = self.score_event(None)

        self.assertEqual(score.scoring_state, ScoringState.BLOCKED)
        self.assertIsNone(score.normalized_quantity)
        self.assertIsNone(score.calculated_score)
        self.assertIn("bloqueado", score.explanation)

    def test_non_executable_contract_does_not_calculate(self):
        source = contracts(
            "DEC13048-ANX-II-ITEM-07",
            "DEC13048-ART3-II",
            "event_count",
            1,
        )
        contract = source.contracts[0]
        source = CriterionExecutionContractCollection((
            replace(
                contract,
                execution_computability=(
                    ExecutionComputability.NOT_EXECUTABLE
                ),
            ),
        ))
        score = self.kernel.score(source).scores[0]

        self.assertEqual(score.scoring_state, ScoringState.BLOCKED)
        self.assertIsNone(score.calculated_score)

    def test_missing_normative_value_is_not_executed(self):
        source = contracts(
            "DEC13048-ANX-II-ITEM-07",
            "DEC13048-ART3-II",
            "event_count",
            1,
        )
        contract = source.contracts[0]
        source = CriterionExecutionContractCollection((
            replace(
                contract,
                resolved_normative_value=replace(
                    contract.resolved_normative_value,
                    value=None,
                ),
            ),
        ))

        score = self.kernel.score(source).scores[0]

        self.assertEqual(score.scoring_state, ScoringState.NOT_EXECUTED)
        self.assertIsNone(score.normative_operand)
        self.assertIsNone(score.calculated_score)
        self.assertIn("valor normativo ausente", score.explanation)

    def test_dual_computability_allows_prepared_arithmetic(self):
        source = contracts(
            "DEC13048-ANX-II-ITEM-07",
            "DEC13048-ART3-II",
            "event_count",
            2,
        )
        contract = source.contracts[0]

        self.assertEqual(
            contract.legal_computability,
            LegalComputability.TEXT_DEPENDENT,
        )
        self.assertEqual(
            contract.execution_computability,
            ExecutionComputability.EXECUTABLE,
        )
        self.assertEqual(
            self.kernel.score(source).scores[0].scoring_state,
            ScoringState.EXECUTED,
        )

    def test_unsupported_rule_is_not_executed(self):
        source = contracts(
            "DEC13048-ANX-I-ITEM-02",
            "DEC13048-ART3-I",
            "designation_count",
            1,
        )

        score = self.kernel.score(source).scores[0]

        self.assertEqual(score.scoring_state, ScoringState.NOT_EXECUTED)
        self.assertIn("não suportada", score.explanation)

    def test_result_preserves_contract_and_normative_traceability(self):
        source = contracts(
            "DEC13048-ANX-II-ITEM-07",
            "DEC13048-ART3-II",
            "event_count",
            2,
        )
        contract = source.contracts[0]

        score = self.kernel.score(source).scores[0]

        self.assertIs(score.source_contract, contract)
        self.assertEqual(score.contract_id, contract.contract_id)
        self.assertEqual(
            score.execution_trace.normative_value_traceability,
            contract.resolved_normative_value.traceability,
        )
        self.assertIn("×", score.execution_trace.formula)

    def test_scores_are_immutable(self):
        score = self.score_event(1)

        with self.assertRaises(FrozenInstanceError):
            score.calculated_score = Decimal(999)

    def test_repeated_execution_is_deterministic(self):
        source = contracts(
            "DEC13048-ANX-II-ITEM-07",
            "DEC13048-ART3-II",
            "event_count",
            2,
        )

        first = self.kernel.score(source)
        second = self.kernel.score(source)

        self.assertEqual(first, second)
        self.assertEqual(first.scores[0].score_id, second.scores[0].score_id)
        self.assertEqual(len(first), len(source))


if __name__ == "__main__":
    unittest.main()
