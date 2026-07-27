from dataclasses import FrozenInstanceError
from pathlib import Path
import unittest

from contracts.application_descriptor import (
    ApplicationDescriptor,
    Version,
)


class ApplicationDescriptorContractTests(unittest.TestCase):
    def descriptor(self, **changes):
        values = {
            "application_id": "audit.patrimonial",
            "display_name": "Auditoria Patrimonial",
            "version": Version(1, 2, 0),
            "minimum_platform_version": Version(1, 0, 0),
            "supported_project_schema_versions": (3, 1, 2),
            "required_capabilities": {"platform.document_engine"},
            "provided_capabilities": {"audit.inventory"},
            "description": "Auditoria de bens patrimoniais",
        }
        values.update(changes)
        return ApplicationDescriptor(**values)

    def test_is_passive_immutable_and_normalizes_collections(self):
        descriptor = self.descriptor()

        self.assertEqual(descriptor.application_id, "audit.patrimonial")
        self.assertEqual(descriptor.display_name, "Auditoria Patrimonial")
        self.assertEqual(
            descriptor.description,
            "Auditoria de bens patrimoniais",
        )
        self.assertEqual(
            descriptor.supported_project_schema_versions,
            (1, 2, 3),
        )
        self.assertIsInstance(descriptor.required_capabilities, frozenset)
        self.assertIsInstance(descriptor.provided_capabilities, frozenset)
        with self.assertRaises(FrozenInstanceError):
            descriptor.display_name = "Outro"

    def test_version_parsing_string_and_comparison(self):
        current = Version.parse("1.4.2")

        self.assertEqual(str(current), "1.4.2")
        self.assertLess(Version(1, 4, 1), current)
        self.assertLess(current, Version(2, 0, 0))
        self.assertEqual(Version.parse(str(current)), current)

    def test_rejects_invalid_versions(self):
        for value in ("1", "1.2", "01.2.3", "1.2.-1", "v1.2.3", ""):
            with self.subTest(value=value), self.assertRaises(ValueError):
                Version.parse(value)
        with self.assertRaises(TypeError):
            Version.parse(1)
        with self.assertRaises(ValueError):
            Version(1, -1, 0)
        with self.assertRaises(TypeError):
            Version(True, 0, 0)

    def test_validates_identity_name_schema_and_capabilities(self):
        invalid = (
            {"application_id": "invalid id"},
            {"display_name": "   "},
            {"supported_project_schema_versions": (1, 1)},
            {"supported_project_schema_versions": (0,)},
            {"required_capabilities": {"Invalid Capability"}},
            {"provided_capabilities": {1}},
            {"description": None},
        )
        for changes in invalid:
            with self.subTest(changes=changes), self.assertRaises(
                (TypeError, ValueError)
            ):
                self.descriptor(**changes)

    def test_preserves_legacy_mixed_case_application_identity(self):
        descriptor = self.descriptor(
            application_id="ProcDocOrganizer"
        )

        self.assertEqual(
            descriptor.application_id,
            "ProcDocOrganizer",
        )

    def test_contract_has_no_ui_rsc_or_runtime_dependencies(self):
        source = (
            Path(__file__).parents[1]
            / "contracts"
            / "application_descriptor.py"
        ).read_text(encoding="utf-8")

        for forbidden in (
            "PySide6",
            "applications.rsc",
            "ProjectSession",
            "Repository",
            "Controller",
            "View",
            "Service",
        ):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, source)


if __name__ == "__main__":
    unittest.main()
