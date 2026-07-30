from __future__ import annotations

from collections import Counter
from dataclasses import FrozenInstanceError, replace
from decimal import Decimal
import json
from pathlib import Path
import unittest

from applications.rsc.execution_compatibility import (
    CompatibilityState,
    ExecutionCompatibilityEvaluator,
)
from applications.rsc.execution_facts import ExecutionFactCollection
from applications.rsc.execution_validation import ExecutionValidator
from applications.rsc.normative_catalog import (
    ArithmeticEngine,
    COMPATIBILITY_POLICIES,
    CompatibilityPolicyId,
    MeasurementType,
    NormativeCatalogError,
    NormativeCriterionCatalog,
    OFFICIAL_NORMATIVE_CATALOG,
)
from test_execution_compatibility import event_fact


ROOT = Path(__file__).resolve().parents[1]
RULES = ROOT / "docs" / "normative" / "criterion_execution_rules.json"
MANIFEST = ROOT / "docs" / "normative" / "execution_rules_manifest.json"
CRITERIA = ROOT / "docs" / "normative" / "decree_criteria.json"


class NormativeCatalogTests(unittest.TestCase):
    def test_catalog_contains_all_55_unique_criteria(self):
        codes = tuple(item.code for item in OFFICIAL_NORMATIVE_CATALOG)

        self.assertEqual(len(OFFICIAL_NORMATIVE_CATALOG), 55)
        self.assertEqual(len(codes), len(set(codes)))
        self.assertEqual(
            Counter(item.annex for item in OFFICIAL_NORMATIVE_CATALOG),
            {
                "I": 10,
                "II": 11,
                "III": 3,
                "IV": 8,
                "V": 4,
                "VI": 19,
            },
        )

    def test_codes_descriptions_units_values_and_links_match_sources(self):
        criteria = json.loads(
            CRITERIA.read_text(encoding="utf-8")
        )["criteria"]
        rules = {
            item["criterion_id"]: item
            for item in json.loads(
                RULES.read_text(encoding="utf-8")
            )["rules"]
        }

        for source in criteria:
            with self.subTest(criterion_id=source["id"]):
                definition = OFFICIAL_NORMATIVE_CATALOG.find(
                    source["id"]
                )
                self.assertIsNotNone(definition)
                self.assertEqual(
                    definition.description,
                    source["official_text"],
                )
                self.assertEqual(definition.annex, source["annex"])
                self.assertEqual(definition.item, source["item"])
                self.assertEqual(
                    definition.normative_unit,
                    source["unit"],
                )
                rule = rules[source["id"]]
                self.assertEqual(
                    definition.execution_rule_id,
                    rule["id"],
                )
                self.assertEqual(
                    definition.requirement_id,
                    rule["requirement_id"],
                )
                self.assertEqual(
                    definition.arithmetic_engine.value,
                    rule["counting_rule"]["type"],
                )
                self.assertEqual(
                    definition.required_measurement.value,
                    rule["measurement_type"],
                )
                expected = (
                    Decimal(source["points"].replace(",", "."))
                    if source["points"] is not None
                    else None
                )
                self.assertEqual(definition.normative_value, expected)
                expected_variants = tuple(
                    (
                        item["role"],
                        Decimal(item["points"].replace(",", ".")),
                    )
                    for item in (source["variants"] or ())
                )
                self.assertEqual(
                    tuple(
                        (item.selector, item.value)
                        for item in definition.value_variants
                    ),
                    expected_variants,
                )

    def test_every_engine_measurement_and_policy_is_declared(self):
        for definition in OFFICIAL_NORMATIVE_CATALOG:
            with self.subTest(criterion_id=definition.code):
                self.assertIsInstance(
                    definition.arithmetic_engine,
                    ArithmeticEngine,
                )
                self.assertIsInstance(
                    definition.required_measurement,
                    MeasurementType,
                )
                self.assertIsInstance(
                    definition.compatibility_policy,
                    CompatibilityPolicyId,
                )
                policy = COMPATIBILITY_POLICIES[
                    definition.compatibility_policy
                ]
                self.assertIn(
                    definition.required_measurement,
                    policy.allowed_measurements,
                )

    def test_every_definition_has_limits_dependencies_and_explanation(self):
        for definition in OFFICIAL_NORMATIVE_CATALOG:
            with self.subTest(criterion_id=definition.code):
                self.assertIsInstance(definition.limits, tuple)
                self.assertEqual(len(definition.dependencies), 4)
                self.assertTrue(definition.human_decision_required)
                self.assertIn(
                    definition.normative_unit,
                    definition.explanation_template,
                )

    def test_duplicate_codes_are_rejected(self):
        definition = OFFICIAL_NORMATIVE_CATALOG.criteria[0]

        with self.assertRaises(NormativeCatalogError):
            NormativeCriterionCatalog((definition, definition))

    def test_each_catalog_owns_its_lookup_index(self):
        definition = OFFICIAL_NORMATIVE_CATALOG.criteria[0]
        isolated = NormativeCriterionCatalog((definition,))

        self.assertIs(isolated.find(definition.code), definition)
        self.assertIsNone(
            isolated.find("DEC13048-ANX-VI-ITEM-19")
        )

    def test_incompatible_policy_is_rejected(self):
        definition = OFFICIAL_NORMATIVE_CATALOG.criteria[0]

        with self.assertRaises(NormativeCatalogError):
            replace(
                definition,
                compatibility_policy=(
                    CompatibilityPolicyId.QUANTITATIVE
                ),
            )

    def test_catalog_and_definitions_are_immutable(self):
        definition = OFFICIAL_NORMATIVE_CATALOG.criteria[0]

        with self.assertRaises(FrozenInstanceError):
            definition.normative_value = Decimal("99")
        with self.assertRaises(TypeError):
            COMPATIBILITY_POLICIES[
                CompatibilityPolicyId.TEMPORAL
            ] = None

    def test_compatibility_consumes_catalog_without_policy_duplication(self):
        fact = event_fact()
        facts = ExecutionFactCollection((fact,))
        validations = ExecutionValidator.from_files(
            RULES,
            MANIFEST,
        ).validate(facts)

        result = ExecutionCompatibilityEvaluator.from_catalog(
            OFFICIAL_NORMATIVE_CATALOG
        ).evaluate(facts, validations)

        self.assertEqual(
            result.compatibilities[0].compatibility_state,
            CompatibilityState.COMPATIBLE,
        )
        self.assertEqual(
            result.compatibilities[0].allowed_measurement_types,
            ("COUNT", "QUANTITY", "HOURS"),
        )


if __name__ == "__main__":
    unittest.main()
