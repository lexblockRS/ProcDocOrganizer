import ast
from dataclasses import FrozenInstanceError, fields
from datetime import date
from pathlib import Path
from uuid import UUID
import unittest

from applications.rsc.assemblers import (
    FunctionalAssignmentEvidenceAssembler,
)
from applications.rsc.commands import (
    CreateFunctionalAssignmentEvidenceCommand,
)
from applications.rsc.dto import FunctionalExerciseDTO
from applications.rsc.models import (
    FunctionalAssignmentEvidence,
    FunctionalAssignmentEvidenceId,
    FunctionalAssignmentEvidenceStatus,
    FunctionalExercise,
    SourceEvidenceReference,
)


def command(**changes):
    values = {
        "person_id": "person-1",
        "source_evidence_reference": "external:evidence-1",
        "exercise_type_code": "fiscal_contrato",
        "exercise_type_label": "Fiscalização de contrato",
        "role": "Fiscal titular",
        "organization": "Instituição",
    }
    values.update(changes)
    return CreateFunctionalAssignmentEvidenceCommand(**values)


class CreateFunctionalAssignmentEvidenceCommandTests(unittest.TestCase):
    def test_creates_with_required_fields(self):
        request = command()

        self.assertEqual(request.person_id, "person-1")
        self.assertIsNone(request.start_date)
        self.assertIsNone(request.end_date)

    def test_creates_with_all_fields(self):
        request = command(
            start_date=date(2024, 1, 1),
            end_date=date(2024, 12, 31),
            unit="Unidade",
            administrative_reference="Portaria 123",
        )

        self.assertEqual(request.start_date, date(2024, 1, 1))
        self.assertEqual(request.end_date, date(2024, 12, 31))
        self.assertEqual(request.unit, "Unidade")
        self.assertEqual(
            request.administrative_reference,
            "Portaria 123",
        )

    def test_preserves_primitive_values_without_normalizing(self):
        request = command(
            person_id=" person-1 ",
            source_evidence_reference=" external:ABC ",
            role=" Fiscal   titular ",
        )

        self.assertEqual(request.person_id, " person-1 ")
        self.assertEqual(
            request.source_evidence_reference,
            " external:ABC ",
        )
        self.assertEqual(request.role, " Fiscal   titular ")

    def test_accepts_only_start_date(self):
        request = command(start_date=date(2024, 1, 1))

        self.assertEqual(request.start_date, date(2024, 1, 1))
        self.assertIsNone(request.end_date)

    def test_accepts_only_end_date(self):
        request = command(end_date=date(2024, 12, 31))

        self.assertIsNone(request.start_date)
        self.assertEqual(request.end_date, date(2024, 12, 31))

    def test_is_immutable(self):
        request = command()

        with self.assertRaises(FrozenInstanceError):
            request.role = "Outro"

    def test_has_no_id_or_status(self):
        field_names = {field.name for field in fields(command())}

        self.assertNotIn("id", field_names)
        self.assertNotIn("status", field_names)

    def test_contains_no_domain_value_objects(self):
        request = command()

        for field in fields(request):
            value = getattr(request, field.name)
            if value is not None:
                self.assertFalse(
                    value.__class__.__module__.startswith(
                        "applications.rsc.models"
                    )
                )


