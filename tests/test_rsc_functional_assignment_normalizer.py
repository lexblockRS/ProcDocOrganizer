import ast
from datetime import date
from pathlib import Path
import unittest

from applications.rsc.models import (
    FunctionalAssignmentEvidence,
    FunctionalAssignmentEvidenceId,
    FunctionalAssignmentEvidenceStatus,
    SourceEvidenceReference,
)
from applications.rsc.services import FunctionalAssignmentNormalizer


def evidence(**changes):
    values = {
        "id": FunctionalAssignmentEvidenceId(
            "12345678-1234-5678-1234-567812345678"
        ),
        "person_id": "person-1",
        "source_evidence_reference": SourceEvidenceReference(
            "external:evidence-1"
        ),
        "exercise_type_code": "fiscal_contrato",
        "exercise_type_label": "Fiscalização de contrato",
        "role": "Fiscal titular",
        "organization": "Instituição",
        "start_date": date(2024, 1, 1),
        "end_date": date(2024, 12, 31),
        "unit": "Unidade Central",
        "administrative_reference": "Portaria 123",
    }
    values.update(changes)
    return FunctionalAssignmentEvidence(**values)


class FunctionalAssignmentNormalizerTests(unittest.TestCase):
    def setUp(self):
        self.normalizer = FunctionalAssignmentNormalizer()

    def test_accepts_only_raw_evidence(self):
        normalized = evidence().mark_normalized()

        with self.assertRaises(ValueError):
            self.normalizer.normalize(normalized)

    def test_rejects_invalid_input_type(self):
        with self.assertRaises(TypeError):
            self.normalizer.normalize(object())

    def test_returns_new_normalized_instance(self):
        original = evidence()

        result = self.normalizer.normalize(original)

        self.assertIsNot(result, original)
        self.assertIs(
            original.status,
            FunctionalAssignmentEvidenceStatus.RAW,
        )
        self.assertIs(
            result.status,
            FunctionalAssignmentEvidenceStatus.NORMALIZED,
        )

    def test_preserves_identity_and_opaque_references(self):
        original = evidence()

        result = self.normalizer.normalize(original)

        self.assertIs(result.id, original.id)
        self.assertEqual(result.person_id, original.person_id)
        self.assertIs(
            result.source_evidence_reference,
            original.source_evidence_reference,
        )

    def test_preserves_dates(self):
        original = evidence()

        result = self.normalizer.normalize(original)

        self.assertIs(result.start_date, original.start_date)
        self.assertIs(result.end_date, original.end_date)

    def test_preserves_absent_fields(self):
        original = evidence(
            start_date=None,
            end_date=None,
            unit=None,
            administrative_reference=None,
        )

        result = self.normalizer.normalize(original)

        self.assertIsNone(result.start_date)
        self.assertIsNone(result.end_date)
        self.assertIsNone(result.unit)
        self.assertIsNone(result.administrative_reference)

    def test_trims_and_collapses_redundant_whitespace(self):
        original = evidence(
            exercise_type_label=(
                "  Fiscalização\t de\n\n contrato  "
            ),
            role="  Fiscal\t titular  ",
            organization="  Instituto\n Federal  ",
            unit="  Unidade\t Central  ",
            administrative_reference="  Portaria\n 123  ",
        )

        result = self.normalizer.normalize(original)

        self.assertEqual(
            result.exercise_type_label,
            "Fiscalização de contrato",
        )
        self.assertEqual(result.role, "Fiscal titular")
        self.assertEqual(result.organization, "Instituto Federal")
        self.assertEqual(result.unit, "Unidade Central")
        self.assertEqual(
            result.administrative_reference,
            "Portaria 123",
        )

    def test_does_not_apply_semantic_normalization(self):
        original = evidence(
            exercise_type_code="PROGRAD",
            exercise_type_label="PROGRAD",
            role="Coordenador Acadêmico",
            organization="Campus de Alegrete",
            unit="PROGRAD",
        )

        result = self.normalizer.normalize(original)

        self.assertEqual(result.exercise_type_code, "PROGRAD")
        self.assertEqual(result.exercise_type_label, "PROGRAD")
        self.assertEqual(result.role, "Coordenador Acadêmico")
        self.assertEqual(
            result.organization,
            "Campus de Alegrete",
        )
        self.assertEqual(result.unit, "PROGRAD")

    def test_returns_new_instance_even_without_text_changes(self):
        original = evidence()

        result = self.normalizer.normalize(original)

        self.assertIsNot(result, original)
        self.assertEqual(result.role, original.role)
        self.assertEqual(result.organization, original.organization)

    def test_text_transformation_is_non_cumulative(self):
        first = self.normalizer.normalize(
            evidence(role="  Fiscal\t titular  ")
        )
        second_source = evidence(role=first.role)
        second = self.normalizer.normalize(second_source)

        self.assertEqual(second.role, first.role)

    def test_second_normalization_is_rejected_by_state_machine(self):
        normalized = self.normalizer.normalize(evidence())

        with self.assertRaises(ValueError):
            self.normalizer.normalize(normalized)

    def test_service_is_exported(self):
        self.assertTrue(FunctionalAssignmentNormalizer)


class FunctionalAssignmentNormalizerArchitectureTests(unittest.TestCase):
    def test_has_no_forbidden_dependencies(self):
        path = (
            Path(__file__).parents[1]
            / "applications"
            / "rsc"
            / "services"
            / "functional_assignment_normalizer.py"
        )
        tree = ast.parse(path.read_text(encoding="utf-8"))
        imported_modules = {
            node.module or ""
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom)
        }
        imported_modules.update(
            alias.name
            for node in ast.walk(tree)
            if isinstance(node, ast.Import)
            for alias in node.names
        )

        self.assertEqual(
            imported_modules,
            {"applications.rsc.models"},
        )


if __name__ == "__main__":
    unittest.main()
