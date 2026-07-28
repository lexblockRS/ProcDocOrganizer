import ast
from dataclasses import FrozenInstanceError
from pathlib import Path
import unittest

import presentation
from presentation import (
    InvalidWorkspacePerspective,
    PerspectiveDefinition,
    PerspectiveId,
    PerspectiveStore,
    WorkspaceContractError,
    WorkspaceSnapshot,
    WorkspaceState,
    WorkspaceStore,
)


def definition(
    value="overview",
    title="Visão geral",
    factory=lambda: object(),
):
    return PerspectiveDefinition(
        PerspectiveId(value),
        title,
        10,
        "overview",
        True,
        factory,
    )


class WorkspaceStateAndSnapshotTests(unittest.TestCase):
    def test_state_has_only_empty_and_ready(self):
        self.assertEqual(
            set(WorkspaceState),
            {WorkspaceState.EMPTY, WorkspaceState.READY},
        )

    def test_default_snapshot_is_empty_frozen_and_slotted(self):
        snapshot = WorkspaceSnapshot()
        self.assertIs(snapshot.state, WorkspaceState.EMPTY)
        self.assertIsNone(snapshot.active_perspective)
        self.assertEqual(snapshot.revision, 0)
        self.assertFalse(hasattr(snapshot, "__dict__"))
        with self.assertRaises(FrozenInstanceError):
            snapshot.revision = 1

    def test_ready_snapshot_requires_perspective(self):
        item_id = PerspectiveId("overview")
        snapshot = WorkspaceSnapshot(
            WorkspaceState.READY,
            item_id,
            1,
        )
        self.assertEqual(snapshot.active_perspective, item_id)
        for args in (
            (WorkspaceState.EMPTY, item_id, 0),
            (WorkspaceState.READY, None, 0),
        ):
            with self.subTest(args=args):
                with self.assertRaises(WorkspaceContractError):
                    WorkspaceSnapshot(*args)

    def test_snapshot_rejects_invalid_types_and_revision(self):
        for args in (
            ("empty", None, 0),
            (WorkspaceState.EMPTY, object(), 0),
            (WorkspaceState.EMPTY, None, True),
            (WorkspaceState.EMPTY, None, -1),
        ):
            with self.subTest(args=args):
                with self.assertRaises(WorkspaceContractError):
                    WorkspaceSnapshot(*args)


class WorkspaceStoreTests(unittest.TestCase):
    def setUp(self):
        self.perspectives = PerspectiveStore()
        self.overview = definition()
        self.perspectives.register(self.overview)
        self.workspace = WorkspaceStore(self.perspectives)

    def test_initial_state_is_empty(self):
        self.assertEqual(self.workspace.snapshot, WorkspaceSnapshot())

    def test_mount_is_logical_and_increments_revision(self):
        snapshot = self.workspace.mount(self.overview.id)
        self.assertIs(snapshot.state, WorkspaceState.READY)
        self.assertEqual(snapshot.active_perspective, self.overview.id)
        self.assertEqual(snapshot.revision, 1)

    def test_mount_rejects_invalid_or_unregistered_id(self):
        original = self.workspace.snapshot
        for value in (None, "overview", PerspectiveId("missing")):
            with self.subTest(value=value):
                with self.assertRaises(InvalidWorkspacePerspective):
                    self.workspace.mount(value)
                self.assertIs(self.workspace.snapshot, original)

    def test_mount_replaces_active_perspective(self):
        second = definition("timeline", "Linha do tempo")
        self.perspectives.register(second)
        self.workspace.mount(self.overview.id)
        snapshot = self.workspace.mount(second.id)
        self.assertEqual(snapshot.active_perspective, second.id)
        self.assertEqual(snapshot.revision, 2)

    def test_redundant_mount_is_noop(self):
        mounted = self.workspace.mount(self.overview.id)
        self.assertIs(self.workspace.mount(self.overview.id), mounted)

    def test_clear_and_redundant_clear(self):
        self.assertIs(self.workspace.clear(), self.workspace.snapshot)
        self.workspace.mount(self.overview.id)
        cleared = self.workspace.clear()
        self.assertIs(cleared.state, WorkspaceState.EMPTY)
        self.assertIsNone(cleared.active_perspective)
        self.assertEqual(cleared.revision, 2)
        self.assertIs(self.workspace.clear(), cleared)

    def test_does_not_activate_perspective_store(self):
        self.workspace.mount(self.overview.id)
        self.assertIsNone(self.perspectives.snapshot.active)

    def test_factory_is_never_executed(self):
        calls = []
        store = PerspectiveStore()
        item = definition(factory=lambda: calls.append("called"))
        store.register(item)
        workspace = WorkspaceStore(store)
        workspace.mount(item.id)
        workspace.clear()
        self.assertEqual(calls, [])

    def test_subscribe_unsubscribe_and_observer_isolation(self):
        received = []

        def broken(_snapshot):
            raise RuntimeError("observer failure")

        self.workspace.subscribe(broken)
        unsubscribe = self.workspace.subscribe(received.append)
        self.workspace.mount(self.overview.id)
        unsubscribe()
        unsubscribe()
        self.workspace.clear()
        self.assertEqual(len(received), 1)
        self.assertEqual(received[0].revision, 1)

    def test_duplicate_subscription_is_not_repeated(self):
        received = []
        self.workspace.subscribe(received.append)
        self.workspace.subscribe(received.append)
        self.workspace.mount(self.overview.id)
        self.assertEqual(len(received), 1)

    def test_rejects_invalid_catalog(self):
        with self.assertRaises(TypeError):
            WorkspaceStore(object())


class WorkspaceArchitectureTests(unittest.TestCase):
    def test_module_has_no_forbidden_dependencies(self):
        path = Path("presentation/workspace.py")
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
            "pyside",
            "pyqt",
            "main_window",
            "toolbar",
            "menu",
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
            "presentation.workspace",
            fromlist=["__all__"],
        )
        expected = {
            "InvalidWorkspacePerspective",
            "WorkspaceContractError",
            "WorkspaceSnapshot",
            "WorkspaceState",
            "WorkspaceStore",
        }
        self.assertEqual(set(module.__all__), expected)
        self.assertTrue(expected.issubset(set(presentation.__all__)))


if __name__ == "__main__":
    unittest.main()
