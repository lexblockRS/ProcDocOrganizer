from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
import json
from pathlib import Path
import unittest

from applications.rsc.criterion_assessment import (
    CriterionAssessmentCollection,
)
from applications.rsc.execution_facts import (
    CanonicalTimeInterval,
    ExecutionFactBuilder,
    ExecutionFactCollection,
    MeasurementValidationState,
    OverlapStatus,
)
from applications.rsc.execution_validation import (
    ExecutionValidator,
    ValidationState,
    measurement_is_computable,
)
from test_execution_facts import assessment, context


ROOT = Path(__file__).resolve().parents[1]
RULES = ROOT / "docs" / "normative" / "criterion_execution_rules.json"
MANIFEST = ROOT / "docs" / "normative" / "execution_rules_manifest.json"


def prepared_fact(
    criterion_id: str = "DEC13048-ANX-I-ITEM-02",
    requirement_id: str = "DEC13048-ART3-I",
    *,
    with_quantity: bool = True,
):
    from applications.rsc.constraint_evaluation import FactUsed

    ctx = context()
    facts = (
        (
            FactUsed(
                key="designation_count",
                value=2,
                source="declared",
            ),
        )
        if with_quantity
        else ()
    )
    source = assessment(
        ctx,
        criterion_id=criterion_id,
        requirement_id=requirement_id,
        facts=facts,
    )
    builder = ExecutionFactBuilder.from_files(RULES, MANIFEST)
    result = builder.build(
        CriterionAssessmentCollection((source,)),
        ctx,
    )
    return result.facts[0]


class ExecutionValidatorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.validator = ExecutionValidator.from_files(RULES, MANIFEST)

    def test_complete_contract_is_text_dependent_by_declared_model(self):
        fact = prepared_fact()

        validation = self.validator.validate(
            ExecutionFactCollection((fact,))
        ).validations[0]

        self.assertEqual(
            validation.validation_state,
            ValidationState.TEXT_DEPENDENT,
        )
        self.assertFalse(validation.blocking_issues)
        self.assertFalse(validation.missing_facts)
        self.assertFalse(validation.missing_measurements)

    def test_missing_fact_and_measurement_block_contract(self):
        fact = prepared_fact(with_quantity=False)

        validation = self.validator.validate(
            ExecutionFactCollection((fact,))
        ).validations[0]

        self.assertEqual(validation.validation_state, ValidationState.BLOCKED)
        self.assertEqual(
            validation.missing_facts[0].fact_name,
            "designation_count",
        )
        self.assertEqual(len(validation.missing_measurements), 1)

    def test_duration_is_computable_from_complete_canonical_interval(self):
        fact = prepared_fact(
            criterion_id="DEC13048-ANX-VI-ITEM-19",
            requirement_id="DEC13048-ART3-VI",
            with_quantity=False,
        )

        validation = self.validator.validate(
            ExecutionFactCollection((fact,))
        ).validations[0]

        self.assertIsNone(fact.measurement.amount)
        self.assertEqual(
            fact.measurement.validation_state,
            MeasurementValidationState.REVIEW_REQUIRED,
        )
        self.assertFalse(validation.missing_measurements)
        self.assertNotEqual(
            validation.validation_state,
            ValidationState.BLOCKED,
        )
        self.assertTrue(all(
            occurrence.quantity is None
            for occurrence in fact.quantified_occurrences
        ))

    def test_duration_without_closed_interval_remains_blocked(self):
        fact = prepared_fact(
            criterion_id="DEC13048-ANX-VI-ITEM-19",
            requirement_id="DEC13048-ART3-VI",
            with_quantity=False,
        )
        fact = replace(
            fact,
            canonical_time_interval=replace(
                fact.canonical_time_interval,
                end=None,
            ),
        )

        validation = self.validator.validate(
            ExecutionFactCollection((fact,))
        ).validations[0]

        self.assertEqual(
            validation.validation_state,
            ValidationState.BLOCKED,
        )
        self.assertEqual(len(validation.missing_measurements), 1)

    def test_duration_with_invalid_interval_remains_blocked(self):
        fact = prepared_fact(
            criterion_id="DEC13048-ANX-VI-ITEM-19",
            requirement_id="DEC13048-ART3-VI",
            with_quantity=False,
        )
        fact = replace(
            fact,
            canonical_time_interval=replace(
                fact.canonical_time_interval,
                end="invalid-date",
            ),
        )

        validation = self.validator.validate(
            ExecutionFactCollection((fact,))
        ).validations[0]

        self.assertEqual(
            validation.validation_state,
            ValidationState.BLOCKED,
        )
        self.assertEqual(len(validation.missing_measurements), 1)

    def test_amount_based_measurements_require_available_amount(self):
        source = prepared_fact()
        for measurement_type in ("QUANTITY", "HOURS", "COUNT"):
            with self.subTest(measurement_type=measurement_type):
                absent = replace(
                    source,
                    measurement=replace(
                        source.measurement,
                        measurement_type=measurement_type,
                        amount=None,
                        validation_state=MeasurementValidationState.MISSING,
                    ),
                )
                available = replace(
                    absent,
                    measurement=replace(
                        absent.measurement,
                        amount=1,
                        validation_state=(
                            MeasurementValidationState.AVAILABLE
                        ),
                    ),
                )

                self.assertFalse(measurement_is_computable(absent))
                self.assertTrue(measurement_is_computable(available))

    def test_missing_document_is_reported_separately(self):
        fact = replace(prepared_fact(), canonical_documents=())

        validation = self.validator.validate(
            ExecutionFactCollection((fact,))
        ).validations[0]

        self.assertEqual(validation.validation_state, ValidationState.BLOCKED)
        self.assertEqual(
            validation.missing_documents[0].document_id,
            "document-1",
        )

    def test_pending_variant_requires_human_review_when_measurement_exists(self):
        fact = prepared_fact(
            criterion_id="DEC13048-ANX-V-ITEM-01",
            requirement_id="DEC13048-ART3-V",
            with_quantity=False,
        )
        fact = replace(
            fact,
            measurement=replace(
                fact.measurement,
                amount=1,
                validation_state=MeasurementValidationState.AVAILABLE,
            ),
            quantified_occurrences=tuple(
                replace(item, quantity=1)
                for item in fact.quantified_occurrences
            ),
            unresolved_items=(),
        )

        validation = self.validator.validate(
            ExecutionFactCollection((fact,))
        ).validations[0]

        self.assertEqual(
            validation.validation_state,
            ValidationState.HUMAN_REVIEW_REQUIRED,
        )
        self.assertEqual(len(validation.unresolved_variants), 1)
        self.assertIn("titular", validation.unresolved_variants[0].possible_variants)

    def test_possible_overlap_requires_human_review(self):
        from applications.rsc.constraint_evaluation import FactUsed

        ctx = context()
        first = assessment(
            ctx,
            criterion_id="DEC13048-ANX-I-ITEM-02",
            requirement_id="DEC13048-ART3-I",
            facts=(
                FactUsed(
                    key="designation_count",
                    value=1,
                    source="declared",
                ),
            ),
        )
        second = assessment(
            ctx,
            criterion_id="DEC13048-ANX-II-ITEM-01",
            requirement_id="DEC13048-ART3-II",
            facts=(
                FactUsed(
                    key="project_count",
                    value=1,
                    source="declared",
                ),
            ),
        )
        facts = ExecutionFactBuilder.from_files(RULES, MANIFEST).build(
            CriterionAssessmentCollection((first, second)),
            ctx,
        )
        adjusted = ExecutionFactCollection(tuple(
            replace(
                fact,
                measurement=replace(
                    fact.measurement,
                    amount=1,
                    validation_state=MeasurementValidationState.AVAILABLE,
                ),
                quantified_occurrences=tuple(
                    replace(item, quantity=1)
                    for item in fact.quantified_occurrences
                ),
                unresolved_items=(),
            )
            for fact in facts
        ))

        validations = self.validator.validate(adjusted)

        self.assertTrue(all(
            item.validation_state
            is ValidationState.HUMAN_REVIEW_REQUIRED
            for item in validations
        ))
        self.assertTrue(all(
            item.overlap_status is OverlapStatus.POSSIBLE
            for item in validations
        ))

    def test_incompatible_unit_blocks_contract_without_correction(self):
        fact = prepared_fact()
        changed = replace(
            fact,
            measurement=replace(fact.measurement, unit="Outra unidade"),
        )

        validation = self.validator.validate(
            ExecutionFactCollection((changed,))
        ).validations[0]

        self.assertEqual(validation.validation_state, ValidationState.BLOCKED)
        self.assertTrue(any(
            item.field == "measurement.unit"
            for item in validation.inconsistent_facts
        ))
        self.assertEqual(changed.measurement.unit, "Outra unidade")

    def test_invalid_period_is_inconsistent(self):
        fact = prepared_fact()
        interval = CanonicalTimeInterval(
            start="2022-01-01",
            end="2021-01-01",
            start_source_field="start_date",
            end_source_field="end_date",
        )
        changed = replace(fact, canonical_time_interval=interval)

        validation = self.validator.validate(
            ExecutionFactCollection((changed,))
        ).validations[0]

        self.assertEqual(validation.validation_state, ValidationState.BLOCKED)
        self.assertTrue(any(
            item.field == "canonical_time_interval"
            for item in validation.inconsistent_facts
        ))

    def test_broken_rule_traceability_is_blocking(self):
        fact = prepared_fact()
        changed = replace(
            fact,
            normative_traceability=replace(
                fact.normative_traceability,
                execution_rule_id="wrong-rule",
            ),
        )

        validation = self.validator.validate(
            ExecutionFactCollection((changed,))
        ).validations[0]

        self.assertEqual(validation.validation_state, ValidationState.BLOCKED)
        self.assertTrue(any(
            item.field == "normative.execution_rule_id"
            for item in validation.inconsistent_facts
        ))

    def test_ready_and_ready_with_warnings_states_are_deterministic(self):
        rules = json.loads(RULES.read_text(encoding="utf-8"))
        manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
        for rule in rules["rules"]:
            if rule["criterion_id"] == "DEC13048-ANX-I-ITEM-02":
                rule["computability_level"] = "FULLY_EXECUTABLE"
        fact = replace(
            prepared_fact(),
            computability_level="FULLY_EXECUTABLE",
            unresolved_items=(),
            human_review_required=False,
        )
        validator = ExecutionValidator(rules, manifest)

        ready = validator.validate(
            ExecutionFactCollection((fact,))
        ).validations[0]
        warned = validator.validate(ExecutionFactCollection((
            replace(fact, unresolved_items=("advisory",)),
        ))).validations[0]

        self.assertEqual(ready.validation_state, ValidationState.READY)
        self.assertEqual(
            warned.validation_state,
            ValidationState.READY_WITH_WARNINGS,
        )

    def test_validation_is_immutable_and_repeated_results_are_equal(self):
        fact = prepared_fact()
        collection = ExecutionFactCollection((fact,))

        first = self.validator.validate(collection)
        second = self.validator.validate(collection)

        self.assertEqual(first, second)
        self.assertEqual(
            first.validations[0].validation_id,
            second.validations[0].validation_id,
        )
        with self.assertRaises(FrozenInstanceError):
            first.validations[0].validation_state = ValidationState.READY


if __name__ == "__main__":
    unittest.main()
