from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
from decimal import Decimal
import json
from pathlib import Path
import unittest

from applications.rsc.execution_contracts import (
    CriterionExecutionContractCollection,
    DuplicateExecutionContractError,
    ExecutionComputability,
    ExecutionContractResolutionError,
    ExecutionContractResolver,
    InconsistentExecutionContractManifestError,
    LegalComputability,
    MissingExecutionContractRuleError,
)
from applications.rsc.execution_facts import ExecutionFactCollection
from applications.rsc.execution_validation import (
    ExecutionValidationCollection,
    ExecutionValidator,
    ValidationState,
)
from test_execution_validation import prepared_fact


ROOT = Path(__file__).resolve().parents[1]
RULES = ROOT / "docs" / "normative" / "criterion_execution_rules.json"
MANIFEST = ROOT / "docs" / "normative" / "execution_rules_manifest.json"
CRITERIA = ROOT / "docs" / "normative" / "decree_criteria.json"


def sources(*, complete: bool = True):
    fact = prepared_fact(with_quantity=complete)
    facts = ExecutionFactCollection((fact,))
    validation = ExecutionValidator.from_files(RULES, MANIFEST).validate(
        facts
    )
    return facts, validation


class ExecutionContractResolverTests(unittest.TestCase):
    def setUp(self) -> None:
        self.resolver = ExecutionContractResolver.from_files(
            RULES,
            MANIFEST,
            CRITERIA,
        )

    def test_resolves_one_complete_contract_per_fact_and_validation(self):
        facts, validations = sources()

        result = self.resolver.resolve(facts, validations)

        self.assertEqual(len(result), 1)
        contract = result.contracts[0]
        self.assertEqual(
            contract.execution_fact_id,
            facts.facts[0].execution_fact_id,
        )
        self.assertEqual(
            contract.validation_id,
            validations.validations[0].validation_id,
        )
        self.assertIs(contract.source_execution_fact, facts.facts[0])
        self.assertIs(contract.source_validation, validations.validations[0])

    def test_duration_contract_is_executable_without_early_quantity(self):
        fact = prepared_fact(
            criterion_id="DEC13048-ANX-VI-ITEM-19",
            requirement_id="DEC13048-ART3-VI",
            with_quantity=False,
        )
        facts = ExecutionFactCollection((fact,))
        validations = ExecutionValidator.from_files(
            RULES,
            MANIFEST,
        ).validate(facts)

        contract = self.resolver.resolve(
            facts,
            validations,
        ).contracts[0]

        self.assertEqual(
            contract.execution_computability,
            ExecutionComputability.EXECUTABLE,
        )
        self.assertIsNone(contract.measurement.amount)
        self.assertTrue(all(
            occurrence.quantity is None
            for occurrence in contract.occurrences
        ))
        self.assertFalse(contract.source_validation.missing_measurements)

    def test_rule_is_materialized_without_execution(self):
        facts, validations = sources()

        contract = self.resolver.resolve(
            facts,
            validations,
        ).contracts[0]

        self.assertEqual(
            contract.execution_rule_id,
            "DEC13048-RULE-ANX-I-ITEM-02",
        )
        self.assertEqual(contract.counting_rule.rule_type, "CUSTOM_TEXT")
        self.assertEqual(contract.temporal_rule, "NONE")
        self.assertEqual(contract.aggregation_rule, "SUM")
        self.assertEqual(contract.overlap_rule, "FORBIDDEN")
        self.assertEqual(
            contract.applicable_table,
            "DEC13048-TABLE-ANEXO-I",
        )
        self.assertEqual(contract.article_reference, "DEC13048-ART-03")
        self.assertEqual(contract.annex_reference, "I")
        self.assertEqual(
            contract.legal_computability,
            LegalComputability.TEXT_DEPENDENT,
        )
        self.assertEqual(
            contract.execution_computability,
            ExecutionComputability.EXECUTABLE,
        )
        self.assertIn("Nenhuma pontuação foi calculada", contract.explanation)

    def test_resolves_official_unit_value_without_calculation(self):
        facts, validations = sources()

        contract = self.resolver.resolve(
            facts,
            validations,
        ).contracts[0]
        value = contract.resolved_normative_value

        self.assertEqual(value.value, Decimal("4.5"))
        self.assertEqual(value.unit, "Por designação")
        self.assertEqual(
            value.table_id,
            "DEC13048-TABLE-ANEXO-I",
        )
        self.assertEqual(value.criterion_id, contract.criterion_id)

    def test_absent_table_mapping_is_rejected(self):
        rules = json.loads(RULES.read_text(encoding="utf-8"))
        manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
        criteria = json.loads(CRITERIA.read_text(encoding="utf-8"))
        criteria["criteria"][1]["table"] = "ANEXO-INEXISTENTE"
        resolver = ExecutionContractResolver(rules, manifest, criteria)
        facts, validations = sources()

        with self.assertRaises(
            InconsistentExecutionContractManifestError
        ):
            resolver.resolve(facts, validations)

    def test_absent_singular_value_is_preserved_as_not_executable(self):
        rules = json.loads(RULES.read_text(encoding="utf-8"))
        manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
        criteria = json.loads(CRITERIA.read_text(encoding="utf-8"))
        criteria["criteria"][1]["points"] = None
        resolver = ExecutionContractResolver(rules, manifest, criteria)
        facts, validations = sources()

        contract = resolver.resolve(facts, validations).contracts[0]

        self.assertIsNone(contract.resolved_normative_value.value)
        self.assertEqual(
            contract.execution_computability,
            ExecutionComputability.NOT_EXECUTABLE,
        )

    def test_normative_value_traceability_reaches_decree_table_and_value(self):
        facts, validations = sources()

        trace = self.resolver.resolve(
            facts,
            validations,
        ).contracts[0].resolved_normative_value.traceability

        self.assertEqual(trace.document_id, "BR-DEC-13048-2026")
        self.assertEqual(trace.source_file, "decree_criteria.json")
        self.assertEqual(trace.table_id, "DEC13048-TABLE-ANEXO-I")
        self.assertEqual(trace.criterion_id, "DEC13048-ANX-I-ITEM-02")
        self.assertEqual(trace.source_field, "points")
        self.assertEqual(trace.original_value, "4,5")

    def test_preserves_measurement_occurrences_facts_and_documents(self):
        facts, validations = sources()
        source = facts.facts[0]

        contract = self.resolver.resolve(
            facts,
            validations,
        ).contracts[0]

        self.assertIs(contract.measurement, source.measurement)
        self.assertIs(contract.occurrences, source.quantified_occurrences)
        self.assertIs(contract.canonical_facts, source.canonical_facts)
        self.assertIs(
            contract.canonical_documents,
            source.canonical_documents,
        )
        self.assertEqual(len(contract.accepted_documents), 10)
        self.assertEqual(
            contract.required_facts,
            ("designation_count",),
        )

    def test_fact_and_validation_must_have_exact_correspondence(self):
        facts, validations = sources()
        changed = replace(
            validations.validations[0],
            execution_fact_id="different-fact",
        )

        with self.assertRaises(ExecutionContractResolutionError):
            self.resolver.resolve(
                facts,
                ExecutionValidationCollection((changed,)),
            )

    def test_inconsistent_manifest_is_rejected(self):
        rules = json.loads(RULES.read_text(encoding="utf-8"))
        manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
        criteria = json.loads(CRITERIA.read_text(encoding="utf-8"))
        manifest["entries"][0]["table_id"] = "wrong-table"

        with self.assertRaises(
            InconsistentExecutionContractManifestError
        ):
            ExecutionContractResolver(rules, manifest, criteria)

    def test_missing_rule_for_fact_is_rejected(self):
        facts, validations = sources()
        source_fact = replace(
            facts.facts[0],
            criterion_id="unknown-criterion",
        )
        source_validation = replace(
            validations.validations[0],
            criterion_id="unknown-criterion",
        )

        with self.assertRaises(MissingExecutionContractRuleError):
            self.resolver.resolve(
                ExecutionFactCollection((source_fact,)),
                ExecutionValidationCollection((source_validation,)),
            )

    def test_traceability_preserves_all_three_origins(self):
        facts, validations = sources()

        contract = self.resolver.resolve(
            facts,
            validations,
        ).contracts[0]

        self.assertEqual(
            contract.normative_traceability.execution_rule_id,
            contract.execution_rule_id,
        )
        self.assertEqual(
            contract.factual_traceability.document_id,
            "document-1",
        )
        self.assertEqual(
            contract.validation_traceability.execution_fact_id,
            contract.execution_fact_id,
        )

    def test_blocking_validation_is_preserved_not_revalidated(self):
        facts, validations = sources(complete=False)

        contract = self.resolver.resolve(
            facts,
            validations,
        ).contracts[0]

        self.assertEqual(contract.validation_state, ValidationState.BLOCKED)
        self.assertTrue(contract.unresolved_items)
        self.assertIn(
            "Campos pendentes impedem futura aplicação",
            contract.explanation,
        )

    def test_duplicate_contracts_are_rejected(self):
        facts, validations = sources()
        contract = self.resolver.resolve(
            facts,
            validations,
        ).contracts[0]

        with self.assertRaises(DuplicateExecutionContractError):
            CriterionExecutionContractCollection((contract, contract))

    def test_resolution_is_immutable_repeatable_and_deterministic(self):
        facts, validations = sources()

        first = self.resolver.resolve(facts, validations)
        second = self.resolver.resolve(facts, validations)

        self.assertEqual(first, second)
        self.assertEqual(
            first.contracts[0].contract_id,
            second.contracts[0].contract_id,
        )
        with self.assertRaises(FrozenInstanceError):
            first.contracts[0].aggregation_rule = "NONE"


if __name__ == "__main__":
    unittest.main()
