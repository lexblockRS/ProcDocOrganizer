import ast
import os
from pathlib import Path
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication, QWidget

from presentation import (
    ApplicationState,
    ApplicationStateStore,
    NavigationController,
    NavigationIntent,
    Notification,
    NotificationCenter,
    NotificationLevel,
    OperationExecutor,
    OperationId,
    PerspectiveId,
    PerspectiveStore,
    PresentationContextStore,
    SelectionContext,
    SelectionIdentity,
    SelectionKind,
    SelectionStore,
    WorkspaceStore,
    ResourceInspectorState,
    ResourceType,
)
from ui.main_window import MainWindow
from ui.workspace_host import WorkspaceHost


class WorkspaceHostTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_receives_and_switches_widgets(self):
        host = WorkspaceHost()
        first = QWidget()
        second = QWidget()
        host.set_active_widget(first)
        self.assertIs(host.active_widget, first)
        host.set_active_widget(second)
        self.assertIs(host.active_widget, second)
        self.assertEqual(host.count(), 2)
        host.deleteLater()

    def test_replaces_and_releases_previous_widget(self):
        host = WorkspaceHost()
        first = QWidget()
        second = QWidget()
        host.set_active_widget(first)
        host.replace_active_widget(second)
        self.assertIsNone(first.parent())
        self.assertIs(host.active_widget, second)
        self.assertEqual(host.count(), 1)
        host.release_active_widget()
        self.assertIsNone(second.parent())
        self.assertIsNone(host.active_widget)
        host.deleteLater()

    def test_rejects_non_widget(self):
        host = WorkspaceHost()
        with self.assertRaises(TypeError):
            host.set_active_widget(object())
        with self.assertRaises(TypeError):
            host.replace_active_widget(object())
        host.deleteLater()


class MainWindowPresentationIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.window = MainWindow()

    def tearDown(self):
        self.window.close()
        self.window.deleteLater()
        self.app.processEvents()

    def test_composes_official_components(self):
        expected = (
            ("application_state_store", ApplicationStateStore),
            ("selection_store", SelectionStore),
            ("perspective_store", PerspectiveStore),
            (
                "presentation_context_store",
                PresentationContextStore,
            ),
            ("workspace_store", WorkspaceStore),
            ("navigation_controller", NavigationController),
            ("notification_center", NotificationCenter),
            ("operation_executor", OperationExecutor),
            ("workspace_host", WorkspaceHost),
        )
        for attribute, expected_type in expected:
            with self.subTest(attribute=attribute):
                self.assertIsInstance(
                    getattr(self.window, attribute),
                    expected_type,
                )

    def test_all_visual_views_have_registered_perspectives(self):
        registered = {
            item.id.value
            for item in self.window.perspective_store.snapshot.available
        }
        self.assertEqual(registered, set(self.window.views))
        self.assertEqual(
            self.window.perspective_store.snapshot.active,
            PerspectiveId("home"),
        )
        self.assertIs(
            self.window.workspace_host.active_widget,
            self.window.home_view,
        )

    def test_navigation_coordinates_stores_and_workspace_host(self):
        self.window.selection_store.select(
            SelectionContext(
                SelectionIdentity(
                    SelectionKind.DOCUMENT,
                    "document-1",
                )
            )
        )
        self.assertTrue(self.window.show_view("documents"))
        self.assertEqual(
            self.window.perspective_store.snapshot.active,
            PerspectiveId("documents"),
        )
        self.assertEqual(
            self.window.workspace_store.snapshot.active_perspective,
            PerspectiveId("documents"),
        )
        self.assertIs(
            self.window.workspace_host.active_widget,
            self.window.documents_workspace,
        )
        self.assertIs(
            self.window.selection_store.snapshot.selection.identity.kind,
            SelectionKind.NONE,
        )

    def test_history_actions_restore_workspace_and_reflect_boundaries(self):
        self.assertFalse(self.window.action_back.isEnabled())
        self.assertFalse(self.window.action_forward.isEnabled())

        self.window.show_view("documents")
        self.window.show_view("evidence")

        self.assertTrue(self.window.action_back.isEnabled())
        self.assertFalse(self.window.action_forward.isEnabled())
        self.window.action_back.trigger()
        self.assertEqual(
            self.window.workspace_store.snapshot.active_perspective,
            PerspectiveId("documents"),
        )
        self.assertTrue(self.window.action_forward.isEnabled())
        self.window.action_forward.trigger()
        self.assertEqual(
            self.window.workspace_store.snapshot.active_perspective,
            PerspectiveId("evidence"),
        )

    def test_project_change_and_close_clear_navigation_history(self):
        self.window.show_view("documents")
        self.assertTrue(self.window.navigation_controller.history)

        self.window.application_state_store.transition_to(
            ApplicationState.PROJECT_OPEN,
            project_id="project-1",
        )
        self.assertEqual(self.window.navigation_controller.history, ())
        self.window.show_view("documents")
        self.window.application_state_store.transition_to(
            ApplicationState.NO_PROJECT
        )

        self.assertEqual(self.window.navigation_controller.history, ())
        self.assertFalse(self.window.action_back.isEnabled())
        self.assertFalse(self.window.action_forward.isEnabled())

    def test_resource_inspector_updates_from_workspace_navigation(self):
        cases = (
            (NavigationIntent.open_document("doc-1"), "document", "doc-1"),
            (NavigationIntent.open_evidence("ev-1"), "evidence", "ev-1"),
            (
                NavigationIntent.open_requirement("req-1"),
                "requirement",
                "req-1",
            ),
        )
        for intent, resource_type, identifier in cases:
            with self.subTest(resource_type=resource_type):
                self.window.navigation_controller.navigate(intent)
                data = self.window.resource_inspector.data
                self.assertIs(data.state, ResourceInspectorState.READY)
                self.assertEqual(data.resource_type, resource_type)
                self.assertEqual(data.resource_id, identifier)

    def test_resource_inspector_handles_missing_and_unavailable_projection(self):
        self.assertIs(
            self.window.resource_inspector.data.state,
            ResourceInspectorState.EMPTY,
        )

        class UnavailableProjector:
            def project(self, _identity, _workspace):
                raise LookupError("projection unavailable")

        self.window.resource_projectors[
            ResourceType.DOCUMENT
        ] = UnavailableProjector()
        self.window.navigation_controller.navigate(
            NavigationIntent.open_document("missing")
        )

        self.assertIs(
            self.window.resource_inspector.data.state,
            ResourceInspectorState.UNAVAILABLE,
        )

    def test_unknown_visual_target_preserves_navigation_state(self):
        perspective = self.window.perspective_store.snapshot
        workspace = self.window.workspace_store.snapshot
        self.assertFalse(self.window.show_view("missing"))
        self.assertIs(self.window.perspective_store.snapshot, perspective)
        self.assertIs(self.window.workspace_store.snapshot, workspace)

    def test_application_state_is_rendered_from_store(self):
        self.window.application_state_store.transition_to(
            ApplicationState.PROJECT_OPEN,
            project_id="project-1",
        )
        self.assertEqual(
            self.window.status_message.text(),
            "Projeto: project-1",
        )
        self.assertTrue(
            self.window.action_documents_workspace.isEnabled()
        )
        self.window.application_state_store.begin_operation("load-1")
        self.assertEqual(
            self.window.status_message.text(),
            "Operação em andamento",
        )
        self.assertFalse(
            self.window.action_documents_workspace.isEnabled()
        )

    def test_notification_adapter_uses_status_bar(self):
        item = Notification(
            NotificationLevel.SUCCESS,
            "Concluído",
            "Projeto carregado.",
            2,
        )
        self.window.notification_center.publish(item)
        self.assertEqual(
            self.window.statusBar().currentMessage(),
            "Projeto carregado.",
        )

    def test_operation_executor_is_composed_and_updates_store(self):
        observed = []
        self.window.application_state_store.subscribe(
            lambda snapshot: observed.append(snapshot.state)
        )
        result = object()
        returned = self.window.operation_executor.execute(
            OperationId("refresh"),
            lambda _context: result,
        )
        self.assertIs(returned, result)
        self.assertEqual(
            observed,
            [ApplicationState.BUSY, ApplicationState.NO_PROJECT],
        )

    def test_close_releases_integration_subscriptions(self):
        self.window.notification_center.publish(
            Notification(
                NotificationLevel.INFO,
                "Antes",
                "Antes do fechamento",
            )
        )
        self.assertTrue(self.window.close())
        self.window.notification_center.publish(
            Notification(
                NotificationLevel.INFO,
                "Depois",
                "Depois do fechamento",
            )
        )
        self.assertEqual(
            self.window.statusBar().currentMessage(),
            "Antes do fechamento",
        )
        self.assertEqual(
            self.window._presentation_unsubscribers,
            [],
        )

    def test_rejected_close_preserves_integration(self):
        self.window.set_close_guard(lambda: False)
        self.assertFalse(self.window.close())
        self.window.notification_center.publish(
            Notification(
                NotificationLevel.INFO,
                "Ativo",
                "Integração ativa",
            )
        )
        self.assertEqual(
            self.window.statusBar().currentMessage(),
            "Integração ativa",
        )

    def test_main_window_does_not_store_project_or_snapshot(self):
        self.assertFalse(hasattr(self.window, "project"))
        self.assertFalse(hasattr(self.window, "snapshot"))
        self.assertFalse(hasattr(self.window, "revision"))


class MainWindowIntegrationArchitectureTests(unittest.TestCase):
    def test_navigation_method_only_forwards_to_controller(self):
        tree = ast.parse(
            Path("ui/main_window.py").read_text(encoding="utf-8")
        )
        window = next(
            node
            for node in tree.body
            if isinstance(node, ast.ClassDef)
            and node.name == "MainWindow"
        )
        show_view = next(
            node
            for node in window.body
            if isinstance(node, ast.FunctionDef)
            and node.name == "show_view"
        )
        calls = {
            node.attr
            for node in ast.walk(show_view)
            if isinstance(node, ast.Attribute)
            and isinstance(node.ctx, ast.Load)
        }
        self.assertIn("navigate_to", calls)
        self.assertNotIn("activate", calls)
        self.assertNotIn("mount", calls)
        self.assertNotIn("select", calls)

    def test_main_window_has_no_direct_state_transitions(self):
        tree = ast.parse(
            Path("ui/main_window.py").read_text(encoding="utf-8")
        )
        called = {
            node.func.attr
            for node in ast.walk(tree)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
        }
        forbidden = {
            "transition_to",
            "begin_operation",
            "complete_operation",
            "cancel_operation",
            "fail_operation",
        }
        self.assertFalse(called & forbidden)


if __name__ == "__main__":
    unittest.main()
