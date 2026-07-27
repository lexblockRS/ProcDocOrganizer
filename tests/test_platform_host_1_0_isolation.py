from pathlib import Path
from tempfile import TemporaryDirectory
import inspect
import unittest

from contracts import (
    ApplicationDescriptor,
    ApplicationLifecycleState,
    ContributionCategory,
    DashboardContribution,
    DashboardRefreshPolicy,
    Version,
)
from core.application_lifecycle_host import ApplicationLifecycleHost
from core.application_registry import ApplicationRegistry
from core.contribution_manager import ContributionManager
from core.project_manager import ProjectManager
from core.project_session_factory import ProjectSessionFactory


class IsolatedApplication:
    """Aplicação mínima composta somente pelas APIs da baseline."""

    descriptor = ApplicationDescriptor(
        application_id="baseline.isolated",
        display_name="Baseline Isolated",
        version=Version(1, 0, 0),
        minimum_platform_version=Version(1, 0, 0),
        supported_project_schema_versions=(1,),
    )

    def __init__(self):
        self.calls = []
        self.session = object()
        self.dashboard = DashboardContribution(
            application_id=self.descriptor.application_id,
            section="summary",
            priority=0,
            widget_factory=object,
            refresh_policy=DashboardRefreshPolicy.ON_OPEN,
        )

    def prepare(self, context):
        self.calls.append("prepare")

    def create_session(self, context):
        self.calls.append("create_session")
        return self.session

    def contributions(self, session):
        self.calls.append("contributions")
        return (self.dashboard,)

    def transition(self, transition):
        self.calls.append(transition.target)

    def dispose(self):
        self.calls.append("dispose")


class PlatformHostIsolationTests(unittest.TestCase):
    def test_external_application_uses_complete_host_without_host_changes(self):
        application = IsolatedApplication()
        registry = ApplicationRegistry((application,))
        contribution_manager = ContributionManager()
        lifecycle_host = ApplicationLifecycleHost()

        self.assertEqual(
            registry.descriptors,
            (application.descriptor,),
        )

        with TemporaryDirectory() as temporary:
            project = ProjectManager().create_project(
                "Isolated",
                Path(temporary),
                application_id=application.descriptor.application_id,
            )
            session = ProjectSessionFactory(registry).create(project)
            runtime = session.platform_session.application_runtime

            contributions = application.contributions(
                runtime.application_session
            )
            contribution_manager.register_application(
                application,
                contributions,
                category=ContributionCategory.DASHBOARD,
            )
            lifecycle_host.activate_session(session)

            self.assertIs(
                runtime.application_session,
                application.session,
            )
            self.assertEqual(
                runtime.lifecycle_state,
                ApplicationLifecycleState.ACTIVE,
            )
            self.assertEqual(
                contribution_manager.dashboard_contributions(),
                (application.dashboard,),
            )

            lifecycle_host.dispose_session(session)

        self.assertEqual(
            runtime.lifecycle_state,
            ApplicationLifecycleState.DISPOSED,
        )
        self.assertIsNone(runtime.application_session)
        self.assertEqual(application.calls.count("prepare"), 1)
        self.assertEqual(application.calls.count("create_session"), 1)
        self.assertEqual(application.calls.count("contributions"), 1)
        self.assertEqual(application.calls.count("dispose"), 1)

    def test_fixture_does_not_import_rsc_or_private_host_components(self):
        source = inspect.getsource(IsolatedApplication)

        for forbidden in (
            "applications.rsc",
            "RscApplication",
            "ProjectController",
            "MainWindow",
            "rsc_session",
            "._",
        ):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, source)


if __name__ == "__main__":
    unittest.main()
