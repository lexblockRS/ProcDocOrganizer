import ast
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from PySide6.QtWidgets import QDialog

from contracts import ActionContribution
from core.project_controller import ProjectController
from core.application_lifecycle_host import ApplicationLifecycleHost
from ui.contribution_installer import ContributionInstallationError


def action(contribution_id):
    return ActionContribution(
        contribution_id=contribution_id,
        text=f"Action {contribution_id}",
        callback=lambda: None,
        menu_id="tools",
    )


class ApplicationSpy:
    def __init__(self, contributions):
        self._contributions = tuple(contributions)
        self.calls = 0

    def contributions(self):
        self.calls += 1
        return self._contributions


class InstallerSpy:
    def __init__(self, error=None):
        self.calls = []
        self.error = error

    def install(self, contributions):
        self.calls.append(("install", tuple(contributions)))
        if self.error is not None:
            raise self.error

    def replace(self, contributions):
        self.calls.append(("replace", tuple(contributions)))
        if self.error is not None:
            raise self.error

    def clear(self):
        self.calls.append(("clear",))
        if self.error is not None:
            raise self.error


class StateSpy:
    def __init__(self, project=None):
        self.current_project = project

    @property
    def has_project(self):
        return self.current_project is not None

    def open_project(self, project):
        self.current_project = project

    def close_project(self):
        self.current_project = None


class ServiceControllerSpy:
    def __init__(self):
        self.services = []

    def set_service(self, service):
        self.services.append(service)

    def set_search_service(self, service):
        self.set_service(service)

    def load(self):
        return True

    def can_leave(self):
        return True


class WindowSpy:
    def __init__(self):
        self.projects = []
        self.clear_count = 0

    def set_project(self, project, documents):
        self.projects.append((project, tuple(documents)))

    def clear_project(self):
        self.clear_count += 1


class RuntimeSpy:
    def __init__(self):
        self.calls = []

    def activate(self):
        self.calls.append("activate")

    def dispose(self):
        self.calls.append("dispose")


def project_session(project, application=None):
    return SimpleNamespace(
        project=project,
        application=application,
        document_repository=SimpleNamespace(
            list_documents=lambda: ()
        ),
        document_service=object(),
        search_service=object(),
        evidence_service=object(),
        platform_session=SimpleNamespace(
            application_runtime=RuntimeSpy()
        ),
    )


def controller_for(session, *, active_session=None, installer=None):
    controller = ProjectController.__new__(ProjectController)
    controller.window = WindowSpy()
    controller.manager = Mock()
    controller.session_factory = SimpleNamespace(
        create=lambda _project: session
    )
    controller.application_registry = SimpleNamespace(descriptors=())
    controller.contribution_installer = installer or InstallerSpy()
    controller.lifecycle_host = ApplicationLifecycleHost()
    if active_session is not None:
        controller.lifecycle_host._current_session = active_session
    from core.project_state import ProjectState
    controller.state = ProjectState(controller.lifecycle_host)
    controller._prepare_session_consumers = None
    controller._commit_session_consumers = None
    controller._rollback_session_consumers = None
    controller._close_session_consumers = None
    controller._active_project_id = lambda _session: "project"
    controller._initial_perspective = "home"
    controller.selected_document = object()
    controller.search_controller = ServiceControllerSpy()
    controller.documents_controller = ServiceControllerSpy()
    controller.evidence_controller = ServiceControllerSpy()
    return controller


