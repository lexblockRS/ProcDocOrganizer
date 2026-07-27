import ast
from pathlib import Path
import unittest

from contracts import ApplicationDescriptor, Version
from core.application_registry import (
    ApplicationNotRegisteredError,
    ApplicationRegistry,
    DuplicateApplicationError,
    IncompatibleApplicationError,
)
from models import Project


def project(application_id="module.example", format_version=1):
    return Project(
        project_name="Projeto",
        project_path=Path("project.pdop"),
        created_at="2026-07-28T10:00:00",
        last_opened_at="2026-07-28T10:00:00",
        application=application_id,
        format_version=format_version,
    )


def descriptor(
    application_id="module.example",
    display_name="Module Example",
    *,
    version=Version(1, 2, 0),
    minimum_platform_version=Version(1, 0, 0),
    schemas=(1,),
):
    return ApplicationDescriptor(
        application_id=application_id,
        display_name=display_name,
        version=version,
        minimum_platform_version=minimum_platform_version,
        supported_project_schema_versions=schemas,
        required_capabilities={"platform.document_engine"},
        provided_capabilities={"module.example"},
    )


class ModuleDouble:
    def __init__(
        self,
        module_descriptor=None,
        *,
        declared_id=None,
        declared_name=None,
    ):
        self.descriptor = module_descriptor or descriptor()
        if declared_id is not None:
            self.application_id = declared_id
        if declared_name is not None:
            self.display_name = declared_name
        self.prepare_calls = 0
        self.session_calls = 0
        self.contribution_calls = 0
        self.transition_calls = 0
        self.dispose_calls = 0

    def prepare(self, context):
        self.prepare_calls += 1

    def create_session(self, context):
        self.session_calls += 1
        return object()

    def contributions(self, session):
        self.contribution_calls += 1
        return ()

    def transition(self, transition):
        self.transition_calls += 1

    def dispose(self):
        self.dispose_calls += 1


class LegacyApplication:
    def __init__(
        self,
        application_id="legacy.example",
        display_name="Legacy Example",
    ):
        self.application_id = application_id
        self.display_name = display_name
        self.checked_projects = []
        self.contribution_calls = 0

    def can_open(self, candidate):
        self.checked_projects.append(candidate)
        return candidate.application == self.application_id

    def contributions(self):
        self.contribution_calls += 1
        return ()


