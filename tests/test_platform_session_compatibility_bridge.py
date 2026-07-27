import inspect
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from applications import RscApplication
from applications.rsc import RscProjectSession
from contracts import (
    ApplicationDescriptor,
    ApplicationLifecycleState,
    Version,
)
from core.application_registry import ApplicationRegistry
from core.platform_session import PlatformSession
from core.project_manager import ProjectManager
from core.project_session import ProjectSession
from core.project_session_factory import ProjectSessionFactory
from models.project import LEGACY_APPLICATION_ID


class FutureModuleDouble:
    application_id = "future"
    display_name = "Future"

    def __init__(self):
        self.descriptor = ApplicationDescriptor(
            application_id=self.application_id,
            display_name=self.display_name,
            version=Version(2, 1, 0),
            minimum_platform_version=Version(1, 0, 0),
            supported_project_schema_versions=(1,),
        )

    def can_open(self, project):
        return project.application == self.application_id

    def prepare(self, context):
        pass

    def create_session(self, context):
        return object()

    def contributions(self, session=None):
        return ()

    def transition(self, transition):
        pass

    def dispose(self):
        pass


class PlatformSessionCompatibilityBridgeTests(unittest.TestCase):
    def test_factory_builds_platform_session_automatically(self):
        with TemporaryDirectory() as temporary:
            project = ProjectManager().create_project(
                "Legacy",
                Path(temporary),
            )

            session = ProjectSessionFactory().create(project)

            self.assertIsInstance(session.platform_session, PlatformSession)
            self.assertIs(
                session.platform_session.project_context.project,
                session.project,
            )
            self.assertEqual(
                session.platform_session.project_context.application_id,
                LEGACY_APPLICATION_ID,
            )
            self.assertEqual(
                session.platform_session.project_context.project_path,
                project.project_path,
            )
            self.assertEqual(
                session.platform_session.project_context.project_version,
                project.format_version,
            )
            self.assertEqual(
                dict(
                    session.platform_session
                    .project_context.permanent_metadata
                ),
                {
                    "project_name": project.project_name,
                    "created_at": project.created_at,
                    "database": project.database,
                },
            )

    def test_session_context_reuses_every_existing_shared_dependency(self):
        with TemporaryDirectory() as temporary:
            project = ProjectManager().create_project(
                "Shared",
                Path(temporary),
            )

            session = ProjectSessionFactory().create(project)
            context = session.platform_session.session_context

            self.assertIs(context.document_engine, session.document_service)
            self.assertIs(context.knowledge_engine, session.evidence_service)
            for name in (
                "document_repository",
                "document_service",
                "document_import_service",
                "document_processor",
                "document_indexer",
                "search_service",
                "evidence_service",
            ):
                with self.subTest(name=name):
                    self.assertIs(
                        context.shared_services[name],
                        getattr(session, name),
                    )
            self.assertIsNone(context.navigation)
            self.assertIsNone(context.capability_provider)

    def test_legacy_runtime_uses_faithful_compatibility_descriptor(self):
        with TemporaryDirectory() as temporary:
            project = ProjectManager().create_project(
                "Legacy",
                Path(temporary),
            )

            runtime = (
                ProjectSessionFactory().create(project)
                .platform_session.application_runtime
            )

            self.assertEqual(
                runtime.descriptor.application_id,
                LEGACY_APPLICATION_ID,
            )
            self.assertEqual(
                runtime.descriptor.supported_project_schema_versions,
                (project.format_version,),
            )
            self.assertIsNone(runtime.module)
            self.assertEqual(
                runtime.lifecycle_state,
                ApplicationLifecycleState.SESSION_CREATED,
            )
            self.assertIsNone(runtime.application_session)

    def test_available_application_module_and_descriptor_are_preserved(self):
        with TemporaryDirectory() as temporary:
            module = FutureModuleDouble()
            project = ProjectManager().create_project(
                "Future",
                Path(temporary),
                application_id=module.application_id,
            )
            factory = ProjectSessionFactory(
                ApplicationRegistry([module])
            )

            session = factory.create(project)
            runtime = session.platform_session.application_runtime

            self.assertIs(runtime.module, module)
            self.assertIs(runtime.descriptor, module.descriptor)
            self.assertIsNotNone(runtime.application_session)
            self.assertIsNone(session.rsc_session)

    def test_rsc_session_is_modular_and_keeps_legacy_alias_operational(self):
        with TemporaryDirectory() as temporary:
            application = RscApplication()
            project = ProjectManager().create_project(
                "RSC",
                Path(temporary),
                application_id="rsc",
            )
            session = ProjectSessionFactory(
                ApplicationRegistry([application])
            ).create(project)
            runtime = session.platform_session.application_runtime

            self.assertIsInstance(session.rsc_session, RscProjectSession)
            self.assertIs(session.application, application)
            self.assertEqual(runtime.descriptor.application_id, "rsc")
            self.assertEqual(runtime.descriptor.display_name, "RSC")
            self.assertIs(runtime.module, application)
            self.assertIs(runtime.descriptor, application.descriptor)
            self.assertIs(runtime.application_session, session.rsc_session)
            self.assertIsNotNone(
                session.rsc_session.create_activity_service
            )

    def test_legacy_constructor_parameters_and_attributes_are_preserved(self):
        expected_parameters = (
            "project",
            "document_repository",
            "document_service",
            "document_import_service",
            "document_processor",
            "document_indexer",
            "search_service",
            "evidence_service",
            "application",
            "rsc_session",
        )

        self.assertEqual(
            tuple(inspect.signature(ProjectSession).parameters),
            expected_parameters,
        )
        self.assertNotIn(
            "platform_session",
            inspect.signature(ProjectSession).parameters,
        )

    def test_project_without_application_metadata_still_opens(self):
        with TemporaryDirectory() as temporary:
            project = ProjectManager().create_project(
                "Historical",
                Path(temporary),
            )
            project_file = project.project_file
            data = json.loads(project_file.read_text(encoding="utf-8"))
            data.pop("application")
            data.pop("format_version")
            project_file.write_text(
                json.dumps(data),
                encoding="utf-8",
            )

            reopened = ProjectManager().open_project(project.project_path)
            session = ProjectSessionFactory().create(reopened)

            self.assertEqual(reopened.application, LEGACY_APPLICATION_ID)
            self.assertEqual(reopened.format_version, 1)
            self.assertEqual(
                session.platform_session
                .project_context.application_id,
                LEGACY_APPLICATION_ID,
            )
            self.assertIsNone(session.rsc_session)


if __name__ == "__main__":
    unittest.main()
