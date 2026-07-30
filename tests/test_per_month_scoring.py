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
from applications.rsc.requirement_scoring import RequirementScoreAggregator
from applications.rsc.scoring_kernel import (
    CriterionScoreCollection,
    CriterionScoringKernel,
    ScoringState,
    decompose_temporal_period,
)
from applications.rsc.temporal_attention import TemporalAttentionAnalyzer
from test_per_year_scoring import score as score_temporal
from test_per_year_scoring import year_contract
from test_scoring_kernel import contracts


def month_contract(
    start: str | None,
    end: str | None,
    *,
    normative_value: Decimal = Decimal("2"),
    temporal_rule: str = "PER_MONTH",
    overlap: OverlapStatus = OverlapStatus.NONE,
    computability: ExecutionComputability = (
        ExecutionComputability.EXECUTABLE
    ),
    validation_state: ValidationState = ValidationState.READY,
    multiple_occurrences: bool = False,
):
    source = contracts(
        "DEC13048-ANX-VI-ITEM-19",
        "DEC13048-ART3-VI",
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
    occurrences = (occurrence,)
    if multiple_occurrences:
        occurrences += (replace(
            occurrence,
            occurrence_id="second-occurrence",
        ),)
    return replace(
        source,
        temporal_rule=temporal_rule,
        occurrences=occurrences,
        execution_computability=computability,
        validation_state=validation_state,
        resolved_normative_value=replace(
            source.resolved_normative_value,
            value=normative_value,
        ),
    )


def month_score(
    start: str | None,
    end: str | None,
    **kwargs,
):
    contract = month_contract(start, end, **kwargs)
    return CriterionScoringKernel().score(
        CriterionExecutionContractCollection((contract,))
    ).scores[0]


class CanonicalCompletedMonthsTests(unittest.TestCase):
    def test_completed_months_is_public_and_canonical(self):
        cases = (
            ("2020-01-01", "2020-06-30", 5),
            ("2020-01-01", "2021-06-01", 17),
            ("2020-01-01", "2021-07-01", 18),
            ("2020-01-01", "2022-04-11", 27),
        )
        for start, end, expected in cases:
            with self.subTest(start=start, end=end):
                decomposition = decompose_temporal_period(start, end)
                self.assertEqual(decomposition.completed_months, expected)
                self.assertEqual(
                    decomposition.completed_months,
                    decomposition.complete_years * 12
                    + decomposition.residual_months,
                )


class PerMonthScoringTests(unittest.TestCase):
    def test_official_reference_cases(self):
        cases = (
            ("2020-01-01", "2020-01-01", 0),
            ("2020-01-01", "2020-01-31", 0),
            ("2020-01-01", "2020-02-01", 1),
            ("2020-01-01", "2020-02-29", 1),
            ("2020-01-01", "2020-03-01", 2),
            ("2020-01-15", "2020-02-14", 0),
            ("2020-01-15", "2020-02-15", 1),
            ("2020-01-15", "2020-02-16", 1),
            ("2020-01-01", "2021-06-01", 17),
            ("2020-01-01", "2021-07-01", 18),
        )
        for start, end, expected_months in cases:
            with self.subTest(start=start, end=end):
                result = month_score(start, end)
                quantity = Decimal(expected_months)
                self.assertEqual(result.scoring_state, ScoringState.EXECUTED)
                self.assertEqual(result.normalized_quantity, quantity)
                self.assertEqual(
                    result.calculated_score,
                    quantity * Decimal("2"),
                )

    def test_month_end_and_leap_calendar_cases(self):
        cases = (
            ("2020-01-31", "2020-02-29", 1),
            ("2019-01-31", "2019-02-28", 1),
            ("2020-02-29", "2021-02-28", 12),
            ("2020-01-30", "2020-02-29", 1),
            ("2020-03-31", "2020-04-30", 1),
            ("2020-12-15", "2021-01-15", 1),
        )
        for start, end, expected_months in cases:
            with self.subTest(start=start, end=end):
                result = month_score(start, end)
                self.assertEqual(
                    result.normalized_quantity,
                    Decimal(expected_months),
                )

    def test_month_boundaries_discard_residual_days(self):
        cases = (
            ("2020-01-15", "2020-02-14", 0),
            ("2020-01-15", "2020-02-15", 1),
            ("2020-01-15", "2020-02-16", 1),
            ("2020-01-15", "2020-04-14", 2),
            ("2020-01-15", "2020-04-15", 3),
        )
        for start, end, expected_months in cases:
            with self.subTest(start=start, end=end):
                self.assertEqual(
                    month_score(start, end).normalized_quantity,
                    Decimal(expected_months),
                )

    def test_explanation_uses_canonical_decomposition(self):
        result = month_score("2021-03-15", "2022-09-20")

        self.assertIn("anos completos 1", result.explanation)
        self.assertIn("meses residuais 6", result.explanation)
        self.assertIn("dias residuais 5", result.explanation)
        self.assertIn("meses completos totais 18", result.explanation)
        self.assertIn("regra aplicada PER_MONTH", result.explanation)
        self.assertIn("valor normativo por mês 2", result.explanation)
        self.assertIn("18 × 2 = 36", result.explanation)

    def test_missing_invalid_open_and_inverted_periods_are_blocked(self):
        cases = (
            (None, None),
            ("2020-01-01", None),
            (None, "2020-02-01"),
            ("invalid", "2020-02-01"),
            ("2020-02-01", "2020-01-01"),
        )
        for start, end in cases:
            with self.subTest(start=start, end=end):
                result = month_score(start, end)
                self.assertEqual(result.scoring_state, ScoringState.BLOCKED)
                self.assertIsNone(result.calculated_score)

    def test_multiple_occurrences_and_overlap_are_blocked(self):
        multiple = month_score(
            "2020-01-01",
            "2020-02-01",
            multiple_occurrences=True,
        )
        overlap = month_score(
            "2020-01-01",
            "2020-02-01",
            overlap=OverlapStatus.POSSIBLE,
        )

        self.assertEqual(multiple.scoring_state, ScoringState.BLOCKED)
        self.assertEqual(overlap.scoring_state, ScoringState.BLOCKED)

    def test_blocked_and_not_executable_contracts_do_not_calculate(self):
        cases = (
            (
                ExecutionComputability.BLOCKED,
                ValidationState.BLOCKED,
            ),
            (
                ExecutionComputability.NOT_EXECUTABLE,
                ValidationState.HUMAN_REVIEW_REQUIRED,
            ),
        )
        for computability, validation_state in cases:
            with self.subTest(computability=computability):
                result = month_score(
                    "2020-01-01",
                    "2020-02-01",
                    computability=computability,
                    validation_state=validation_state,
                )
                self.assertIsNone(result.calculated_score)
                self.assertNotEqual(
                    result.scoring_state,
                    ScoringState.EXECUTED,
                )

    def test_decimal_values_zero_and_fractional_remain_exact(self):
        for value, expected in (
            (Decimal("0"), Decimal("0")),
            (Decimal("2.50"), Decimal("7.50")),
            (Decimal("0.125"), Decimal("0.375")),
        ):
            with self.subTest(value=value):
                result = month_score(
                    "2020-01-01",
                    "2020-04-01",
                    normative_value=value,
                )
                self.assertEqual(result.calculated_score, expected)
                self.assertIsInstance(result.normalized_quantity, Decimal)
                self.assertIsInstance(result.normative_operand, Decimal)
                self.assertIsInstance(result.calculated_score, Decimal)

    def test_real_pipeline_contract_executes_without_early_quantity(self):
        source = contracts(
            "DEC13048-ANX-VI-ITEM-19",
            "DEC13048-ART3-VI",
            "unused",
            None,
        )

        result = CriterionScoringKernel().score(source).scores[0]

        self.assertEqual(result.scoring_state, ScoringState.EXECUTED)
        self.assertIsNone(source.contracts[0].measurement.amount)
        self.assertEqual(result.normalized_quantity, Decimal(23))
        self.assertEqual(result.calculated_score, Decimal(23))
        self.assertIs(
            result.source_contract.source_execution_fact,
            source.contracts[0].source_execution_fact,
        )
        self.assertIs(
            result.source_contract.source_validation,
            source.contracts[0].source_validation,
        )

    def test_result_is_deterministic_repeatable_and_immutable(self):
        contract = month_contract("2020-01-01", "2021-07-01")
        source = CriterionExecutionContractCollection((contract,))
        kernel = CriterionScoringKernel()

        first = kernel.score(source)
        second = kernel.score(source)

        self.assertEqual(first, second)
        self.assertIs(first.scores[0].source_contract, contract)
        with self.assertRaises(FrozenInstanceError):
            first.scores[0].normalized_quantity = Decimal(999)
        decomposition = decompose_temporal_period(
            "2020-01-01",
            "2021-07-01",
        )
        with self.assertRaises(FrozenInstanceError):
            decomposition.complete_years = 999

    def test_existing_rules_aggregator_and_attention_remain_compatible(self):
        year = score_temporal(year_contract(
            "2020-01-01",
            "2021-07-01",
            temporal_rule="NONE",
        ))
        fraction = score_temporal(year_contract(
            "2020-01-01",
            "2021-07-01",
            temporal_rule="FRACTION_ABOVE_SIX_MONTHS",
        ))
        event = CriterionScoringKernel().score(contracts(
            "DEC13048-ANX-II-ITEM-07",
            "DEC13048-ART3-II",
            "event_count",
            2,
        )).scores[0]
        publication = CriterionScoringKernel().score(contracts(
            "DEC13048-ANX-VI-ITEM-10",
            "DEC13048-ART3-VI",
            "publication_count",
            2,
        )).scores[0]
        monthly = month_score("2020-01-01", "2020-03-01")
        collection = CriterionScoreCollection((
            event,
            publication,
            monthly,
        ))

        self.assertEqual(year.normalized_quantity, Decimal(1))
        self.assertEqual(fraction.normalized_quantity, Decimal(2))
        self.assertEqual(event.scoring_state, ScoringState.EXECUTED)
        self.assertEqual(publication.scoring_state, ScoringState.EXECUTED)
        self.assertGreater(
            len(RequirementScoreAggregator().aggregate(collection)),
            0,
        )
        self.assertIsInstance(
            TemporalAttentionAnalyzer().analyze(collection).attentions,
            tuple,
        )


if __name__ == "__main__":
    unittest.main()
