from __future__ import annotations

from dataclasses import FrozenInstanceError
import unittest

from applications.rsc.scoring_kernel import CriterionScoreCollection
from applications.rsc.temporal_attention import (
    TemporalAttentionAnalyzer,
    TemporalAttentionCode,
    TemporalAttentionSeverity,
)
from test_per_year_scoring import score, year_contract


def analyzed(start: str, end: str):
    scored = score(year_contract(
        start,
        end,
        temporal_rule="FRACTION_ABOVE_SIX_MONTHS",
    ))
    collection = TemporalAttentionAnalyzer().analyze(
        CriterionScoreCollection((scored,))
    )
    return scored, collection


class TemporalAttentionAnalyzerTests(unittest.TestCase):
    def test_exact_six_months_produces_limit_attention(self):
        scored, result = analyzed("2020-01-01", "2020-07-01")

        codes = tuple(item.code for item in result.for_score(scored.score_id))

        self.assertIn(TemporalAttentionCode.EXACT_SIX_MONTH_LIMIT, codes)
        attention = next(
            item
            for item in result
            if item.code is TemporalAttentionCode.EXACT_SIX_MONTH_LIMIT
        )
        self.assertEqual(
            attention.severity,
            TemporalAttentionSeverity.WARNING,
        )
        self.assertIn("exatamente", attention.message)

    def test_five_months_and_twenty_seven_days_warns_below_limit(self):
        _, result = analyzed("2020-01-01", "2020-06-28")

        self.assertIn(
            TemporalAttentionCode.JUST_BELOW_SIX_MONTH_LIMIT,
            tuple(item.code for item in result),
        )

    def test_six_months_and_one_day_warns_above_limit(self):
        _, result = analyzed("2020-01-01", "2020-07-02")

        self.assertIn(
            TemporalAttentionCode.JUST_ABOVE_SIX_MONTH_LIMIT,
            tuple(item.code for item in result),
        )

    def test_seven_complete_months_has_no_margin_attention(self):
        _, result = analyzed("2020-01-01", "2020-08-01")
        margin_codes = {
            TemporalAttentionCode.JUST_BELOW_SIX_MONTH_LIMIT,
            TemporalAttentionCode.JUST_ABOVE_SIX_MONTH_LIMIT,
        }

        self.assertFalse(
            margin_codes & {item.code for item in result}
        )

    def test_february_29_produces_leap_day_attention(self):
        _, result = analyzed("2020-02-29", "2021-02-28")

        self.assertIn(
            TemporalAttentionCode.LEAP_DAY_INVOLVED,
            tuple(item.code for item in result),
        )

    def test_exact_half_year_and_anniversary_are_landmarks(self):
        for start, end in (
            ("2020-01-01", "2020-07-01"),
            ("2020-01-01", "2021-01-01"),
        ):
            with self.subTest(start=start, end=end):
                _, result = analyzed(start, end)
                self.assertIn(
                    TemporalAttentionCode.EXACT_TEMPORAL_LANDMARK,
                    tuple(item.code for item in result),
                )

    def test_non_temporal_score_has_no_attention(self):
        from test_scoring_kernel import contracts
        from applications.rsc.scoring_kernel import CriterionScoringKernel

        scored = CriterionScoringKernel().score(contracts(
            "DEC13048-ANX-II-ITEM-07",
            "DEC13048-ART3-II",
            "event_count",
            1,
        ))

        result = TemporalAttentionAnalyzer().analyze(scored)

        self.assertEqual(len(result), 0)

    def test_analysis_never_changes_score_or_contract(self):
        scored, _ = analyzed("2020-01-01", "2020-07-01")
        original_score = scored
        original_contract = scored.source_contract

        TemporalAttentionAnalyzer().analyze(
            CriterionScoreCollection((scored,))
        )

        self.assertIs(scored, original_score)
        self.assertIs(scored.source_contract, original_contract)

    def test_attentions_are_deterministic_repeatable_and_immutable(self):
        scored = score(year_contract(
            "2020-01-01",
            "2020-07-01",
            temporal_rule="FRACTION_ABOVE_SIX_MONTHS",
        ))
        scores = CriterionScoreCollection((scored,))
        analyzer = TemporalAttentionAnalyzer()

        first = analyzer.analyze(scores)
        second = analyzer.analyze(scores)

        self.assertEqual(first, second)
        with self.assertRaises(FrozenInstanceError):
            first.attentions[0].message = "changed"


if __name__ == "__main__":
    unittest.main()
