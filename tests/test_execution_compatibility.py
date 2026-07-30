from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
import json
from pathlib import Path
import unittest

from applications.rsc.execution_compatibility import (
    CompatibilityState,
    ExecutionCompatibilityCollection,
    ExecutionCompatibilityError,
    ExecutionCompatibilityEvaluator,
)
from applications.rsc.execution_contracts import (
    ExecutionComputability,
    ExecutionContractResolver,
)
from applications.rsc.constraint_evaluation import FactUsed
from applications.rsc.criterion_assessment import CriterionAssessmentCollection
from applications.rsc.execution_facts import ExecutionFactBuilder
from applications.rsc.execution_facts import ExecutionFactCollection
from applications.rsc.execution_validation import (
    ExecutionValidationCollection,
    ExecutionValidator,
)
from test_execution_validation import prepared_fact
from test_execution_facts import assessment, context


ROOT = Path(__file__).resolve().parents[1]
RULES = ROOT / "docs" / "normative" / "criterion_execution_rules.json"
MANIFEST = ROOT / "docs" / "normative" / "execution_rules_manifest.json"
CRITERIA = ROOT / "docs" / "normative" / "decree_criteria.json"


def quantitative_fact(
    criterion_id,
    requirement_id,
    fact_name,
    amount=2,
):
    evaluation_context = context()
    source = CriterionAssessmentCollection((
        assessment(
            evaluation_context,
            criterion_id,
            requirement_id,
            facts=(
                FactUsed(
                    key=fact_name,
                    value=amount,
                    source="test",
                ),
            ),
        ),
    ))
    return ExecutionFactBuilder.from_files(
        RULES,
        MANIFEST,
    ).build(source, evaluation_context).facts[0]


def event_fact(amount=2):
    return quantitative_fact(
        "DEC13048-ANX-II-ITEM-07",
        "DEC13048-ART3-II",
        "event_count",
        amount,
    )


def evaluated(fact):
    facts = ExecutionFactCollection((fact,))
    validations = ExecutionValidator.from_files(
        RULES,
        MANIFEST,
    ).validate(facts)
    result = ExecutionCompatibilityEvaluator.from_file(RULES).evaluate(
        facts,
        validations,
    )
    return facts, validations, result


