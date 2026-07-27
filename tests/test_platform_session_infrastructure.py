from dataclasses import FrozenInstanceError
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from contracts.application_descriptor import (
    ApplicationDescriptor,
    Version,
)
from contracts.capabilities import (
    CLOCK_CAPABILITY,
    NAVIGATION_CAPABILITY,
)
from contracts.lifecycle import ApplicationLifecycleState
from core.application_runtime import ApplicationRuntime
from core.platform_session import PlatformSession
from core.project_context import ProjectContext
from core.session_context import SessionContext


class ModuleDouble:
    def __init__(self, descriptor):
        self.descriptor = descriptor

    def prepare(self, context):
        pass

    def create_session(self, context):
        return object()

    def contributions(self, session):
        return ()

    def transition(self, transition):
        pass

    def dispose(self):
        pass


class NavigationDouble:
    capability_id = NAVIGATION_CAPABILITY

    def navigate(self, destination, parameters=None):
        return True


class ClockDouble:
    capability_id = CLOCK_CAPABILITY


class ProviderDouble:
    def __init__(self, capability):
        self.capability = capability

    @property
    def capability_ids(self):
        return frozenset({self.capability.capability_id})

    def get_capability(self, capability_id):
        if capability_id != self.capability.capability_id:
            raise KeyError(capability_id)
        return self.capability


class PlatformSessionInfrastructureTests(unittest.TestCase):
    def setUp(self):
        self.descriptor = ApplicationDescriptor(
            application_id="example",
            display_name="Example",
            version=Version(1, 0, 0),
            minimum_platform_version=Version(1, 0, 0),
        )

    def project_context(self, project, path):
        return ProjectContext(
            project=project,
            application_id="example",
            project_path=path,
            project_version=1,
            permanent_metadata={"created_at": "2026-07-27"},
        )

    def session_context(self):
        clock = ClockDouble()
        return SessionContext(
            document_engine=object(),
            knowledge_engine=object(),
            navigation=NavigationDouble(),
            shared_services={"clock": clock},
            capability_provider=ProviderDouble(clock),
        )

    def runtime(self):
        return ApplicationRuntime(
            descriptor=self.descriptor,
            module=ModuleDouble(self.descriptor),
            lifecycle_state=ApplicationLifecycleState.REGISTERED,
        )

    def test_project_context_is_passive_immutable_and_defensive(self):
        with TemporaryDirectory() as temporary:
            project = object()
            metadata = {"owner": "platform"}
            context = ProjectContext(
                project=project,
                application_id=" example ",
                project_path=Path(temporary),
                project_version=1,
                permanent_metadata=metadata,
            )
            metadata["owner"] = "changed"

            self.assertIs(context.project, project)
            self.assertEqual(context.application_id, "example")
            self.assertEqual(context.permanent_metadata["owner"], "platform")
            with self.assertRaises(TypeError):
                context.permanent_metadata["owner"] = "changed"
            with self.assertRaises(FrozenInstanceError):
                context.project_version = 2

    def test_project_context_validates_permanent_identity(self):
        with TemporaryDirectory() as temporary:
            path = Path(temporary)
            invalid = (
                {"project": None},
                {"application_id": " "},
                {"project_path": str(path)},
                {"project_version": 0},
                {"permanent_metadata": {"": "value"}},
            )
            for changes in invalid:
                values = {
                    "project": object(),
                    "application_id": "example",
                    "project_path": path,
                    "project_version": 1,
                    "permanent_metadata": {},
                }
                values.update(changes)
                with self.subTest(changes=changes), self.assertRaises(
                    (TypeError, ValueError)
                ):
                    ProjectContext(**values)

    def test_session_context_preserves_resource_identity_and_mapping(self):
        document_engine = object()
        knowledge_engine = object()
        service = object()
        services = {"shared": service}
        context = SessionContext(
            document_engine=document_engine,
            knowledge_engine=knowledge_engine,
            navigation=NavigationDouble(),
            shared_services=services,
        )
        services["other"] = object()

        self.assertIs(context.document_engine, document_engine)
        self.assertIs(context.knowledge_engine, knowledge_engine)
        self.assertIs(context.shared_services["shared"], service)
        self.assertNotIn("other", context.shared_services)
        with self.assertRaises(TypeError):
            context.shared_services["other"] = object()
        with self.assertRaises(FrozenInstanceError):
            context.document_engine = object()

    def test_session_context_accepts_neutral_capability_provider(self):
        context = self.session_context()

        self.assertEqual(
            context.capability_provider.capability_ids,
            frozenset({CLOCK_CAPABILITY}),
        )
        self.assertTrue(context.navigation.navigate("platform://home"))

    def test_application_runtime_starts_without_application_session(self):
        runtime = self.runtime()

        self.assertIs(runtime.descriptor, self.descriptor)
        self.assertIs(runtime.module.descriptor, self.descriptor)
        self.assertEqual(
            runtime.lifecycle_state,
            ApplicationLifecycleState.REGISTERED,
        )
        self.assertIsNone(runtime.application_session)

    def test_application_runtime_allows_temporarily_unavailable_module(self):
        runtime = ApplicationRuntime(
            descriptor=self.descriptor,
            module=None,
            lifecycle_state=ApplicationLifecycleState.REGISTERED,
        )

        self.assertIsNone(runtime.module)
        self.assertIsNone(runtime.application_session)

    def test_application_runtime_can_hold_future_session_identity(self):
        runtime = self.runtime()
        future_session = object()

        runtime.application_session = future_session
        runtime.lifecycle_state = ApplicationLifecycleState.SESSION_CREATED

        self.assertIs(runtime.application_session, future_session)
        self.assertEqual(
            runtime.lifecycle_state,
            ApplicationLifecycleState.SESSION_CREATED,
        )

    def test_application_runtime_rejects_mismatched_descriptor(self):
        other = ApplicationDescriptor(
            application_id="other",
            display_name="Other",
            version=Version(1, 0, 0),
            minimum_platform_version=Version(1, 0, 0),
        )

        with self.assertRaises(ValueError):
            ApplicationRuntime(
                descriptor=self.descriptor,
                module=ModuleDouble(other),
                lifecycle_state=ApplicationLifecycleState.REGISTERED,
            )

    def test_platform_session_composes_exact_internal_objects(self):
        with TemporaryDirectory() as temporary:
            project = object()
            project_context = self.project_context(
                project,
                Path(temporary),
            )
            session_context = self.session_context()
            runtime = self.runtime()

            session = PlatformSession(
                project_context=project_context,
                session_context=session_context,
                application_runtime=runtime,
            )

            self.assertIs(session.project_context, project_context)
            self.assertIs(session.session_context, session_context)
            self.assertIs(session.application_runtime, runtime)
            with self.assertRaises(FrozenInstanceError):
                session.project_context = project_context

    def test_new_infrastructure_has_no_forbidden_dependencies(self):
        root = Path(__file__).parents[1]
        files = (
            root / "core" / "project_context.py",
            root / "core" / "session_context.py",
            root / "core" / "application_runtime.py",
            root / "core" / "platform_session.py",
        )
        forbidden = (
            "PySide6",
            "applications.rsc",
            "project_session",
            "sqlite",
            "Repository",
            "Controller",
            "View",
            "Factory",
        )

        for path in files:
            source = path.read_text(encoding="utf-8")
            for dependency in forbidden:
                with self.subTest(path=path.name, dependency=dependency):
                    self.assertNotIn(dependency, source)


if __name__ == "__main__":
    unittest.main()