class ApplicationContributionLifecycleTests(unittest.TestCase):
    def test_load_activates_new_runtime_after_installation(self):
        project = object()
        created = project_session(project)
        controller = controller_for(created)

        controller._load_project(project)

        self.assertEqual(
            created.platform_session.application_runtime.calls,
            ["activate"],
        )

    def test_switch_disposes_previous_runtime_after_new_activation(self):
        old = project_session(object())
        new = project_session(object())
        controller = controller_for(new, active_session=old)

        controller._load_project(new.project)

        self.assertEqual(
            new.platform_session.application_runtime.calls,
            ["activate"],
        )
        self.assertEqual(
            old.platform_session.application_runtime.calls,
            ["dispose"],
        )

    def test_initial_project_installs_application_contributions(self):
        project = object()
        contribution = action("initial")
        application = ApplicationSpy([contribution])
        controller = controller_for(
            project_session(project, application)
        )

        controller._load_project(project)

        self.assertEqual(
            controller.contribution_installer.calls,
            [("install", (contribution,))],
        )
        self.assertEqual(application.calls, 1)

    def test_new_project_flow_installs_contributions(self):
        project = object()
        contribution = action("new")
        controller = controller_for(
            project_session(
                project, ApplicationSpy([contribution])
            )
        )
        controller.manager.create_project.return_value = project
        dialog = Mock()
        dialog.exec.return_value = QDialog.DialogCode.Accepted
        dialog.get_project_name.return_value = "Project"
        dialog.get_project_folder.return_value = Path("destination")
        dialog.get_application_id.return_value = "example"

        with patch(
            "core.project_controller.NewProjectDialog",
            return_value=dialog,
        ):
            controller.new_project()

        self.assertEqual(
            controller.contribution_installer.calls,
            [("install", (contribution,))],
        )

    def test_open_project_flow_installs_contributions(self):
        project = object()
        contribution = action("open")
        controller = controller_for(
            project_session(
                project, ApplicationSpy([contribution])
            )
        )
        controller.manager.open_project.return_value = project

        with patch(
            "core.project_controller.QFileDialog.getExistingDirectory",
            return_value="project.pdop",
        ):
            controller.open_project()

        self.assertEqual(
            controller.contribution_installer.calls,
            [("install", (contribution,))],
        )

    def test_switching_session_replaces_contributions(self):
        old_project = object()
        new_project = object()
        old_session = project_session(old_project)
        contribution = action("replacement")
        controller = controller_for(
            project_session(
                new_project, ApplicationSpy([contribution])
            ),
            active_session=old_session,
        )

        controller._load_project(new_project)

        self.assertEqual(
            controller.contribution_installer.calls,
            [("replace", (contribution,))],
        )

    def test_close_project_clears_contributions(self):
        project = object()
        active = project_session(project)
        controller = controller_for(
            active,
            active_session=active,
        )

        controller.close_project()

        self.assertEqual(
            controller.contribution_installer.calls,
            [("clear",)],
        )
        self.assertIsNone(controller.session)
        self.assertIsNone(controller.state.current_project)
        self.assertEqual(
            active.platform_session.application_runtime.calls,
            ["dispose"],
        )

    def test_close_without_project_clears_idempotently(self):
        session = project_session(object())
        controller = controller_for(session)

        controller.close_project()

        self.assertEqual(
            controller.contribution_installer.calls,
            [("clear",)],
        )

    def test_application_without_contributions_installs_empty_tuple(self):
        project = object()
        application = ApplicationSpy(())
        controller = controller_for(
            project_session(project, application)
        )

        controller._load_project(project)

        self.assertEqual(
            controller.contribution_installer.calls,
            [("install", ())],
        )

    def test_installer_error_is_propagated_before_session_commit(self):
        old_project = object()
        new_project = object()
        old_session = project_session(old_project)
        error = ContributionInstallationError("installation failed")
        installer = InstallerSpy(error)
        controller = controller_for(
            project_session(
                new_project, ApplicationSpy([action("new")])
            ),
            active_session=old_session,
            installer=installer,
        )

        with self.assertRaises(ContributionInstallationError) as context:
            controller._load_project(new_project)

        self.assertIs(context.exception, error)
        self.assertIs(controller.session, old_session)
        self.assertIs(controller.state.current_project, old_project)
        self.assertEqual(controller.window.projects, [])
        self.assertEqual(controller.search_controller.services, [])
        self.assertEqual(controller.documents_controller.services, [])
        self.assertEqual(controller.evidence_controller.services, [])

    def test_install_failure_is_propagated_before_initial_session_commit(self):
        project = object()
        error = ContributionInstallationError("install failed")
        installer = InstallerSpy(error)
        contribution = action("initial")
        controller = controller_for(
            project_session(
                project, ApplicationSpy([contribution])
            ),
            installer=installer,
        )

        with self.assertRaises(ContributionInstallationError) as context:
            controller._load_project(project)

        self.assertIs(context.exception, error)
        self.assertEqual(
            installer.calls,
            [("install", (contribution,))],
        )
        self.assertIsNone(controller.session)
        self.assertIsNone(controller.state.current_project)
        self.assertEqual(controller.window.projects, [])
        self.assertEqual(controller.search_controller.services, [])
        self.assertEqual(controller.documents_controller.services, [])
        self.assertEqual(controller.evidence_controller.services, [])

    def test_clear_failure_preserves_open_session_and_services(self):
        project = object()
        active = project_session(project)
        error = ContributionInstallationError("clear failed")
        installer = InstallerSpy(error)
        controller = controller_for(
            active,
            active_session=active,
            installer=installer,
        )
        controller.search_controller.set_search_service(
            active.search_service
        )
        controller.documents_controller.set_service(
            active.document_service
        )
        controller.evidence_controller.set_service(
            active.evidence_service
        )

        with self.assertRaises(ContributionInstallationError) as context:
            controller.close_project()

        self.assertIs(context.exception, error)
        self.assertEqual(installer.calls, [("clear",)])
        self.assertIs(controller.session, active)
        self.assertIs(controller.state.current_project, project)
        self.assertEqual(controller.window.clear_count, 0)
        self.assertEqual(
            controller.search_controller.services,
            [active.search_service],
        )
        self.assertEqual(
            controller.documents_controller.services,
            [active.document_service],
        )
        self.assertEqual(
            controller.evidence_controller.services,
            [active.evidence_service],
        )

    def test_contributions_error_is_propagated_before_installer_call(self):
        old_project = object()
        new_project = object()
        old_session = project_session(old_project)
        error = RuntimeError("contributions failed")
        application = Mock()
        application.contributions.side_effect = error
        installer = InstallerSpy()
        controller = controller_for(
            project_session(new_project, application),
            active_session=old_session,
            installer=installer,
        )

        with self.assertRaises(RuntimeError) as context:
            controller._load_project(new_project)

        self.assertIs(context.exception, error)
        self.assertEqual(installer.calls, [])
        self.assertIs(controller.session, old_session)
        self.assertIs(controller.state.current_project, old_project)
        self.assertEqual(controller.window.projects, [])
        self.assertEqual(controller.search_controller.services, [])
        self.assertEqual(controller.documents_controller.services, [])
        self.assertEqual(controller.evidence_controller.services, [])

    def test_controller_does_not_create_or_manipulate_qt_actions(self):
        root = Path(__file__).parents[1]
        controller_path = root / "core" / "project_controller.py"
        source = controller_path.read_text(encoding="utf-8")
        tree = ast.parse(source)
        imported_names = {
            alias.name
            for node in ast.walk(tree)
            if isinstance(node, (ast.Import, ast.ImportFrom))
            for alias in node.names
        }

        self.assertNotIn("QAction", imported_names)
        self.assertNotIn("QMenu", imported_names)
        self.assertNotIn("_InstalledAction", source)
        self.assertNotIn(".get_menu(", source)

    def test_main_window_remains_decoupled_from_applications(self):
        root = Path(__file__).parents[1]
        source = (
            root / "ui" / "main_window.py"
        ).read_text(encoding="utf-8")

        for forbidden in (
            "ActionContribution",
            "DesktopContributionInstaller",
            "RscApplication",
            "ApplicationRegistry",
        ):
            self.assertNotIn(forbidden, source)


if __name__ == "__main__":
    unittest.main()
