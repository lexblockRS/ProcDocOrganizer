import ast
from dataclasses import FrozenInstanceError
from pathlib import Path
import unittest

import presentation
from presentation.perspectives import (
    DuplicatePerspective,
    InvalidPerspectiveDefinition,
    PerspectiveContractError,
    PerspectiveDefinition,
    PerspectiveId,
    PerspectiveNotRegistered,
    PerspectiveSnapshot,
    PerspectiveStore,
)


def definition(
    value="overview",
    title="Visão geral",
    order=10,
    factory=lambda: object(),
):
    return PerspectiveDefinition(
        id=PerspectiveId(value),
        title=title,
        order=order,
        icon="overview",
        requires_project=True,
        factory=factory,
    )


class PerspectiveIdTests(unittest.TestCase):
    def test_is_structural_hashable_and_normalized(self):
        left = PerspectiveId(" overview ")
        right = PerspectiveId("overview")
        self.assertEqual(left, right)
        self.assertEqual(hash(left), hash(right))
        self.assertEqual(left.to_dict(), {"value": "overview"})

    def test_is_frozen_and_slotted(self):
        item = PerspectiveId("overview")
        with self.assertRaises(FrozenInstanceError):
            item.value = "other"
        self.assertFalse(hasattr(item, "__dict__"))

    def test_rejects_invalid_value(self):
        for value in ("", "  ", None):
            with self.subTest(value=value):
                with self.assertRaises(PerspectiveContractError):
                    PerspectiveId(value)


class PerspectiveDefinitionTests(unittest.TestCase):
    def test_is_structural_frozen_slotted_and_serializable(self):
        factory = lambda: object()
        left = definition(factory=factory)
        right = definition(factory=factory)
        self.assertEqual(left, right)
        self.assertNotIn("factory", left.to_dict())
        with self.assertRaises(FrozenInstanceError):
            left.title = "Outro"
        self.assertFalse(hasattr(left, "__dict__"))

    def test_normalizes_text(self):
        item = PerspectiveDefinition(
            PerspectiveId("x"), " Título ", 1, " icon ", False, lambda: None
        )
        self.assertEqual(item.title, "Título")
        self.assertEqual(item.icon, "icon")

    def test_rejects_invalid_fields(self):
        valid = (
            PerspectiveId("x"), "Título", 1, None, False, lambda: None
        )
        invalid = (
            (None, *valid[1:]),
            (valid[0], "", *valid[2:]),
            (*valid[:2], True, *valid[3:]),
            (*valid[:3], "", *valid[4:]),
            (*valid[:4], 1, valid[5]),
            (*valid[:5], None),
        )
        for args in invalid:
            with self.subTest(args=args):
                with self.assertRaises(InvalidPerspectiveDefinition):
                    PerspectiveDefinition(*args)


class PerspectiveSnapshotTests(unittest.TestCase):
    def test_default_is_empty_and_frozen(self):
        snapshot = PerspectiveSnapshot()
        self.assertIsNone(snapshot.active)
        self.assertEqual(snapshot.available, ())
        self.assertEqual(snapshot.revision, 0)
        with self.assertRaises(FrozenInstanceError):
            snapshot.revision = 1

    def test_rejects_active_not_available(self):
        with self.assertRaises(PerspectiveContractError):
            PerspectiveSnapshot(active=PerspectiveId("missing"))

    def test_rejects_mutable_or_duplicate_collection(self):
        item = definition()
        with self.assertRaises(PerspectiveContractError):
            PerspectiveSnapshot(available=[item])
        with self.assertRaises(PerspectiveContractError):
            PerspectiveSnapshot(available=(item, item))


