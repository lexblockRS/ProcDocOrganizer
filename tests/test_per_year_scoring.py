from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
from decimal import Decimal
import unittest

from applications.rsc.execution_contracts import (
    CriterionExecutionContractCollection,
    ExecutionComputability,
)
from applications.rsc.execution_facts import (
    CanonicalTimeInterval,
    OverlapStatus,
)
from applications.rsc.execution_validation import ValidationState
from applications.rsc.scoring_kernel import (
    CriterionScoringKernel,
    ScoringState,
)
from test_scoring_kernel import contracts


def year_contract(
    start: str | None,
    end: str | None,
    *,
    temporal_rule: str = "NONE",
    overlap: OverlapStatus = OverlapStatus.NONE,
    computability: ExecutionComputability = (
        ExecutionComputability.EXECUTABLE
    ),
    validation_state: ValidationState = ValidationState.READY,
):
    source = contracts(
        "DEC13048-ANX-I-ITEM-01",
        "DEC13048-ART3-I",
        "unused",
        None,
    ).contracts[0]
    occurrence = replace(
        source.occurrences[0],
        period=CanonicalTimeInterval(
            start=start,
            end=end,
            start_source_field="start_date",
            end_source_field="end_date",
        ),
        overlap_status=overlap,
    )
    return replace(
        source,
        temporal_rule=temporal_rule,
        occurrences=(occurrence,),
        execution_computability=computability,
        validation_state=validation_state,
    )


def score(contract):
    return CriterionScoringKernel().score(
        CriterionExecutionContractCollection((contract,))
    ).scores[0]


class PerYearScoringTests(unittest.TestCase):
    def test_one_complete_year(self):
        result = score(year_contract("2020-01-15", "2021-01-15"))

        self.assertEqual(result.scoring_state, ScoringState.EXECUTED)
        self.assertEqual(result.normalized_quantity, Decimal(1))
        self.assertEqual(
            result.calculated_score,
            Decimal(1) * result.normative_operand,
        )
        self.assertIn("início 2020-01-15", result.explanation)
        self.assertIn("fim 2021-01-15", result.explanation)

    def test_two_complete_years_use_decimal(self):
        result = score(year_contract("2020-02-29", "2022-02-28"))

        self.assertEqual(result.normalized_quantity, Decimal(2))
        self.assertIsInstance(result.calculated_score, Decimal)
        self.assertEqual(
            result.calculated_score,
            Decimal(2) * result.normative_operand,
        )

    def test_incomplete_year_executes_as_zero(self):
        result = score(year_contract("2020-05-10", "2021-05-09"))

        self.assertEqual(result.scoring_state, ScoringState.EXECUTED)
        self.assertEqual(result.normalized_quantity, Decimal(0))
        self.assertEqual(result.calculated_score, Decimal(0))

    def test_inverted_dates_are_blocked(self):
        result = score(year_contract("2022-01-01", "2021-01-01"))

        self.assertEqual(result.scoring_state, ScoringState.BLOCKED)
        self.assertIsNone(result.calculated_score)
        self.assertIn("datas invertidas", result.explanation)

    def test_open_period_is_blocked(self):
        result = score(year_contract("2020-01-01", None))

        self.assertEqual(result.scoring_state, ScoringState.BLOCKED)
        self.assertIn("período aberto", result.explanation)

    def test_absent_dates_are_blocked(self):
        result = score(year_contract(None, None))

        self.assertEqual(result.scoring_state, ScoringState.BLOCKED)
        self.assertIn("data ausente", result.explanation)

    def test_unknown_fraction_rule_remains_blocked(self):
        result = score(year_contract(
            "2020-01-01",
            "2021-08-01",
            temporal_rule="UNSUPPORTED_FRACTION",
        ))

        self.assertEqual(result.scoring_state, ScoringState.BLOCKED)
        self.assertIn("fração", result.explanation)

    def test_overlap_is_blocked(self):
        result = score(year_contract(
            "2020-01-01",
            "2022-01-01",
            overlap=OverlapStatus.POSSIBLE,
        ))

        self.assertEqual(result.scoring_state, ScoringState.BLOCKED)
        self.assertIn("sobreposição", result.explanation)

    def test_non_executable_contract_remains_blocked(self):
        result = score(year_contract(
            "2020-01-01",
            "2021-01-01",
            computability=ExecutionComputability.BLOCKED,
            validation_state=ValidationState.BLOCKED,
        ))

        self.assertEqual(result.scoring_state, ScoringState.BLOCKED)
        self.assertIsNone(result.calculated_score)

    def test_textual_and_human_review_states_are_preserved(self):
        for validation_state, expected in (
            (ValidationState.TEXT_DEPENDENT, ScoringState.TEXT_DEPENDENT),
            (
                ValidationState.HUMAN_REVIEW_REQUIRED,
                ScoringState.HUMAN_REVIEW_REQUIRED,
            ),
        ):
            with self.subTest(validation_state=validation_state):
                result = score(year_contract(
                    "2020-01-01",
                    "2021-01-01",
                    computability=ExecutionComputability.NOT_EXECUTABLE,
                    validation_state=validation_state,
                ))
                self.assertEqual(result.scoring_state, expected)
                self.assertIsNone(result.calculated_score)

    def test_invalid_date_is_blocked(self):
        result = score(year_contract("2020-02-30", "2021-01-01"))

        self.assertEqual(result.scoring_state, ScoringState.BLOCKED)
        self.assertIn("inválida", result.explanation)

    def test_result_is_deterministic_and_immutable(self):
        contract = year_contract("2020-01-01", "2022-01-01")

        first = score(contract)
        second = score(contract)

        self.assertEqual(first, second)
        with self.assertRaises(FrozenInstanceError):
            first.normalized_quantity = Decimal(99)


if __name__ == "__main__":
    unittest.main()
