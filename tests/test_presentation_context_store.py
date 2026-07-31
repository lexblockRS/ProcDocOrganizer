import ast
from dataclasses import FrozenInstanceError
from pathlib import Path
import unittest

import presentation
from presentation import (
    ApplicationState,
    ApplicationStateStore,
    PerspectiveDefinition,
    PerspectiveId,
    PerspectiveStore,
    PresentationContextStore,
    PresentationSnapshot,
    SelectionContext,
    SelectionIdentity,
    SelectionKind,
    SelectionStore,
)


def perspective():
    return PerspectiveDefinition(
        PerspectiveId("overview"),
        "Visão geral",
        10,
        "overview",
        True,
        lambda: object(),
    )


class PresentationSnapshotTests(unittest.TestCase):
    def setUp(self):
        self.application_state_store = ApplicationStateStore()
        self.selection_store = SelectionStore()
        self.perspective_store = PerspectiveStore()

    def snapshot(self):
        return PresentationSnapshot(
            self.application_state_store.snapshot,
            self.selection_store.snapshot,
            self.perspective_store.snapshot,
        )

    def test_is_frozen_slotted_and_initially_revision_zero(self):
        snapshot = self.snapshot()
        self.assertEqual(snapshot.revision, 0)
        self.assertFalse(hasattr(snapshot, "__dict__"))
        with self.assertRaises(FrozenInstanceError):
            snapshot.revision = 1

    def test_rejects_invalid_components_and_revision(self):
        valid = (
            self.application_state_store.snapshot,
            self.selection_store.snapshot,
            self.perspective_store.snapshot,
        )
        for args in (
            (object(), valid[1], valid[2]),
            (valid[0], object(), valid[2]),
            (valid[0], valid[1], object()),
        ):
            with self.subTest(args=args):
                with self.assertRaises(TypeError):
                    PresentationSnapshot(*args)
        with self.assertRaises(TypeError):
            PresentationSnapshot(*valid, revision=True)
        with self.assertRaises(ValueError):
            PresentationSnapshot(*valid, revision=-1)


class PresentationContextStoreTests(unittest.TestCase):
    def setUp(self):
        self.application_state = ApplicationStateStore()
        self.selection = SelectionStore()
        self.perspectives = PerspectiveStore()
        self.context = PresentationContextStore(
            self.application_state,
            self.selection,
            self.perspectives,
        )

    def test_initial_snapshot_aggregates_current_sources(self):
        snapshot = self.context.snapshot
        self.assertIs(
            snapshot.application_state,
            self.application_state.snapshot,
        )
        self.assertIs(snapshot.selection, self.selection.snapshot)
        self.assertIs(snapshot.perspective, self.perspectives.snapshot)
        self.assertEqual(snapshot.revision, 0)

    def test_application_state_update_is_aggregated(self):
        old_selection = self.context.snapshot.selection
        self.application_state.transition_to(
            ApplicationState.PROJECT_OPEN,
            project_id="project-1",
        )
        snapshot = self.context.snapshot
        self.assertIs(
            snapshot.application_state,
            self.application_state.snapshot,
        )
        self.assertIs(snapshot.selection, old_selection)
        self.assertEqual(snapshot.revision, 1)

    def test_selection_update_is_aggregated(self):
        selected = SelectionContext(
            SelectionIdentity(SelectionKind.DOCUMENT, "document-1"),
            "Documento",
        )
        self.selection.select(selected)
        self.assertIs(
            self.context.snapshot.selection,
            self.selection.snapshot,
        )
        self.assertEqual(self.context.snapshot.revision, 1)

    def test_perspective_updates_are_aggregated(self):
        item = perspective()
        self.perspectives.register(item)
        self.perspectives.activate(item.id)
        self.assertIs(
            self.context.snapshot.perspective,
            self.perspectives.snapshot,
        )
        self.assertEqual(
            self.context.snapshot.perspective.active,
            item.id,
        )
        self.assertEqual(self.context.snapshot.revision, 2)

    def test_source_owners_remain_authoritative(self):
        application_before = self.application_state.snapshot
        selection_before = self.selection.snapshot
        perspective_before = self.perspectives.snapshot
        self.context.subscribe(lambda _snapshot: None)
        self.assertIs(self.application_state.snapshot, application_before)
        self.assertIs(self.selection.snapshot, selection_before)
        self.assertIs(self.perspectives.snapshot, perspective_before)

    def test_redundant_source_changes_do_not_increment_revision(self):
        self.selection.clear()
        self.perspectives.deactivate()
        self.assertEqual(self.context.snapshot.revision, 0)

    def test_subscribe_unsubscribe_and_isolation(self):
        received = []

        def broken(_snapshot):
            raise RuntimeError("observer failure")

        self.context.subscribe(broken)
        unsubscribe = self.context.subscribe(received.append)
        self.selection.select(
            SelectionContext(
                SelectionIdentity(SelectionKind.PROCESS, "process-1")
            )
        )
        unsubscribe()
        unsubscribe()
        self.selection.clear()
        self.assertEqual(len(received), 1)
        self.assertEqual(received[0].revision, 1)
        self.assertEqual(self.context.snapshot.revision, 2)

    def test_duplicate_subscription_is_not_repeated(self):
        received = []
        self.context.subscribe(received.append)
        self.context.subscribe(received.append)
        self.perspectives.register(perspective())
        self.assertEqual(len(received), 1)

    def test_invalid_dependencies_are_rejected(self):
        valid = (
            self.application_state,
            self.selection,
            self.perspectives,
        )
        for args in (
            (object(), valid[1], valid[2]),
            (valid[0], object(), valid[2]),
            (valid[0], valid[1], object()),
        ):
            with self.subTest(args=args):
                with self.assertRaises(TypeError):
                    PresentationContextStore(*args)


class PresentationContextArchitectureTests(unittest.TestCase):
    def test_module_has_no_forbidden_dependencies(self):
        path = Path("presentation/presentation_context.py")
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
            "PySide",
            "PyQt",
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

    def test_public_exports_are_intentional(self):
        module = __import__(
            "presentation.presentation_context",
            fromlist=["__all__"],
        )
        self.assertEqual(
            set(module.__all__),
            {"PresentationContextStore", "PresentationSnapshot"},
        )
        self.assertTrue(
            set(module.__all__).issubset(set(presentation.__all__))
        )


if __name__ == "__main__":
    unittest.main()
