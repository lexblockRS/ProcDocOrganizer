from __future__ import annotations

from dataclasses import FrozenInstanceError
from decimal import Decimal
import unittest

from applications.rsc.execution_contracts import ExecutionComputability
from applications.rsc.execution_validation import ValidationState
from applications.rsc.scoring_kernel import ScoringState
from test_per_year_scoring import score, year_contract


FRACTION_RULE = "FRACTION_ABOVE_SIX_MONTHS"


def fraction_score(start: str, end: str):
    return score(year_contract(
        start,
        end,
        temporal_rule=FRACTION_RULE,
    ))


class FractionAboveSixMonthsScoringTests(unittest.TestCase):
    def test_exactly_six_months_rounds_up(self):
        result = fraction_score("2020-01-15", "2020-07-15")

        self.assertEqual(result.scoring_state, ScoringState.EXECUTED)
        self.assertEqual(result.normalized_quantity, Decimal(1))
        self.assertIn("meses residuais 6", result.explanation)
        self.assertIn("fração acrescentou um ano", result.explanation)

    def test_five_months_and_twenty_nine_days_does_not_round(self):
        result = fraction_score("2020-01-01", "2020-06-30")

        self.assertEqual(result.normalized_quantity, Decimal(0))
        self.assertIn("meses residuais 5", result.explanation)
        self.assertIn("dias residuais 29", result.explanation)
        self.assertIn("fração não alterou os anos", result.explanation)

    def test_six_months_and_one_day_rounds_up(self):
        result = fraction_score("2020-01-15", "2020-07-16")

        self.assertEqual(result.normalized_quantity, Decimal(1))
        self.assertIn("meses residuais 6", result.explanation)
        self.assertIn("dias residuais 1", result.explanation)

    def test_seven_months_rounds_up(self):
        result = fraction_score("2020-01-01", "2020-08-01")

        self.assertEqual(result.normalized_quantity, Decimal(1))
        self.assertIn("meses residuais 7", result.explanation)

    def test_eleven_months_rounds_up(self):
        result = fraction_score("2020-01-01", "2020-12-01")

        self.assertEqual(result.normalized_quantity, Decimal(1))
        self.assertIn("meses residuais 11", result.explanation)

    def test_one_year_and_six_months_becomes_two_years(self):
        result = fraction_score("2020-01-01", "2021-07-01")

        self.assertEqual(result.normalized_quantity, Decimal(2))
        self.assertIn("anos completos 1", result.explanation)
        self.assertIn("anos considerados 2", result.explanation)

    def test_one_year_and_five_months_remains_one_year(self):
        result = fraction_score("2020-01-01", "2021-06-01")

        self.assertEqual(result.normalized_quantity, Decimal(1))
        self.assertIn("anos completos 1", result.explanation)
        self.assertIn("meses residuais 5", result.explanation)

    def test_two_years_and_six_months_becomes_three_years(self):
        result = fraction_score("2020-01-01", "2022-07-01")

        self.assertEqual(result.normalized_quantity, Decimal(3))
        self.assertIn("anos completos 2", result.explanation)
        self.assertIn("meses residuais 6", result.explanation)

    def test_leap_year_uses_calendar_months(self):
        result = fraction_score("2019-09-01", "2020-03-01")

        self.assertEqual(result.normalized_quantity, Decimal(1))
        self.assertIn("meses residuais 6", result.explanation)

    def test_starting_on_february_29_uses_clamped_calendar_dates(self):
        result = fraction_score("2020-02-29", "2020-08-29")

        self.assertEqual(result.normalized_quantity, Decimal(1))
        self.assertIn("meses residuais 6", result.explanation)

    def test_zero_complete_years_can_round_to_one(self):
        result = fraction_score("2022-02-01", "2022-08-01")

        self.assertIn("anos completos 0", result.explanation)
        self.assertEqual(result.normalized_quantity, Decimal(1))

    def test_blocked_contract_does_not_apply_fraction(self):
        contract = year_contract(
            "2020-01-01",
            "2020-07-01",
            temporal_rule=FRACTION_RULE,
            computability=ExecutionComputability.BLOCKED,
            validation_state=ValidationState.BLOCKED,
        )

        result = score(contract)

        self.assertEqual(result.scoring_state, ScoringState.BLOCKED)
        self.assertIsNone(result.calculated_score)

    def test_per_year_continues_to_ignore_residual_fraction(self):
        result = score(year_contract(
            "2020-01-01",
            "2021-07-01",
            temporal_rule="NONE",
        ))

        self.assertEqual(result.normalized_quantity, Decimal(1))

    def test_decimal_determinism_repeatability_and_immutability(self):
        contract = year_contract(
            "2020-01-01",
            "2021-07-01",
            temporal_rule=FRACTION_RULE,
        )

        first = score(contract)
        second = score(contract)

        self.assertEqual(first, second)
        self.assertIsInstance(first.normalized_quantity, Decimal)
        self.assertIsInstance(first.calculated_score, Decimal)
        with self.assertRaises(FrozenInstanceError):
            first.calculated_score = Decimal(999)


if __name__ == "__main__":
    unittest.main()
