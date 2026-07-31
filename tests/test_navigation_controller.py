import ast
from pathlib import Path
import unittest
from unittest.mock import patch

import presentation
from presentation import (
    NavigationController,
    PerspectiveDefinition,
    PerspectiveId,
    PerspectiveNotRegistered,
    PerspectiveStore,
    SelectionContext,
    SelectionIdentity,
    SelectionKind,
    SelectionStore,
    WorkspaceState,
    WorkspaceStore,
)


def definition(value, title):
    return PerspectiveDefinition(
        PerspectiveId(value),
        title,
        10,
        None,
        True,
        lambda: object(),
    )


class NavigationControllerTests(unittest.TestCase):
    def setUp(self):
        self.perspectives = PerspectiveStore()
        self.overview = definition("overview", "Visão geral")
        self.timeline = definition("timeline", "Linha do tempo")
        self.perspectives.register(self.overview)
        self.perspectives.register(self.timeline)
        self.workspace = WorkspaceStore(self.perspectives)
        self.selection = SelectionStore()
        self.controller = NavigationController(
            self.perspectives,
            self.workspace,
            self.selection,
        )

    def select_document(self):
        self.selection.select(
            SelectionContext(
                SelectionIdentity(SelectionKind.DOCUMENT, "document-1"),
                "Documento",
            )
        )

    def test_valid_navigation_coordinates_all_stores(self):
        self.select_document()
        result = self.controller.navigate_to(self.overview.id)
        self.assertIsNone(result)
        self.assertEqual(
            self.perspectives.snapshot.active,
            self.overview.id,
        )
        self.assertEqual(
            self.workspace.snapshot.active_perspective,
            self.overview.id,
        )
        self.assertIs(
            self.workspace.snapshot.state,
            WorkspaceState.READY,
        )
        self.assertIs(
            self.selection.snapshot.selection.identity.kind,
            SelectionKind.NONE,
        )

    def test_missing_perspective_stops_without_changes(self):
        perspective_before = self.perspectives.snapshot
        workspace_before = self.workspace.snapshot
        selection_before = self.selection.snapshot
        with self.assertRaises(PerspectiveNotRegistered):
            self.controller.navigate_to(PerspectiveId("missing"))
        self.assertIs(self.perspectives.snapshot, perspective_before)
        self.assertIs(self.workspace.snapshot, workspace_before)
        self.assertIs(self.selection.snapshot, selection_before)

    def test_invalid_id_stops_before_stores(self):
        with patch.object(
            self.perspectives, "activate"
        ) as activate:
            with self.assertRaises(TypeError):
                self.controller.navigate_to("overview")
        activate.assert_not_called()

    def test_workspace_failure_stops_flow_and_propagates(self):
        self.select_document()
        selection_before = self.selection.snapshot.selection
        with patch.object(
            self.workspace,
            "mount",
            side_effect=RuntimeError("workspace failure"),
        ):
            with self.assertRaisesRegex(
                RuntimeError, "workspace failure"
            ):
                self.controller.navigate_to(self.overview.id)
        self.assertEqual(
            self.perspectives.snapshot.active,
            self.overview.id,
        )
        self.assertEqual(
            self.selection.snapshot.selection,
            selection_before,
        )
        self.assertIs(self.workspace.snapshot.state, WorkspaceState.EMPTY)

    def test_selection_failure_propagates_without_rollback(self):
        self.controller.navigate_to(self.overview.id)
        self.select_document()
        selection_before = self.selection.snapshot.selection
        with patch.object(
            self.selection,
            "clear",
            side_effect=RuntimeError("selection failure"),
        ):
            with self.assertRaisesRegex(
                RuntimeError, "selection failure"
            ):
                self.controller.navigate_to(self.timeline.id)
        self.assertEqual(
            self.perspectives.snapshot.active,
            self.timeline.id,
        )
        self.assertEqual(
            self.workspace.snapshot.active_perspective,
            self.timeline.id,
        )
        self.assertEqual(
            self.selection.snapshot.selection,
            selection_before,
        )

    def test_selection_clear_can_be_disabled(self):
        self.select_document()
        selected = self.selection.snapshot
        controller = NavigationController(
            self.perspectives,
            self.workspace,
            self.selection,
            clear_selection_on_navigation=False,
        )
        controller.navigate_to(self.overview.id)
        self.assertIs(self.selection.snapshot, selected)

    def test_redundant_navigation_preserves_store_revisions(self):
        self.controller.navigate_to(self.overview.id)
        revisions = (
            self.perspectives.snapshot.revision,
            self.workspace.snapshot.revision,
            self.selection.snapshot.revision,
        )
        self.controller.navigate_to(self.overview.id)
        self.assertEqual(
            (
                self.perspectives.snapshot.revision,
                self.workspace.snapshot.revision,
                self.selection.snapshot.revision,
            ),
            revisions,
        )

    def test_calls_stores_in_required_order(self):
        calls = []
        with (
            patch.object(
                self.perspectives,
                "activate",
                side_effect=lambda value: calls.append(
                    ("activate", value)
                ),
            ),
            patch.object(
                self.workspace,
                "mount",
                side_effect=lambda value: calls.append(("mount", value)),
            ),
            patch.object(
                self.selection,
                "clear",
                side_effect=lambda: calls.append(("clear", None)),
            ),
        ):
            self.controller.navigate_to(self.overview.id)
        self.assertEqual(
            calls,
            [
                ("activate", self.overview.id),
                ("mount", self.overview.id),
                ("clear", None),
            ],
        )

    def test_rejects_invalid_dependencies_and_policy(self):
        valid = (self.perspectives, self.workspace, self.selection)
        for args in (
            (object(), valid[1], valid[2]),
            (valid[0], object(), valid[2]),
            (valid[0], valid[1], object()),
        ):
            with self.subTest(args=args):
                with self.assertRaises(TypeError):
                    NavigationController(*args)
        with self.assertRaises(TypeError):
            NavigationController(*valid, clear_selection_on_navigation=1)

    def test_has_no_navigation_state_api(self):
        self.assertFalse(hasattr(self.controller, "snapshot"))
        self.assertFalse(hasattr(self.controller, "revision"))
        self.assertFalse(hasattr(self.controller, "subscribe"))
        self.assertFalse(hasattr(self.controller, "__dict__"))