class ExecutionCompatibilityTests(unittest.TestCase):
    def test_per_event_accepts_declared_quantitative_measurement(self):
        fact = event_fact()

        _, _, result = evaluated(fact)
        compatibility = result.compatibilities[0]

        self.assertEqual(
            compatibility.compatibility_state,
            CompatibilityState.COMPATIBLE,
        )
        self.assertEqual(compatibility.counting_rule, "PER_EVENT")
        self.assertEqual(compatibility.measurement_type, "COUNT")
        self.assertIn(
            "COUNT",
            compatibility.allowed_measurement_types,
        )

    def test_per_month_and_per_year_accept_duration(self):
        cases = (
            ("DEC13048-ANX-VI-ITEM-19", "DEC13048-ART3-VI"),
            ("DEC13048-ANX-I-ITEM-01", "DEC13048-ART3-I"),
        )
        for criterion_id, requirement_id in cases:
            with self.subTest(criterion_id=criterion_id):
                fact = prepared_fact(
                    criterion_id=criterion_id,
                    requirement_id=requirement_id,
                    with_quantity=False,
                )
                _, _, result = evaluated(fact)
                compatibility = result.compatibilities[0]
                self.assertEqual(
                    compatibility.compatibility_state,
                    CompatibilityState.COMPATIBLE,
                )
                self.assertEqual(
                    compatibility.allowed_measurement_types,
                    ("DURATION",),
                )

    def test_per_publication_accepts_declared_count(self):
        fact = quantitative_fact(
            "DEC13048-ANX-VI-ITEM-10",
            "DEC13048-ART3-VI",
            "publication_count",
        )

        _, _, result = evaluated(fact)
        compatibility = result.compatibilities[0]

        self.assertEqual(
            compatibility.compatibility_state,
            CompatibilityState.COMPATIBLE,
        )
        self.assertEqual(
            compatibility.counting_rule,
            "PER_PUBLICATION",
        )

    def test_per_event_rejects_duration_without_changing_validation(self):
        source = event_fact()
        fact = replace(
            source,
            measurement=replace(
                source.measurement,
                measurement_type="DURATION",
            ),
        )
        facts = ExecutionFactCollection((fact,))
        validations = ExecutionValidator.from_files(
            RULES,
            MANIFEST,
        ).validate(facts)

        compatibility = ExecutionCompatibilityEvaluator.from_file(
            RULES
        ).evaluate(facts, validations).compatibilities[0]

        self.assertFalse(validations.validations[0].blocking_issues)
        self.assertEqual(
            compatibility.compatibility_state,
            CompatibilityState.INCOMPATIBLE,
        )
        self.assertTrue(any(
            "PER_EVENT" in issue for issue in compatibility.issues
        ))

    def test_incompatible_measurement_blocks_contract_before_kernel(self):
        source = event_fact()
        fact = replace(
            source,
            measurement=replace(
                source.measurement,
                measurement_type="DURATION",
            ),
        )
        facts = ExecutionFactCollection((fact,))
        validations = ExecutionValidator.from_files(
            RULES,
            MANIFEST,
        ).validate(facts)
        compatibilities = ExecutionCompatibilityEvaluator.from_file(
            RULES
        ).evaluate(facts, validations)

        contract = ExecutionContractResolver.from_files(
            RULES,
            MANIFEST,
            CRITERIA,
        ).resolve(facts, validations, compatibilities).contracts[0]

        self.assertEqual(
            contract.execution_computability,
            ExecutionComputability.BLOCKED,
        )
        self.assertTrue(any(
            item.startswith("incompatible_measurement:")
            for item in contract.unresolved_items
        ))

    def test_missing_policy_is_safely_incompatible(self):
        rules = json.loads(RULES.read_text(encoding="utf-8"))
        target = next(
            item for item in rules["rules"]
            if item["criterion_id"] == "DEC13048-ANX-II-ITEM-07"
        )
        target["counting_rule"]["type"] = "UNKNOWN_RULE"
        fact = event_fact()
        facts = ExecutionFactCollection((fact,))
        validations = ExecutionValidator.from_files(
            RULES,
            MANIFEST,
        ).validate(facts)

        compatibility = ExecutionCompatibilityEvaluator(
            rules
        ).evaluate(facts, validations).compatibilities[0]

        self.assertEqual(
            compatibility.compatibility_state,
            CompatibilityState.INCOMPATIBLE,
        )
        self.assertEqual(compatibility.allowed_measurement_types, ())

    def test_requires_exact_fact_validation_correspondence(self):
        fact = prepared_fact()
        facts = ExecutionFactCollection((fact,))
        validations = ExecutionValidator.from_files(
            RULES,
            MANIFEST,
        ).validate(facts)
        changed = replace(
            validations.validations[0],
            execution_fact_id="different",
        )

        with self.assertRaises(ExecutionCompatibilityError):
            ExecutionCompatibilityEvaluator.from_file(RULES).evaluate(
                facts,
                ExecutionValidationCollection((changed,)),
            )

    def test_collection_is_immutable_repeatable_and_deterministic(self):
        fact = prepared_fact()

        _, _, first = evaluated(fact)
        _, _, second = evaluated(fact)

        self.assertEqual(first, second)
        self.assertIsInstance(first, ExecutionCompatibilityCollection)
        with self.assertRaises(FrozenInstanceError):
            first.compatibilities[0].compatibility_state = (
                CompatibilityState.INCOMPATIBLE
            )


if __name__ == "__main__":
    unittest.main()
