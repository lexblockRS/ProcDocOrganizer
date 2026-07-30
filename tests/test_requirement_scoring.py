from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
from decimal import Decimal
import unittest

from applications.rsc.requirement_scoring import RequirementScoreAggregator
from applications.rsc.scoring_kernel import (
    CriterionScoreCollection,
    CriterionScoringKernel,
    ScoringState,
)
from test_scoring_kernel import contracts


def executed_score(
    *,
    criterion_id: str = "DEC13048-ANX-II-ITEM-07",
    value: int | Decimal = 2,
):
    source = contracts(
        criterion_id,
        "DEC13048-ART3-II",
        "event_count",
        value,
    )
    return CriterionScoringKernel().score(source).scores[0]


class RequirementScoreAggregatorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.aggregator = RequirementScoreAggregator()

    def test_empty_collection_produces_no_requirement(self):
        result = self.aggregator.aggregate(CriterionScoreCollection())

        self.assertEqual(len(result), 0)

    def test_single_criterion_produces_one_requirement_score(self):
        criterion = executed_score()

        result = self.aggregator.aggregate(
            CriterionScoreCollection((criterion,))
        )

        self.assertEqual(len(result), 1)
        requirement = result.requirement_scores[0]
        self.assertEqual(requirement.requirement_id, criterion.requirement_id)
        self.assertEqual(requirement.criterion_scores, (criterion,))
        self.assertEqual(requirement.executed_scores, (criterion,))
        self.assertEqual(requirement.total_score, criterion.calculated_score)

    def test_multiple_criteria_are_summed_as_decimal(self):
        first = executed_score(value=Decimal("2.5"))
        second = executed_score(
            criterion_id="DEC13048-ANX-II-ITEM-11",
            value=3,
        )

        result = self.aggregator.aggregate(
            CriterionScoreCollection((first, second))
        ).requirement_scores[0]

        self.assertEqual(
            result.total_score,
            first.calculated_score + second.calculated_score,
        )
        self.assertIsInstance(result.total_score, Decimal)
        self.assertEqual(result.executed_scores, (first, second))

    def test_blocked_score_is_preserved_but_not_summed(self):
        executed = executed_score()
        blocked = replace(
            executed,
            score_id="blocked-score",
            contract_id="blocked-contract",
            criterion_id="blocked-criterion",
            scoring_state=ScoringState.BLOCKED,
            calculated_score=None,
            arithmetic_operation=None,
        )

        result = self.aggregator.aggregate(
            CriterionScoreCollection((executed, blocked))
        ).requirement_scores[0]

        self.assertEqual(result.total_score, executed.calculated_score)
        self.assertEqual(result.blocked_scores, (blocked,))
        self.assertIn(blocked, result.criterion_scores)
        self.assertIn(blocked.score_id, result.aggregation_trace.blocked_score_ids)

    def test_textual_and_not_executed_scores_are_ignored(self):
        executed = executed_score()
        textual = replace(
            executed,
            score_id="textual-score",
            contract_id="textual-contract",
            criterion_id="textual-criterion",
            scoring_state=ScoringState.TEXT_DEPENDENT,
            calculated_score=None,
            arithmetic_operation=None,
        )
        not_executed = replace(
            executed,
            score_id="not-executed-score",
            contract_id="not-executed-contract",
            criterion_id="not-executed-criterion",
            scoring_state=ScoringState.NOT_EXECUTED,
            calculated_score=None,
            arithmetic_operation=None,
        )

        result = self.aggregator.aggregate(
            CriterionScoreCollection((executed, textual, not_executed))
        ).requirement_scores[0]

        self.assertEqual(result.total_score, executed.calculated_score)
        self.assertEqual(result.ignored_scores, (textual, not_executed))
        self.assertIn("TEXT_DEPENDENT", result.explanation)
        self.assertIn("NOT_EXECUTED", result.explanation)

    def test_different_requirements_produce_distinct_scores_in_input_order(self):
        first = executed_score()
        second = replace(
            first,
            score_id="other-score",
            contract_id="other-contract",
            criterion_id="other-criterion",
            requirement_id="other-requirement",
        )

        result = self.aggregator.aggregate(
            CriterionScoreCollection((first, second))
        )

        self.assertEqual(
            tuple(item.requirement_id for item in result),
            (first.requirement_id, "other-requirement"),
        )

    def test_trace_preserves_every_score_and_participant(self):
        first = executed_score()
        blocked = replace(
            first,
            score_id="blocked-score",
            contract_id="blocked-contract",
            criterion_id="blocked-criterion",
            scoring_state=ScoringState.BLOCKED,
            calculated_score=None,
        )

        result = self.aggregator.aggregate(
            CriterionScoreCollection((first, blocked))
        ).requirement_scores[0]

        self.assertIs(result.criterion_scores[0], first)
        self.assertIs(result.criterion_scores[1], blocked)
        self.assertEqual(
            result.aggregation_trace.criterion_score_ids,
            (first.score_id, blocked.score_id),
        )
        self.assertEqual(
            result.aggregation_trace.participating_criterion_ids,
            (first.criterion_id,),
        )

    def test_aggregation_is_deterministic_and_repeatable(self):
        scores = CriterionScoreCollection((
            executed_score(),
            executed_score(
                criterion_id="DEC13048-ANX-II-ITEM-11",
                value=1,
            ),
        ))

        first = self.aggregator.aggregate(scores)
        second = self.aggregator.aggregate(scores)

        self.assertEqual(first, second)
        self.assertEqual(
            first.requirement_scores[0].requirement_score_id,
            second.requirement_scores[0].requirement_score_id,
        )

    def test_requirement_score_is_immutable(self):
        requirement = self.aggregator.aggregate(
            CriterionScoreCollection((executed_score(),))
        ).requirement_scores[0]

        with self.assertRaises(FrozenInstanceError):
            requirement.total_score = Decimal(999)


if __name__ == "__main__":
    unittest.main()