class PerspectiveStoreTests(unittest.TestCase):
    def setUp(self):
        self.store = PerspectiveStore()
        self.overview = definition()

    def test_register_query_list_and_contains(self):
        snapshot = self.store.register(self.overview)
        self.assertEqual(snapshot.revision, 1)
        self.assertIs(self.store.get(self.overview.id), self.overview)
        self.assertTrue(self.store.contains(self.overview.id))
        self.assertEqual(self.store.list_all(), (self.overview,))

    def test_registration_order_is_deterministic(self):
        later = definition("later", "Zeta", 20)
        same_order = definition("alpha", "Alfa", 10)
        self.store.register(later)
        self.store.register(self.overview)
        self.store.register(same_order)
        self.assertEqual(
            [item.id.value for item in self.store.list_all()],
            ["alpha", "overview", "later"],
        )

    def test_rejects_null_duplicate_id_and_conflicting_title(self):
        with self.assertRaises(InvalidPerspectiveDefinition):
            self.store.register(None)
        self.store.register(self.overview)
        with self.assertRaises(DuplicatePerspective):
            self.store.register(definition(title="Outro"))
        with self.assertRaises(DuplicatePerspective):
            self.store.register(
                definition("other", " VISÃO GERAL ")
            )

    def test_invalid_changes_preserve_snapshot(self):
        original = self.store.snapshot
        with self.assertRaises(PerspectiveNotRegistered):
            self.store.activate(PerspectiveId("missing"))
        self.assertIs(self.store.snapshot, original)

    def test_activate_switch_deactivate_and_revision(self):
        second = definition("timeline", "Linha do tempo", 20)
        self.store.register(self.overview)
        self.store.register(second)
        self.assertEqual(self.store.activate(self.overview.id).revision, 3)
        self.assertEqual(self.store.activate(second.id).revision, 4)
        snapshot = self.store.deactivate()
        self.assertIsNone(snapshot.active)
        self.assertEqual(snapshot.revision, 5)

    def test_redundant_activation_and_deactivation_are_noops(self):
        self.store.register(self.overview)
        active = self.store.activate(self.overview.id)
        self.assertIs(self.store.activate(self.overview.id), active)
        inactive = self.store.deactivate()
        self.assertIs(self.store.deactivate(), inactive)

    def test_factory_is_never_executed(self):
        calls = []
        item = definition(factory=lambda: calls.append("called"))
        self.store.register(item)
        self.store.get(item.id)
        self.store.activate(item.id)
        self.store.deactivate()
        self.assertEqual(calls, [])

    def test_subscribe_unsubscribe_and_observer_isolation(self):
        received = []

        def broken(_snapshot):
            raise RuntimeError("observer failure")

        self.store.subscribe(broken)
        unsubscribe = self.store.subscribe(received.append)
        self.store.register(self.overview)
        unsubscribe()
        unsubscribe()
        self.store.activate(self.overview.id)
        self.assertEqual(received, [self.store.snapshot.__class__(
            available=(self.overview,), revision=1
        )])

    def test_duplicate_subscription_is_not_repeated(self):
        received = []
        self.store.subscribe(received.append)
        self.store.subscribe(received.append)
        self.store.register(self.overview)
        self.assertEqual(len(received), 1)


class PerspectiveArchitectureTests(unittest.TestCase):
    def test_module_has_no_forbidden_dependencies(self):
        path = Path("presentation/perspectives.py")
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
        names = imports | imported_names
        forbidden = (
            "PySide",
            "PyQt",
            "domain",
            "application_state",
            "selection",
            "main_window",
            "facade",
        )
        for name in names:
            self.assertFalse(any(item in name for item in forbidden), name)

    def test_public_exports_are_intentional(self):
        expected = {
            "DuplicatePerspective",
            "InvalidPerspectiveDefinition",
            "PerspectiveContractError",
            "PerspectiveDefinition",
            "PerspectiveId",
            "PerspectiveNotRegistered",
            "PerspectiveSnapshot",
            "PerspectiveStore",
        }
        module = __import__(
            "presentation.perspectives", fromlist=["__all__"]
        )
        self.assertEqual(set(module.__all__), expected)
        self.assertTrue(expected.issubset(set(presentation.__all__)))


if __name__ == "__main__":
    unittest.main()