class ApplicationModuleRegistryTests(unittest.TestCase):
    def test_registers_module_and_preserves_official_descriptor_identity(self):
        module = ModuleDouble()
        registry = ApplicationRegistry()

        registry.register_module(module)

        self.assertIs(
            registry.get_descriptor(module.descriptor.application_id),
            module.descriptor,
        )
        self.assertIs(
            registry.get_module(module.descriptor.application_id),
            module,
        )
        self.assertIs(
            registry.get(module.descriptor.application_id),
            module,
        )
        self.assertEqual(registry.modules, (module,))
        self.assertEqual(registry.descriptors, (module.descriptor,))
        self.assertEqual(registry.applications, ())

    def test_generic_register_recognizes_module_structurally(self):
        module = ModuleDouble()
        registry = ApplicationRegistry([module])

        self.assertIs(registry.resolve_module(project()), module)
        self.assertIs(registry.resolve(project()), module)
        self.assertEqual(module.prepare_calls, 0)
        self.assertEqual(module.session_calls, 0)
        self.assertEqual(module.contribution_calls, 0)
        self.assertEqual(module.transition_calls, 0)
        self.assertEqual(module.dispose_calls, 0)

    def test_legacy_api_and_transitional_descriptor_are_preserved(self):
        application = LegacyApplication()
        registry = ApplicationRegistry([application])

        self.assertEqual(registry.applications, (application,))
        self.assertEqual(registry.modules, ())
        self.assertIs(registry.get(application.application_id), application)
        self.assertIs(registry.resolve(project("legacy.example")), application)
        transitional = registry.get_descriptor(
            application.application_id
        )
        self.assertEqual(
            transitional.application_id,
            application.application_id,
        )
        self.assertEqual(
            transitional.display_name,
            application.display_name,
        )
        self.assertEqual(transitional.version, Version(0, 0, 0))
        self.assertEqual(
            transitional.minimum_platform_version,
            Version(0, 0, 0),
        )
        self.assertEqual(
            transitional.supported_project_schema_versions,
            (1,),
        )
        self.assertEqual(application.contribution_calls, 0)

    def test_legacy_declared_versions_are_preserved(self):
        application = LegacyApplication()
        application.version = "2.3.4"
        application.minimum_platform_version = Version(1, 0, 0)
        application.supported_project_schema_versions = (1, 2)

        registered = ApplicationRegistry([application]).get_descriptor(
            application.application_id
        )

        self.assertEqual(registered.version, Version(2, 3, 4))
        self.assertEqual(
            registered.minimum_platform_version,
            Version(1, 0, 0),
        )
        self.assertEqual(
            registered.supported_project_schema_versions,
            (1, 2),
        )

    def test_aliases_resolve_to_the_same_canonical_entry(self):
        application = LegacyApplication()
        registry = ApplicationRegistry()
        registry.register(application, aliases=("legacy.old",))

        self.assertIs(registry.get("legacy.old"), application)
        self.assertIs(
            registry.get_descriptor("legacy.old"),
            registry.get_descriptor("legacy.example"),
        )
        self.assertIs(
            registry.resolve(project("legacy.old")),
            application,
        )
        self.assertEqual(
            application.checked_projects[-1].application,
            "legacy.example",
        )

    def test_historical_identifier_keeps_existing_resolution(self):
        registry = ApplicationRegistry()
        self.assertIsNone(registry.resolve(project("ProcDocOrganizer")))

        application = LegacyApplication(
            "ProcDocOrganizer",
            "ProcDocOrganizer",
        )
        registry.register(application)

        self.assertIs(
            registry.resolve(project("ProcDocOrganizer")),
            application,
        )
        self.assertEqual(
            registry.get_descriptor("ProcDocOrganizer").application_id,
            application.application_id,
        )

    def test_rejects_duplicate_ids_same_object_and_alias_collisions(self):
        application = LegacyApplication()
        registry = ApplicationRegistry()
        registry.register(application, aliases=("legacy.old",))

        for operation in (
            lambda: registry.register(application),
            lambda: registry.register(
                LegacyApplication("legacy.old")
            ),
            lambda: registry.register(
                LegacyApplication("other"),
                aliases=("legacy.example",),
            ),
            lambda: registry.register(
                LegacyApplication("historical"),
                aliases=("ProcDocOrganizer",),
            ),
        ):
            with self.subTest(operation=operation):
                with self.assertRaises(DuplicateApplicationError):
                    operation()

    def test_rejects_empty_id_and_divergent_module_descriptor(self):
        with self.assertRaises(ValueError):
            ApplicationRegistry([LegacyApplication(" ")])

        module = ModuleDouble(declared_id="different")
        with self.assertRaisesRegex(ValueError, "diverge"):
            ApplicationRegistry([module])

    def test_rejects_incompatible_minimum_platform_version(self):
        module = ModuleDouble(descriptor(
            minimum_platform_version=Version(2, 0, 0)
        ))

        with self.assertRaises(IncompatibleApplicationError):
            ApplicationRegistry(
                [module],
                platform_version=Version(1, 9, 9),
            )

    def test_defensively_rejects_invalid_schema_and_capability_shapes(self):
        invalid_schema = descriptor()
        object.__setattr__(
            invalid_schema,
            "supported_project_schema_versions",
            (0,),
        )
        with self.assertRaises(ValueError):
            ApplicationRegistry([ModuleDouble(invalid_schema)])

        mutable_capabilities = descriptor()
        object.__setattr__(
            mutable_capabilities,
            "required_capabilities",
            ["platform.document_engine"],
        )
        with self.assertRaises(TypeError):
            ApplicationRegistry([ModuleDouble(mutable_capabilities)])

    def test_rejects_project_schema_and_unknown_id_explicitly(self):
        module = ModuleDouble(descriptor(schemas=(2,)))
        registry = ApplicationRegistry([module])

        with self.assertRaises(IncompatibleApplicationError):
            registry.resolve_module(project(format_version=1))
        with self.assertRaises(ApplicationNotRegisteredError):
            registry.resolve(project("unknown"))

    def test_listing_and_resolution_are_deterministic(self):
        alpha = ModuleDouble(descriptor("alpha", "Alpha"))
        middle = LegacyApplication("middle", "Middle")
        zulu = ModuleDouble(descriptor("zulu", "Zulu"))
        first = ApplicationRegistry([zulu, middle, alpha])
        second = ApplicationRegistry([alpha, middle, zulu])

        self.assertEqual(
            tuple(item.application_id for item in first.descriptors),
            ("alpha", "middle", "zulu"),
        )
        self.assertEqual(
            first.descriptors,
            second.descriptors,
        )
        self.assertIs(first.resolve_module(project("alpha")), alpha)
        self.assertIs(first.resolve(project("middle")), middle)

    def test_registry_has_no_forbidden_imports_or_session_creation(self):
        path = (
            Path(__file__).parents[1]
            / "core"
            / "application_registry.py"
        )
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source)
        imports = {
            alias.name
            for node in ast.walk(tree)
            if isinstance(node, ast.Import)
            for alias in node.names
        }
        imports.update(
            node.module or ""
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom)
        )

        for forbidden in (
            "PySide6",
            "applications.rsc",
            "presentation",
            "ui",
            "sqlite",
            "repositories",
            "project_session_factory",
            "controllers",
            "views",
            "dialogs",
        ):
            with self.subTest(forbidden=forbidden):
                self.assertFalse(
                    any(
                        forbidden.lower() in imported.lower()
                        for imported in imports
                    )
                )
        self.assertNotIn(".create_session(", source)


if __name__ == "__main__":
    unittest.main()