class NavigationArchitectureTests(unittest.TestCase):
    def test_module_dependencies_are_restricted(self):
        path = Path("presentation/navigation.py")
        tree = ast.parse(path.read_text(encoding="utf-8"))
        imports = {
            node.module or ""
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom)
        }
        imported_names = {
            alias.name
            for node in ast.walk(tree)
            if isinstance(node, ast.Import)
            for alias in node.names
        }
        forbidden = (
            "application_state",
            "pyside",
            "pyqt",
            "main_window",
            "domain",
            "infrastructure",
            "facade",
        )
        for name in imports | imported_names:
            self.assertFalse(
                any(item in name.casefold() for item in forbidden),
                name,
            )

    def test_ast_has_no_state_contract(self):
        tree = ast.parse(
            Path("presentation/navigation.py").read_text(
                encoding="utf-8"
            )
        )
        names = {
            node.name
            for node in ast.walk(tree)
            if isinstance(
                node,
                (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef),
            )
        }
        self.assertNotIn("snapshot", names)
        self.assertNotIn("subscribe", names)
        self.assertNotIn("revision", names)
        self.assertNotIn("Snapshot", " ".join(names))

    def test_public_export_is_intentional(self):
        module = __import__(
            "presentation.navigation",
            fromlist=["__all__"],
        )
        self.assertEqual(
            set(module.__all__),
            {"NavigationController", "NavigationHistoryEntry"},
        )
        self.assertIn("NavigationController", presentation.__all__)


if __name__ == "__main__":
    unittest.main()
