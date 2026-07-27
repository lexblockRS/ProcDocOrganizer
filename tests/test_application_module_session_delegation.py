from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from applications import RscApplication
from contracts import ApplicationDescriptor, Version
from core.application_registry import ApplicationRegistry
from core.project_manager import ProjectManager
from core.project_session import ProjectSession
from core.project_session_factory import ProjectSessionFactory
from core.session_context import SessionContext


class ModularApplicationDouble:
    def __init__(self, application_id="modular", failure=None):
        self.descriptor = ApplicationDescriptor(
            application_id=application_id,
            display_name="Modular",
            version=Version(1, 0, 0),
            minimum_platform_version=Version(1, 0, 0),
            supported_project_schema_versions=(1,),
        )
        self.failure = failure
        self.create_session_calls = []
        self.created_session = object()

    def prepare(self, context):
        pass

    def create_session(self, context):
        self.create_session_calls.append(context)
        if self.failure is not None:
            raise self.failure
        return self.created_session

    def contributions(self, session):
        return ()

    def transition(self, transition):
        pass

    def dispose(self):
        pass


class LegacyApplicationDouble:
    application_id = "legacy-test"
    display_name = "Legacy Test"

    def __init__(self):
        self.create_session_calls = 0

    def can_open(self, project):
        return project.application == self.application_id

    def contributions(self):
        return ()

    def create_session(self, context):
        self.create_session_calls += 1
        return object()


class ApplicationModuleSessionDelegationTests(unittest.TestCase):
    def _project(self, temporary, application_id):
        return ProjectManager().create_project(
            "Delegation",
            Path(temporary),
            application_id=application_id,
        )

    def test_factory_delegates_once_and_stores_application_session(self):
        with TemporaryDirectory() as temporary:
            module = ModularApplicationDouble()
            project = self._project(temporary, module.descriptor.application_id)

            session = ProjectSessionFactory(
                ApplicationRegistry([module])
            ).create(project)

            self.assertIsInstance(session, ProjectSession)
            self.assertEqual(len(module.create_session_calls), 1)
            self.assertIsInstance(
                module.create_session_calls[0],
                SessionContext,
            )
            self.assertIs(
                session.platform_session
                .application_runtime.application_session,
                module.created_session,
            )
            self.assertIsNone(session.rsc_session)

    def test_legacy_application_does_not_delegate_create_session(self):
        with TemporaryDirectory() as temporary:
            application = LegacyApplicationDouble()
            project = self._project(temporary, application.application_id)

            session = ProjectSessionFactory(
                ApplicationRegistry([application])
            ).create(project)

            self.assertEqual(application.create_session_calls, 0)
            self.assertIsNone(
                session.platform_session
                .application_runtime.application_session
            )

    def test_rsc_uses_modular_creation_path_and_compatibility_alias(self):
        with TemporaryDirectory() as temporary:
            application = RscApplication()
            project = self._project(temporary, application.application_id)
            factory = ProjectSessionFactory(
                ApplicationRegistry([application])
            )

            session = factory.create(project)

            self.assertIsNotNone(session.rsc_session)
            self.assertIs(
                session.platform_session
                .application_runtime.application_session,
                session.rsc_session,
            )
            self.assertIs(
                factory._application_registry.resolve_module(project),
                application,
            )

    def test_create_session_failure_does_not_return_partial_session(self):
        with TemporaryDirectory() as temporary:
            failure = RuntimeError("session creation failed")
            module = ModularApplicationDouble(failure=failure)
            project = self._project(temporary, module.descriptor.application_id)
            factory = ProjectSessionFactory(
                ApplicationRegistry([module])
            )

            with self.assertRaisesRegex(
                RuntimeError,
                "session creation failed",
            ):
                factory.create(project)

            self.assertEqual(len(module.create_session_calls), 1)


if __name__ == "__main__":
    unittest.main()
