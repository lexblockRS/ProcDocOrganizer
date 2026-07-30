import ast
from dataclasses import FrozenInstanceError
from datetime import date, datetime
from pathlib import Path
import unittest

from applications.rsc.models import (
    Activity,
    FunctionalAssignmentEvidence,
    FunctionalAssignmentEvidenceId,
    FunctionalAssignmentEvidenceStatus,
    FunctionalExercise,
    Project,
    SourceEvidenceReference,
)


UUID_TEXT = "12345678-1234-5678-1234-567812345678"


def evidence(**changes):
    values = {
        "id": FunctionalAssignmentEvidenceId(UUID_TEXT),
        "person_id": "person-1",
        "source_evidence_reference": SourceEvidenceReference(
            "evidence:external-1"
        ),
        "exercise_type_code": "fiscal_contrato",
        "exercise_type_label": "Fiscalização de contrato",
        "role": "Fiscal titular",
        "organization": "Instituição",
    }
    values.update(changes)
    return FunctionalAssignmentEvidence(**values)


class FunctionalAssignmentEvidenceIdTests(unittest.TestCase):
    def test_creates_valid_id(self):
        identifier = FunctionalAssignmentEvidenceId(UUID_TEXT)

        self.assertEqual(identifier.value, UUID_TEXT)
        self.assertEqual(str(identifier), UUID_TEXT)

    def test_normalizes_uuid_representation(self):
        identifier = FunctionalAssignmentEvidenceId.from_string(
            "  12345678123456781234567812345678  "
        )

        self.assertEqual(identifier.value, UUID_TEXT)

    def test_rejects_empty_value(self):
        with self.assertRaises(ValueError):
            FunctionalAssignmentEvidenceId(" ")

    def test_rejects_invalid_uuid(self):
        with self.assertRaises(ValueError):
            FunctionalAssignmentEvidenceId("invalid")

    def test_rejects_invalid_type(self):
        with self.assertRaises(TypeError):
            FunctionalAssignmentEvidenceId(None)

    def test_equality_is_by_value(self):
        self.assertEqual(
            FunctionalAssignmentEvidenceId(UUID_TEXT),
            FunctionalAssignmentEvidenceId(UUID_TEXT),
        )


class SourceEvidenceReferenceTests(unittest.TestCase):
    def test_creates_valid_reference(self):
        reference = SourceEvidenceReference("  external:ABC-123  ")

        self.assertEqual(reference.value, "external:ABC-123")
        self.assertEqual(str(reference), "external:ABC-123")

    def test_rejects_empty_reference(self):
        with self.assertRaises(ValueError):
            SourceEvidenceReference(" ")

    def test_rejects_invalid_type(self):
        with self.assertRaises(TypeError):
            SourceEvidenceReference(None)

    def test_preserves_opaque_reference_format(self):
        value = "scheme://opaque/path?key=A_B-1"

        self.assertEqual(SourceEvidenceReference(value).value, value)


class FunctionalAssignmentEvidenceCreationTests(unittest.TestCase):
    def test_creates_with_required_fields_and_raw_status(self):
        item = evidence()

        self.assertEqual(item.person_id, "person-1")
        self.assertIs(
            item.status,
            FunctionalAssignmentEvidenceStatus.RAW,
        )
        self.assertIsNone(item.start_date)
        self.assertIsNone(item.end_date)

    def test_creates_with_all_fields(self):
        item = evidence(
            start_date=date(2024, 1, 1),
            end_date=date(2024, 12, 31),
            unit="Unidade Central",
            administrative_reference="Portaria 123",
        )

        self.assertEqual(item.start_date, date(2024, 1, 1))
        self.assertEqual(item.end_date, date(2024, 12, 31))
        self.assertEqual(item.unit, "Unidade Central")
        self.assertEqual(
            item.administrative_reference,
            "Portaria 123",
        )

    def test_accepts_only_start_date(self):
        item = evidence(start_date=date(2024, 1, 1))

        self.assertEqual(item.start_date, date(2024, 1, 1))
        self.assertIsNone(item.end_date)

    def test_accepts_only_end_date(self):
        item = evidence(end_date=date(2024, 12, 31))

        self.assertIsNone(item.start_date)
        self.assertEqual(item.end_date, date(2024, 12, 31))

    def test_accepts_both_dates(self):
        item = evidence(
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 1),
        )

        self.assertEqual(item.start_date, item.end_date)

    def test_rejects_end_before_start(self):
        with self.assertRaises(ValueError):
            evidence(
                start_date=date(2024, 1, 2),
                end_date=date(2024, 1, 1),
            )

    def test_rejects_invalid_date_types_and_datetime(self):
        for field, value in (
            ("start_date", "2024-01-01"),
            ("end_date", "2024-01-01"),
            ("start_date", datetime(2024, 1, 1)),
            ("end_date", datetime(2024, 1, 1)),
        ):
            with self.subTest(field=field, value=value):
                with self.assertRaises(TypeError):
                    evidence(**{field: value})

    def test_rejects_empty_required_text_fields(self):
        for field in (
            "person_id",
            "exercise_type_code",
            "exercise_type_label",
            "role",
            "organization",
        ):
            with self.subTest(field=field):
                with self.assertRaises(ValueError):
                    evidence(**{field: " "})

    def test_rejects_invalid_required_text_types(self):
        for field in (
            "person_id",
            "exercise_type_code",
            "exercise_type_label",
            "role",
            "organization",
        ):
            with self.subTest(field=field):
                with self.assertRaises(TypeError):
                    evidence(**{field: None})

    def test_rejects_invalid_identity_reference_and_status_types(self):
        for field in ("id", "source_evidence_reference", "status"):
            with self.subTest(field=field):
                with self.assertRaises(TypeError):
                    evidence(**{field: object()})

    def test_normalizes_text_spaces(self):
        item = evidence(
            person_id="  person-1  ",
            exercise_type_code=" fiscal   contrato ",
            exercise_type_label=" Fiscalização   de contrato ",
            role=" Fiscal   titular ",
            organization=" Instituto   Federal ",
            unit=" Unidade   Central ",
            administrative_reference=" Portaria   123 ",
        )

        self.assertEqual(item.person_id, "person-1")
        self.assertEqual(item.exercise_type_code, "fiscal contrato")
        self.assertEqual(
            item.exercise_type_label,
            "Fiscalização de contrato",
        )
        self.assertEqual(item.role, "Fiscal titular")
        self.assertEqual(item.organization, "Instituto Federal")
        self.assertEqual(item.unit, "Unidade Central")
        self.assertEqual(
            item.administrative_reference,
            "Portaria 123",
        )

    def test_rejects_empty_optional_text_when_provided(self):
        for field in ("unit", "administrative_reference"):
            with self.subTest(field=field):
                with self.assertRaises(ValueError):
                    evidence(**{field: " "})

    def test_rejects_invalid_optional_text_types(self):
        for field in ("unit", "administrative_reference"):
            with self.subTest(field=field):
                with self.assertRaises(TypeError):
                    evidence(**{field: 123})

    def test_is_immutable(self):
        item = evidence()

        with self.assertRaises(FrozenInstanceError):
            item.role = "Outro"


