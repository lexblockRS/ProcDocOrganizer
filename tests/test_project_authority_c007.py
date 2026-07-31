from __future__ import annotations

import ast
from decimal import Decimal
import os
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from applications import RscApplication
from applications.rsc.project_explorer_composition import (
    create_project_explorer_service,
)
from core.application import Application
from core.application_lifecycle_host import ApplicationLifecycleHost
from core.application_registry import ApplicationRegistry
from core.operational_project_state import OperationalProjectStateStore
from core.project_manager import ProjectManager
from core.project_session import ProjectSession
from core.project_session_factory import ProjectSessionFactory
from models import Document
from presentation import NavigationIntent, NavigationIntentType


class RuntimeSpy:
    def __init__(self, *, fail_activate=False):
        self.fail_activate = fail_activate
        self.calls = []

    def activate(self):
        self.calls.append("activate")
        if self.fail_activate:
            raise RuntimeError("activation failed")

    def dispose(self):
        self.calls.append("dispose")


def fake_session(name, *, fail_activate=False):
    runtime = RuntimeSpy(fail_activate=fail_activate)
    return SimpleNamespace(
        project=SimpleNamespace(project_name=name),
        platform_session=SimpleNamespace(application_runtime=runtime),
        runtime=runtime,
    )


class ProjectAuthorityLifecycleTests(unittest.TestCase):
    def test_host_has_exactly_one_session_and_disposes_previous_after_commit(self):
        host = ApplicationLifecycleHost()
        first = fake_session("A")
        second = fake_session("B")

        host.activate_session(first)
        host.activate_session(second)

        self.assertIs(host.current_session, second)
        self.assertEqual(first.runtime.calls, ["activate", "dispose"])
        self.assertEqual(second.runtime.calls, ["activate"])

    def test_runtime_failure_preserves_previous_and_disposes_candidate(self):
        host = ApplicationLifecycleHost()
        first = fake_session("A")
        candidate = fake_session("B", fail_activate=True)
        host.activate_session(first)

        with self.assertRaisesRegex(RuntimeError, "activation failed"):
            host.activate_session(candidate)

        self.assertIs(host.current_session, first)
        self.assertEqual(first.runtime.calls, ["activate"])
        self.assertEqual(candidate.runtime.calls, ["activate", "dispose"])

    def test_final_binding_failure_rolls_back_without_disposing_previous(self):
        host = ApplicationLifecycleHost()
        first = fake_session("A")
        candidate = fake_session("B")
        host.activate_session(first)
        restored = []
        bound_consumer = [first]
        workspace = {"project": "A"}
        history = ["dashboard:A", "document:A"]

        def fail_binding(session, _previous):
            bound_consumer[0] = session
            raise RuntimeError("consumer failed")

        def restore_binding(previous, _candidate):
            bound_consumer[0] = previous
            restored.append(previous)

        with self.assertRaisesRegex(RuntimeError, "consumer failed"):
            host.activate_session(
                candidate,
                after_publish=fail_binding,
                rollback=restore_binding,
            )

        self.assertIs(host.current_session, first)
        self.assertIs(bound_consumer[0], first)
        self.assertEqual(restored, [first])
        self.assertEqual(workspace, {"project": "A"})
        self.assertEqual(history, ["dashboard:A", "document:A"])
        self.assertEqual(first.runtime.calls, ["activate"])
        self.assertEqual(candidate.runtime.calls, ["activate", "dispose"])

    def test_controller_and_view_do_not_store_active_project_authority(self):
        controller_source = Path("core/project_controller.py").read_text(
            encoding="utf-8"
        )
        controller_tree = ast.parse(controller_source)
        assigned = {
            target.attr
            for node in ast.walk(controller_tree)
            if isinstance(node, (ast.Assign, ast.AnnAssign))
            for target in (
                node.targets if isinstance(node, ast.Assign) else (node.target,)
            )
            if isinstance(target, ast.Attribute)
            and isinstance(target.value, ast.Name)
            and target.value.id == "self"
        }
        view_source = Path("ui/project_explorer.py").read_text(encoding="utf-8")
        self.assertNotIn("session", assigned)
        self.assertNotIn("_APPLICATION_LIFECYCLE_HOST", controller_source)
        self.assertNotIn("_current_project", view_source)
        self.assertNotIn("_current_workspace", view_source)
        for lifecycle_method in (
            "def create_project(",
            "def open_project(",
            "def close_project(",
        ):
            self.assertNotIn(lifecycle_method, view_source)


