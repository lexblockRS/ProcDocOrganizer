from __future__ import annotations

from dataclasses import replace
from decimal import Decimal
import unittest

from applications.rsc.execution_contracts import (
    CriterionExecutionContractCollection,
    ExecutionComputability,
)
from applications.rsc.scoring_kernel import (
    CriterionScoringKernel,
    ScoringState,
)
from test_scoring_kernel import contracts


def event_contract(amount, *, normative_value=None):
    collection = contracts(
        "DEC13048-ANX-II-ITEM-07",
        "DEC13048-ART3-II",
        "event_count",
        amount,
    )
    if normative_value is None:
        return collection
    source = collection.contracts[0]
    return CriterionExecutionContractCollection((
        replace(
            source,
            resolved_normative_value=replace(
                source.resolved_normative_value,
                value=normative_value,
            ),
        ),
    ))


class PerEventScoringTests(unittest.TestCase):
    def setUp(self) -> None:
        self.kernel = CriterionScoringKernel()

    def score(self, amount, *, normative_value=None):
        return self.kernel.score(
            event_contract(amount, normative_value=normative_value)
        ).scores[0]

    def test_zero_events_execute_as_zero(self):
        score = self.score(0)

        self.assertEqual(score.scoring_state, ScoringState.EXECUTED)
        self.assertEqual(score.normalized_quantity, Decimal("0"))
        self.assertEqual(score.calculated_score, Decimal("0"))

    def test_one_event_uses_measurement_amount(self):
        score = self.score(1, normative_value=Decimal("2"))

        self.assertEqual(score.normalized_quantity, Decimal("1"))
        self.assertEqual(score.calculated_score, Decimal("2"))

    def test_multiple_events_use_decimal_multiplication(self):
        score = self.score(5, normative_value=Decimal("2.25"))

        self.assertEqual(score.normalized_quantity, Decimal("5"))
        self.assertEqual(score.normative_operand, Decimal("2.25"))
        self.assertEqual(score.calculated_score, Decimal("11.25"))
        self.assertEqual(score.arithmetic_operation, "MULTIPLY")

    def test_decimal_quantity_is_preserved_without_float(self):
        score = self.score(
            Decimal("2.5"),
            normative_value=Decimal("1.2"),
        )

        self.assertIsInstance(score.normalized_quantity, Decimal)
        self.assertIsInstance(score.calculated_score, Decimal)
        self.assertEqual(score.calculated_score, Decimal("3.00"))

    def test_missing_amount_is_blocked_upstream(self):
        score = self.score(None)

        self.assertEqual(score.scoring_state, ScoringState.BLOCKED)
        self.assertIsNone(score.calculated_score)

    def test_non_executable_contract_is_blocked(self):
        source = event_contract(2)
        contract = source.contracts[0]
        blocked = CriterionExecutionContractCollection((
            replace(
                contract,
                execution_computability=ExecutionComputability.BLOCKED,
            ),
        ))

        score = self.kernel.score(blocked).scores[0]

        self.assertEqual(score.scoring_state, ScoringState.BLOCKED)
        self.assertIsNone(score.calculated_score)

    def test_explanation_records_rule_quantity_operand_formula_and_result(self):
        score = self.score(5, normative_value=Decimal("2"))

        self.assertIn("regra PER_EVENT", score.explanation)
        self.assertIn("Measurement COUNT", score.explanation)
        self.assertIn("quantidade de eventos 5", score.explanation)
        self.assertIn("valor normativo por evento 2", score.explanation)
        self.assertIn("5 × 2 = 10", score.explanation)

    def test_execution_is_repeatable_and_deterministic(self):
        source = event_contract(3, normative_value=Decimal("1.5"))

        first = self.kernel.score(source)
        second = self.kernel.score(source)

        self.assertEqual(first, second)
        self.assertEqual(first.scores[0].score_id, second.scores[0].score_id)


if __name__ == "__main__":
    unittest.main()