class FunctionalAssignmentEvidenceTransitionTests(unittest.TestCase):
    def test_progresses_through_all_states(self):
        raw = evidence()
        identified = raw.mark_identified()
        linked = identified.mark_linked()

        self.assertIs(
            identified.status,
            FunctionalAssignmentEvidenceStatus.IDENTIFIED,
        )
        self.assertIs(
            linked.status,
            FunctionalAssignmentEvidenceStatus.LINKED,
        )
        self.assertIs(
            raw.status,
            FunctionalAssignmentEvidenceStatus.RAW,
        )

    def test_rejects_state_skips(self):
        raw = evidence()

        with self.assertRaises(ValueError):
            raw.mark_linked()

    def test_rejects_regressions_and_repeated_transitions(self):
        normalized = evidence().mark_normalized()
        identified = normalized.mark_identified()
        linked = identified.mark_linked()

        for item, transition in (
            (normalized, normalized.mark_normalized),
            (identified, identified.mark_normalized),
            (identified, identified.mark_identified),
            (linked, linked.mark_normalized),
            (linked, linked.mark_identified),
            (linked, linked.mark_linked),
        ):
            with self.subTest(status=item.status, transition=transition):
                with self.assertRaises(ValueError):
                    transition()

    def test_transitions_preserve_all_other_attributes(self):
        original = evidence(
            start_date=date(2024, 1, 1),
            unit="Unidade",
            administrative_reference="Portaria 123",
        )
        transitioned = (
            original.mark_normalized().mark_identified().mark_linked()
        )

        for field in (
            "id",
            "person_id",
            "source_evidence_reference",
            "exercise_type_code",
            "exercise_type_label",
            "role",
            "organization",
            "start_date",
            "end_date",
            "unit",
            "administrative_reference",
        ):
            with self.subTest(field=field):
                self.assertEqual(
                    getattr(transitioned, field),
                    getattr(original, field),
                )


class FunctionalAssignmentEvidenceArchitectureTests(unittest.TestCase):
    def test_model_has_only_standard_library_dependencies(self):
        path = (
            Path(__file__).parents[1]
            / "applications"
            / "rsc"
            / "models"
            / "functional_assignment_evidence.py"
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
            {"dataclasses", "datetime", "enum", "uuid"},
        )

    def test_model_does_not_generate_uuid(self):
        path = (
            Path(__file__).parents[1]
            / "applications"
            / "rsc"
            / "models"
            / "functional_assignment_evidence.py"
        )
        tree = ast.parse(path.read_text(encoding="utf-8"))
        imported_names = {
            alias.name
            for node in ast.walk(tree)
            if isinstance(node, (ast.Import, ast.ImportFrom))
            for alias in node.names
        }

        self.assertNotIn("uuid4", imported_names)

    def test_exports_new_types_and_preserves_existing_exports(self):
        self.assertTrue(FunctionalAssignmentEvidence)
        self.assertTrue(FunctionalAssignmentEvidenceId)
        self.assertTrue(FunctionalAssignmentEvidenceStatus)
        self.assertTrue(SourceEvidenceReference)
        self.assertTrue(Activity)
        self.assertTrue(FunctionalExercise)
        self.assertTrue(Project)


if __name__ == "__main__":
    unittest.main()