class OperationalProjectStateTests(unittest.TestCase):
    def test_identity_and_monotonic_revision_survive_reopening(self):
        with TemporaryDirectory() as temporary:
            project = ProjectManager().create_project(
                "Revision", Path(temporary), application_id="rsc"
            )
            database_path = project.project_path / project.database
            first = OperationalProjectStateStore(database_path)
            project_id = first.project_id
            self.assertEqual(first.current(), 0)
            self.assertEqual(first.increment("document.created"), 1)
            self.assertEqual(first.increment("evidence.created"), 2)

            reopened = OperationalProjectStateStore(database_path)
            self.assertEqual(reopened.project_id, project_id)
            self.assertEqual(reopened.current(), 2)

    def test_project_session_public_contract_remains_frozen_and_unchanged(self):
        field_names = tuple(ProjectSession.__dataclass_fields__)
        self.assertNotIn("operational_revision", field_names)
        self.assertNotIn("operational_project_id", field_names)
        self.assertTrue(ProjectSession.__dataclass_params__.frozen)


class ProductiveProjectScopeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.qt = QApplication.instance() or QApplication([])

    def _session(self, project):
        return ProjectSessionFactory(
            ApplicationRegistry((RscApplication(),))
        ).create(project)

    def test_document_without_evidence_reaches_productive_coverage(self):
        with TemporaryDirectory() as temporary:
            project = ProjectManager().create_project(
                "Coverage", Path(temporary), application_id="rsc"
            )
            session = self._session(project)
            service = create_project_explorer_service(session)
            try:
                document = Document(
                    id="document-without-evidence",
                    name="isolado.pdf",
                    original_filename="isolado.pdf",
                    stored_filename="isolado.pdf",
                    relative_path="documents/isolado.pdf",
                    imported_at=Document.now(),
                    created_at=Document.now(),
                    updated_at=Document.now(),
                    sha256="a" * 64,
                )
                session.document_repository.create(document)

                workspace, coverage_input = service._presentation_inputs(
                    service.project
                )
                dashboard, review = service.presentation_snapshots(
                    service.project, workspace_snapshot=workspace
                )

                self.assertEqual(len(coverage_input.documents), 1)
                self.assertEqual(
                    coverage_input.documents[0].identity.resource_id,
                    document.id,
                )
                self.assertEqual(coverage_input.documents[0].evidences, ())
                self.assertEqual(dashboard.coverage.document_coverage.total, 1)
                self.assertEqual(dashboard.coverage.document_coverage.unused, 1)
                document_items = tuple(
                    item
                    for item in review.items
                    if item.category.value == "documents"
                )
                self.assertEqual(len(document_items), 1)
                self.assertEqual(
                    document_items[0].primary_resource.resource_id,
                    document.id,
                )
            finally:
                service.close()
                session.platform_session.application_runtime.dispose()

    def test_two_pdop_projects_have_isolated_ids_revisions_and_connections(self):
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            manager = ProjectManager()
            first_project = manager.create_project("A", root, application_id="rsc")
            second_project = manager.create_project("B", root, application_id="rsc")
            first_session = self._session(first_project)
            second_session = self._session(second_project)
            first = create_project_explorer_service(first_session)
            second = create_project_explorer_service(second_session)
            try:
                first.create_evidence(
                    project_id=first.project.aggregate_id, title="Somente A"
                )
                first.execute()
                self.assertNotEqual(
                    first.project.aggregate_id, second.project.aggregate_id
                )
                self.assertEqual(len(first.list_evidences(first.project.aggregate_id)), 1)
                self.assertEqual(len(second.list_evidences(second.project.aggregate_id)), 0)
                self.assertEqual(first.operational_revision, 1)
                self.assertEqual(second.operational_revision, 0)
                self.assertIsNotNone(first.last_execution_result)
                self.assertIsNone(second.last_execution_result)
            finally:
                first.close()
                second.close()
                first_session.platform_session.application_runtime.dispose()
                second_session.platform_session.application_runtime.dispose()
            self.assertIsNone(first._evidences._connection)
            self.assertIsNone(second._evidences._connection)

    def test_operational_mutations_increment_without_reusing_visual_revision(self):
        with TemporaryDirectory() as temporary:
            project = ProjectManager().create_project(
                "Mutations", Path(temporary), application_id="rsc"
            )
            session = self._session(project)
            service = create_project_explorer_service(session)
            try:
                document = Document(
                    id="canonical-document",
                    name="documento.pdf",
                    original_filename="documento.pdf",
                    stored_filename="documento.pdf",
                    relative_path="documents/documento.pdf",
                    imported_at=Document.now(),
                    created_at=Document.now(),
                    updated_at=Document.now(),
                    sha256="b" * 64,
                )
                session.document_repository.create(document)
                evidence = service.create_evidence(
                    project_id=service.project.aggregate_id,
                    title="Evidence",
                )
                fact = service.create_fact(
                    project_id=service.project.aggregate_id,
                    evidence_id=evidence.aggregate_id,
                    fact_type="activity",
                    description="Fact",
                    quantity=Decimal("1"),
                    unit="item",
                )
                service.create_binding(
                    execution_fact_id=fact.aggregate_id,
                    criterion_id=service.criterion_definitions()[0].code,
                )

                workspace, _ = service._presentation_inputs(service.project)
                visual_revision = 37
                from dataclasses import replace

                projected_workspace, coverage_input = service._presentation_inputs(
                    service.project,
                    workspace_snapshot=replace(workspace, revision=visual_revision),
                )
                self.assertEqual(service.operational_revision, 4)
                self.assertEqual(coverage_input.project_revision, 4)
                self.assertEqual(projected_workspace.revision, visual_revision)
                self.assertEqual(service.project.revision, 0)
            finally:
                service.close()
                session.platform_session.application_runtime.dispose()

    def test_legacy_productive_database_is_detected_but_not_opened_or_changed(self):
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            legacy = root / "productive-shell.sqlite"
            payload = b"legacy-data-must-remain"
            legacy.write_bytes(payload)
            application = Application(productive_database_path=legacy)
            try:
                self.assertTrue(application.legacy_productive_database_detected)
                self.assertIsNone(application.lifecycle_host.current_session)
                self.assertEqual(legacy.read_bytes(), payload)
            finally:
                application.main_window.close()
                application.app.processEvents()

    def test_real_composition_rollback_preserves_presentation_context(self):
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            application = Application(
                productive_database_path=root / "legacy.sqlite"
            )
            controller = application.project_controller
            first_project = application.project_manager.create_project(
                "A", root, application_id="rsc"
            )
            second_project = application.project_manager.create_project(
                "B", root, application_id="rsc"
            )
            try:
                controller._load_project(first_project)
                controller._complete_project_open(first_project, "A aberta.")
                first_session = application.lifecycle_host.current_session
                first_service = application._productive_service
                application.main_window.navigation_controller.navigate(
                    NavigationIntent(
                        NavigationIntentType.OPEN_PERSPECTIVE,
                        "review_workspace",
                        project_id=first_service.project.aggregate_id,
                    )
                )
                workspace = application.main_window.workspace_store.snapshot
                selection = application.main_window.selection_store.snapshot
                history = application.main_window.navigation_controller.history
                history_position = (
                    application.main_window.navigation_controller.history_position
                )
                prepared = []
                original_prepare = controller._prepare_session_consumers
                original_bind = application.productive_workspace.bind_service

                def prepare(session):
                    service = original_prepare(session)
                    prepared.append(service)
                    return service

                def fail_candidate(service):
                    if service is not first_service:
                        raise RuntimeError("falha controlada de consumidor")
                    return original_bind(service)

                controller._prepare_session_consumers = prepare
                try:
                    with patch.object(
                        application.productive_workspace,
                        "bind_service",
                        side_effect=fail_candidate,
                    ):
                        with self.assertRaisesRegex(
                            RuntimeError, "falha controlada"
                        ):
                            controller._load_project(second_project)
                finally:
                    controller._prepare_session_consumers = original_prepare

                self.assertIs(
                    application.lifecycle_host.current_session, first_session
                )
                self.assertIs(application._productive_service, first_service)
                self.assertIs(
                    application.productive_workspace._service, first_service
                )
                self.assertIs(
                    application.main_window.workspace_store.snapshot, workspace
                )
                self.assertIs(
                    application.main_window.selection_store.snapshot, selection
                )
                self.assertEqual(
                    application.main_window.navigation_controller.history,
                    history,
                )
                self.assertEqual(
                    application.main_window.navigation_controller.history_position,
                    history_position,
                )
                self.assertEqual(len(prepared), 1)
                self.assertIsNone(prepared[0]._evidences._connection)
                self.assertIsNone(prepared[0]._facts._connection)
                self.assertIsNone(prepared[0]._bindings._connection)
            finally:
                if application.lifecycle_host.current_session is not None:
                    controller.close_project()
                application.main_window.close()
                application.app.processEvents()


if __name__ == "__main__":
    unittest.main()
