from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError
from pathlib import Path
import unittest

from applications import RscApplication
from contracts import ApplicationDescriptor, Version
from core.application_registry import (
    ApplicationRegistry,
    DuplicateApplicationError,
)


ROOT = Path(__file__).resolve().parents[1]


def descriptor(application_id: str) -> ApplicationDescriptor:
    return ApplicationDescriptor(
        application_id=application_id,
        display_name=application_id.title(),
        version=Version(1, 0, 0),
        minimum_platform_version=Version(1, 0, 0),
        description=f"Application {application_id}.",
        author="Test Author",
        services=("example_service",),
        views=("example_view",),
        commands=("example_command",),
        provided_capabilities=frozenset({"example"}),
    )


class FakeApplication:
    def __init__(self, application_id: str) -> None:
        self.descriptor = descriptor(application_id)
        self.application_id = self.descriptor.application_id
        self.display_name = self.descriptor.display_name

    def prepare(self, context: object) -> None:
        pass

    def create_session(self, context: object) -> object:
        return object()

    def contributions(self, session: object = None) -> tuple[object, ...]:
        return ()

    def transition(self, transition: object) -> None:
        pass

    def dispose(self) -> None:
        pass


class ApplicationHostTests(unittest.TestCase):
    def test_descriptor_is_complete_and_immutable(self):
        value = descriptor("example")

        self.assertEqual(value.application_id, "example")
        self.assertEqual(value.display_name, "Example")
        self.assertEqual(value.author, "Test Author")
        self.assertEqual(value.services, ("example_service",))
        self.assertEqual(value.views, ("example_view",))
        self.assertEqual(value.commands, ("example_command",))
        self.assertEqual(value.provided_capabilities, frozenset({"example"}))
        with self.assertRaises(FrozenInstanceError):
            value.display_name = "Changed"

    def test_registers_and_recovers_application(self):
        application = FakeApplication("example")
        registry = ApplicationRegistry()

        registry.register(application)

        self.assertIs(registry.get("example"), application)
        self.assertIs(registry.get_module("example"), application)
        self.assertIs(
            registry.get_descriptor("example"),
            application.descriptor,
        )

    def test_lists_multiple_applications_as_descriptors(self):
        registry = ApplicationRegistry((
            FakeApplication("zeta"),
            FakeApplication("alpha"),
        ))

        self.assertEqual(
            tuple(item.application_id for item in registry.list()),
            ("alpha", "zeta"),
        )
        self.assertTrue(all(
            isinstance(item, ApplicationDescriptor)
            for item in registry.list()
        ))

    def test_rejects_duplicate_ids(self):
        registry = ApplicationRegistry((FakeApplication("example"),))

        with self.assertRaises(DuplicateApplicationError):
            registry.register(FakeApplication("example"))

    def test_rsc_is_only_a_registered_application(self):
        application = RscApplication()
        registry = ApplicationRegistry((application,))

        self.assertIs(registry.get("rsc"), application)
        self.assertEqual(registry.list(), (application.descriptor,))
        self.assertEqual(application.descriptor.author, "ProcDocOrganizer")
        self.assertEqual(
            application.descriptor.provided_capabilities,
            frozenset({"rsc"}),
        )

    def test_platform_host_has_no_rsc_dependencies(self):
        paths = (
            ROOT / "core" / "application_registry.py",
            ROOT / "core" / "application_lifecycle_host.py",
            ROOT / "core" / "application_runtime.py",
            ROOT / "core" / "project_session_factory.py",
        )
        forbidden = (
            "applications.rsc",
            "criterion",
            "execution_fact",
            "scoring_kernel",
            "normative_catalog",
        )
        for path in paths:
            with self.subTest(path=path.name):
                tree = ast.parse(path.read_text(encoding="utf-8"))
                imports = {
                    alias.name.lower()
                    for node in ast.walk(tree)
                    if isinstance(node, ast.Import)
                    for alias in node.names
                }
                imports.update(
                    (node.module or "").lower()
                    for node in ast.walk(tree)
                    if isinstance(node, ast.ImportFrom)
                )
                self.assertFalse(any(
                    marker in imported
                    for imported in imports
                    for marker in forbidden
                ))


if __name__ == "__main__":
    unittest.main()
