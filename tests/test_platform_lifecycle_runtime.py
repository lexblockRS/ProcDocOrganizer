from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from contracts import ApplicationDescriptor, ApplicationLifecycleState, Version
from core.application_registry import ApplicationRegistry
from core.project_manager import ProjectManager
from core.project_session_factory import ProjectSessionFactory


class LifecycleModule:
    def __init__(
        self,
        *,
        prepare_failure=None,
        session_failure=None,
        dispose_failure=None,
        transition_failure=None,
    ):
        self.descriptor = ApplicationDescriptor(
            application_id="lifecycle.test",
            display_name="Lifecycle Test",
            version=Version(1, 0, 0),
            minimum_platform_version=Version(1, 0, 0),
            supported_project_schema_versions=(1,),
        )
        self.prepare_failure = prepare_failure
        self.session_failure = session_failure
        self.dispose_failure = dispose_failure
        self.transition_failure = transition_failure
        self.calls = []
        self.created_session = object()

    def prepare(self, context):
        self.calls.append(("prepare", context))
        if self.prepare_failure is not None:
            raise self.prepare_failure

    def create_session(self, context):
        self.calls.append(("create_session", context))
        if self.session_failure is not None:
            raise self.session_failure
        return self.created_session

    def contributions(self, session):
        return ()

    def transition(self, transition):
        self.calls.append(
            ("transition", transition.source, transition.target)
        )
        if self.transition_failure is not None:
            raise self.transition_failure

    def dispose(self):
        self.calls.append(("dispose",))
        if self.dispose_failure is not None:
            raise self.dispose_failure


class PlatformLifecycleRuntimeTests(unittest.TestCase):
    def create(self, module):
        temporary = TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        project = ProjectManager().create_project(
            "Lifecycle",
            Path(temporary.name),
            application_id=module.descriptor.application_id,
        )
        factory = ProjectSessionFactory(ApplicationRegistry([module]))
        return factory.create(project)

    def test_factory_prepares_then_creates_and_publishes_session(self):
        module = LifecycleModule()

        session = self.create(module)
        runtime = session.platform_session.application_runtime

        self.assertEqual(
            [call[0] for call in module.calls],
            ["prepare", "transition", "create_session", "transition"],
        )
        self.assertIs(
            runtime.application_session,
            module.created_session,
        )
        self.assertEqual(
            runtime.lifecycle_state,
            ApplicationLifecycleState.SESSION_CREATED,
        )

    def test_activation_and_disposal_follow_complete_order(self):
        module = LifecycleModule()
        session = self.create(module)
        runtime = session.platform_session.application_runtime

        runtime.activate()
        runtime.dispose()
        runtime.dispose()

        targets = [
            call[2]
            for call in module.calls
            if call[0] == "transition"
        ]
        self.assertEqual(
            targets,
            [
                ApplicationLifecycleState.PROJECT_PREPARED,
                ApplicationLifecycleState.SESSION_CREATED,
                ApplicationLifecycleState.PRESENTATION_MOUNTED,
                ApplicationLifecycleState.ACTIVE,
                ApplicationLifecycleState.DEACTIVATING,
                ApplicationLifecycleState.DISPOSED,
            ],
        )
        self.assertEqual(
            [call for call in module.calls if call[0] == "dispose"],
            [("dispose",)],
        )
        self.assertIsNone(runtime.application_session)
        self.assertEqual(
            runtime.lifecycle_state,
            ApplicationLifecycleState.DISPOSED,
        )

    def test_prepare_failure_does_not_create_or_publish_session(self):
        module = LifecycleModule(
            prepare_failure=RuntimeError("prepare failed")
        )

        with self.assertRaisesRegex(RuntimeError, "prepare failed"):
            self.create(module)

        self.assertEqual(
            [call[0] for call in module.calls],
            ["prepare"],
        )

    def test_session_failure_disposes_prepared_module(self):
        module = LifecycleModule(
            session_failure=RuntimeError("session failed")
        )

        with self.assertRaisesRegex(RuntimeError, "session failed"):
            self.create(module)

        self.assertEqual(
            [call[0] for call in module.calls],
            [
                "prepare",
                "transition",
                "create_session",
                "dispose",
                "transition",
            ],
        )

    def test_dispose_failure_is_contained_and_runtime_is_consistent(self):
        module = LifecycleModule(
            dispose_failure=RuntimeError("dispose failed")
        )
        runtime = self.create(module).platform_session.application_runtime
        runtime.activate()

        with self.assertLogs(
            "core.application_runtime", level="ERROR"
        ):
            runtime.dispose()

        self.assertEqual(
            runtime.lifecycle_state,
            ApplicationLifecycleState.DISPOSED,
        )
        self.assertIsNone(runtime.application_session)

    def test_invalid_or_repeated_operations_are_rejected(self):
        module = LifecycleModule()
        runtime = self.create(module).platform_session.application_runtime

        with self.assertRaises(RuntimeError):
            runtime.prepare(object())
        with self.assertRaises(RuntimeError):
            runtime.create_session(object())
        runtime.activate()
        with self.assertRaises(RuntimeError):
            runtime.activate()

    def test_transition_failure_is_logged_without_corrupting_runtime(self):
        module = LifecycleModule(
            transition_failure=RuntimeError("transition failed")
        )

        with self.assertLogs(
            "core.application_runtime", level="ERROR"
        ):
            runtime = self.create(
                module
            ).platform_session.application_runtime
            runtime.activate()
            runtime.dispose()

        self.assertEqual(
            runtime.lifecycle_state,
            ApplicationLifecycleState.DISPOSED,
        )


if __name__ == "__main__":
    unittest.main()