class FunctionalAssignmentEvidenceAssemblerTests(unittest.TestCase):
    def setUp(self):
        self.assembler = FunctionalAssignmentEvidenceAssembler()

    def test_accepts_command_and_returns_domain_entity(self):
        item = self.assembler.assemble(command())

        self.assertIsInstance(item, FunctionalAssignmentEvidence)
        self.assertNotIsInstance(item, FunctionalExercise)
        self.assertNotIsInstance(item, FunctionalExerciseDTO)

    def test_rejects_invalid_command_type(self):
        with self.assertRaises(TypeError):
            self.assembler.assemble(object())

    def test_creates_domain_identity_with_canonical_uuid(self):
        item = self.assembler.assemble(command())

        self.assertIsInstance(item.id, FunctionalAssignmentEvidenceId)
        self.assertEqual(str(UUID(str(item.id))), str(item.id))

    def test_generates_distinct_ids(self):
        first = self.assembler.assemble(command())
        second = self.assembler.assemble(command())

        self.assertNotEqual(first.id, second.id)

    def test_creates_opaque_source_reference(self):
        item = self.assembler.assemble(
            command(source_evidence_reference="scheme://opaque?x=A-1")
        )

        self.assertIsInstance(
            item.source_evidence_reference,
            SourceEvidenceReference,
        )
        self.assertEqual(
            str(item.source_evidence_reference),
            "scheme://opaque?x=A-1",
        )

    def test_projects_all_command_fields(self):
        request = command(
            person_id="person-2",
            source_evidence_reference="external:evidence-2",
            exercise_type_code="gestao",
            exercise_type_label="Gestão",
            role="Presidente",
            organization="Instituto Federal",
            start_date=date(2023, 2, 1),
            end_date=date(2023, 11, 30),
            unit="Conselho",
            administrative_reference="Portaria 123",
        )

        item = self.assembler.assemble(request)

        self.assertEqual(item.person_id, request.person_id)
        self.assertEqual(
            str(item.source_evidence_reference),
            request.source_evidence_reference,
        )
        self.assertEqual(
            item.exercise_type_code,
            request.exercise_type_code,
        )
        self.assertEqual(
            item.exercise_type_label,
            request.exercise_type_label,
        )
        self.assertEqual(item.role, request.role)
        self.assertEqual(item.organization, request.organization)
        self.assertEqual(item.start_date, request.start_date)
        self.assertEqual(item.end_date, request.end_date)
        self.assertEqual(item.unit, request.unit)
        self.assertEqual(
            item.administrative_reference,
            request.administrative_reference,
        )

    def test_creates_entity_in_raw_state_without_transition(self):
        item = self.assembler.assemble(command())

        self.assertIs(
            item.status,
            FunctionalAssignmentEvidenceStatus.RAW,
        )

    def test_does_not_change_command(self):
        request = command(
            person_id=" person-1 ",
            role=" Fiscal   titular ",
        )

        self.assembler.assemble(request)

        self.assertEqual(request.person_id, " person-1 ")
        self.assertEqual(request.role, " Fiscal   titular ")

    def test_propagates_domain_errors(self):
        for field, value, error in (
            ("person_id", " ", ValueError),
            ("source_evidence_reference", " ", ValueError),
            ("role", None, TypeError),
            ("start_date", "2024-01-01", TypeError),
        ):
            with self.subTest(field=field):
                with self.assertRaises(error):
                    self.assembler.assemble(
                        command(**{field: value})
                    )

    def test_propagates_invalid_date_range(self):
        with self.assertRaises(ValueError):
            self.assembler.assemble(
                command(
                    start_date=date(2024, 1, 2),
                    end_date=date(2024, 1, 1),
                )
            )

    def test_requires_no_repository_and_does_not_persist(self):
        item = FunctionalAssignmentEvidenceAssembler().assemble(
            command()
        )

        self.assertIsInstance(item, FunctionalAssignmentEvidence)


class FunctionalAssignmentEvidenceAssemblerArchitectureTests(
    unittest.TestCase
):
    def test_command_has_only_standard_library_dependencies(self):
        imports = self._imports(
            "applications/rsc/commands/"
            "create_functional_assignment_evidence.py"
        )

        self.assertEqual(imports, {"dataclasses", "datetime"})

    def test_assembler_has_only_allowed_dependencies(self):
        imports = self._imports(
            "applications/rsc/assemblers/"
            "functional_assignment_evidence_assembler.py"
        )

        self.assertEqual(
            imports,
            {
                "uuid",
                "applications.rsc.commands",
                "applications.rsc.models",
            },
        )

    def test_public_exports_are_available(self):
        self.assertTrue(CreateFunctionalAssignmentEvidenceCommand)
        self.assertTrue(FunctionalAssignmentEvidenceAssembler)

    @staticmethod
    def _imports(relative_path):
        path = Path(__file__).parents[1] / relative_path
        tree = ast.parse(path.read_text(encoding="utf-8"))
        modules = {
            node.module or ""
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom)
        }
        modules.update(
            alias.name
            for node in ast.walk(tree)
            if isinstance(node, ast.Import)
            for alias in node.names
        )
        return modules


if __name__ == "__main__":
    unittest.main()
