from dataclasses import FrozenInstanceError
import ast
from pathlib import Path
from types import MappingProxyType
import unittest

import presentation
import presentation.selection as selection_module
from presentation.selection import (
    InvalidSelectionContext,
    InvalidSelectionIdentity,
    SelectionContext,
    SelectionIdentity,
    SelectionKind,
    SelectionSnapshot,
    SelectionStore,
)


def context(
    kind=SelectionKind.DOCUMENT,
    identifier="item-1",
    display_name="Item",
    metadata=None,
):
    return SelectionContext(
        SelectionIdentity(kind, identifier),
        display_name,
        {} if metadata is None else metadata,
    )


class SelectionKindAndIdentityTests(unittest.TestCase):
    def test_kind_values_are_complete_and_stable(self):
        self.assertEqual(
            tuple((item.name, item.value) for item in SelectionKind),
            (
                ("NONE", "none"),
                ("PROCESS", "process"),
                ("DOCUMENT", "document"),
                ("ACTIVITY", "activity"),
                ("EVIDENCE", "evidence"),
                (
                    "FUNCTIONAL_ASSIGNMENT",
                    "functional_assignment",
                ),
                ("FUNCTIONAL_EXERCISE", "functional_exercise"),
                ("REQUIREMENT", "requirement"),
            ),
        )

    def test_each_real_kind_accepts_a_stable_string_identifier(self):
        for kind in tuple(SelectionKind)[1:]:
            with self.subTest(kind=kind):
                identity = SelectionIdentity(kind, " item-1 ")
                self.assertEqual(identity.identifier, "item-1")

    def test_none_identity_is_canonical_structural_and_hashable(self):
        first = SelectionIdentity.none()
        second = SelectionIdentity(SelectionKind.NONE, "")

        self.assertEqual(first, second)
        self.assertEqual(first.identifier, None)
        self.assertEqual(hash(first), hash(second))
        self.assertEqual({first, second}, {first})

    def test_real_identity_rejects_empty_or_incompatible_identifier(self):
        for identifier in (None, "", "   ", 12, [], object()):
            with self.subTest(identifier=identifier):
                with self.assertRaises(InvalidSelectionIdentity):
                    SelectionIdentity(SelectionKind.DOCUMENT, identifier)

    def test_none_rejects_a_real_identifier_and_arbitrary_kind(self):
        with self.assertRaises(InvalidSelectionIdentity):
            SelectionIdentity(SelectionKind.NONE, "item-1")
        with self.assertRaises(InvalidSelectionIdentity):
            SelectionIdentity("document", "item-1")

    def test_identity_is_frozen_and_uses_slots(self):
        identity = SelectionIdentity(SelectionKind.PROCESS, "process-1")
        with self.assertRaises(FrozenInstanceError):
            identity.identifier = "other"
        with self.assertRaises(AttributeError):
            identity.extra = object()


class SelectionContextTests(unittest.TestCase):
    def test_valid_context_normalizes_name_and_has_structural_equality(self):
        first = context(
            display_name=" Item ",
            metadata={"number": 1, "active": True},
        )
        second = context(
            display_name="Item",
            metadata={"number": 1, "active": True},
        )

        self.assertEqual(first, second)
        self.assertEqual(first.display_name, "Item")
        self.assertIsInstance(first.metadata, MappingProxyType)

    def test_none_context_is_canonical(self):
        first = SelectionContext.none()
        second = SelectionContext(SelectionIdentity.none())

        self.assertEqual(first, second)
        self.assertEqual(first.identity.kind, SelectionKind.NONE)
        self.assertEqual(first.display_name, "")
        self.assertEqual(dict(first.metadata), {})

    def test_none_context_rejects_noncanonical_presentation_data(self):
        with self.assertRaises(InvalidSelectionContext):
            SelectionContext(SelectionIdentity.none(), "Selecionado")
        with self.assertRaises(InvalidSelectionContext):
            SelectionContext(
                SelectionIdentity.none(), metadata={"label": "valor"}
            )

    def test_metadata_is_deeply_frozen_and_defensively_copied(self):
        nested = {"label": "original"}
        source = {
            "nested": nested,
            "tuple": ({"value": 1}, "item"),
            "tags": frozenset(("a", "b")),
        }
        selection = context(metadata=source)

        source["new"] = "external"
        nested["label"] = "changed"

        self.assertNotIn("new", selection.metadata)
        self.assertEqual(
            selection.metadata["nested"]["label"], "original"
        )
        self.assertIsInstance(
            selection.metadata["nested"], MappingProxyType
        )
        self.assertIsInstance(
            selection.metadata["tuple"][0], MappingProxyType
        )
        with self.assertRaises(TypeError):
            selection.metadata["new"] = "blocked"
        with self.assertRaises(TypeError):
            selection.metadata["nested"]["label"] = "blocked"

    def test_metadata_rejects_mutable_or_arbitrary_values(self):
        incompatible = (
            ["mutable"],
            {"mutable"},
            bytearray(b"value"),
            lambda: None,
            object(),
        )
        for value in incompatible:
            with self.subTest(value=value):
                with self.assertRaises(InvalidSelectionContext):
                    context(metadata={"value": value})

    def test_metadata_rejects_invalid_keys_and_unhashable_frozenset_values(self):
        for metadata in (
            {" ": "value"},
            {1: "value"},
            {"items": frozenset()},
        ):
            if metadata == {"items": frozenset()}:
                self.assertEqual(context(metadata=metadata).metadata["items"], frozenset())
                continue
            with self.subTest(metadata=metadata):
                with self.assertRaises(InvalidSelectionContext):
                    context(metadata=metadata)

    def test_context_rejects_entity_like_objects_without_importing_domain(self):
        class Entity:
            pass

        with self.assertRaises(InvalidSelectionContext):
            context(metadata={"entity": Entity()})
        with self.assertRaises(InvalidSelectionContext):
            SelectionContext(object())

    def test_context_is_frozen_and_uses_slots(self):
        selection = context()
        with self.assertRaises(FrozenInstanceError):
            selection.display_name = "Other"
        with self.assertRaises(AttributeError):
            selection.widget = object()


class SelectionSnapshotAndStoreTests(unittest.TestCase):
    def setUp(self):
        self.store = SelectionStore()

    def test_initial_snapshot_is_none_revision_zero_and_frozen(self):
        snapshot = self.store.snapshot

        self.assertEqual(snapshot.selection, SelectionContext.none())
        self.assertEqual(snapshot.revision, 0)
        with self.assertRaises(FrozenInstanceError):
            snapshot.revision = 1

    def test_snapshot_rejects_invalid_selection_and_revision(self):
        with self.assertRaises(InvalidSelectionContext):
            SelectionSnapshot(selection=object())
        for revision in (-1, True, "1"):
            with self.subTest(revision=revision):
                with self.assertRaises(InvalidSelectionContext):
                    SelectionSnapshot(revision=revision)

    def test_store_selects_each_real_kind_with_exact_revision(self):
        for revision, kind in enumerate(tuple(SelectionKind)[1:], start=1):
            selected = self.store.select(
                context(kind, f"{kind.value}-1", kind.value.title())
            )
            self.assertEqual(selected.selection.identity.kind, kind)
            self.assertEqual(selected.revision, revision)

    def test_redundant_selection_preserves_snapshot_revision_and_observers(self):
        selection = context(metadata={"category": "A"})
        first = self.store.select(selection)
        observed = []
        self.store.subscribe(observed.append)

        second = self.store.select(
            context(metadata={"category": "A"})
        )

        self.assertIs(second, first)
        self.assertEqual(second.revision, 1)
        self.assertEqual(observed, [])

    def test_clear_changes_only_nonempty_selection(self):
        initial = self.store.snapshot
        self.assertIs(self.store.clear(), initial)

        self.store.select(context())
        cleared = self.store.clear()
        redundant = self.store.clear()

        self.assertEqual(cleared.selection, SelectionContext.none())
        self.assertEqual(cleared.revision, 2)
        self.assertIs(redundant, cleared)

    def test_invalid_input_preserves_snapshot_revision_and_notifications(self):
        before = self.store.snapshot
        observed = []
        self.store.subscribe(observed.append)

        with self.assertLogs("presentation.selection", level="WARNING"):
            with self.assertRaises(InvalidSelectionContext):
                self.store.select(object())

        self.assertIs(self.store.snapshot, before)
        self.assertEqual(observed, [])

    def test_observers_receive_new_snapshot_and_unsubscribe_is_idempotent(self):
        first_observed = []
        second_observed = []
        unsubscribe = self.store.subscribe(first_observed.append)
        self.store.subscribe(second_observed.append)

        first = self.store.select(context())
        unsubscribe()
        unsubscribe()
        second = self.store.clear()

        self.assertEqual(first_observed, [first])
        self.assertEqual(second_observed, [first, second])

    def test_observer_failure_is_logged_and_does_not_block_following_observers(self):
        observed = []

        def failing(_snapshot):
            raise RuntimeError("observer failure")

        self.store.subscribe(failing)
        self.store.subscribe(observed.append)

        with self.assertLogs("presentation.selection", level="ERROR"):
            result = self.store.select(context())

        self.assertIs(self.store.snapshot, result)
        self.assertEqual(observed, [result])

    def test_instances_are_isolated_and_not_singletons(self):
        other = SelectionStore()
        self.store.select(context())

        self.assertNotEqual(self.store.snapshot, other.snapshot)
        self.assertEqual(other.snapshot, SelectionSnapshot())


class SelectionArchitectureTests(unittest.TestCase):
    def test_public_exports_are_intentional(self):
        expected = {
            "InvalidSelectionContext",
            "InvalidSelectionIdentity",
            "SelectionContext",
            "SelectionContractError",
            "SelectionIdentity",
            "SelectionKind",
            "SelectionSnapshot",
            "SelectionStore",
        }
        self.assertEqual(set(selection_module.__all__), expected)
        self.assertTrue(expected.issubset(set(presentation.__all__)))
        for name in expected:
            self.assertIs(
                getattr(presentation, name),
                getattr(__import__(
                    "presentation.selection", fromlist=[name]
                ), name),
            )

    def test_selection_module_has_no_forbidden_imports_or_cycles(self):
        path = Path(__file__).parents[1] / "presentation" / "selection.py"
        tree = ast.parse(path.read_text(encoding="utf-8"))
        imports = {
            alias.name.lower()
            for node in ast.walk(tree)
            if isinstance(node, ast.Import)
            for alias in node.names
        }
        imports.update(
            (node.module or "").lower().lstrip(".")
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom)
        )
        forbidden = (
            "pyside",
            "pyqt",
            "applications.rsc",
            "application_state",
            "applicationfacade",
            "infrastructure",
            "repository",
            "ui",
        )
        self.assertFalse(
            any(
                token in imported
                for imported in imports
                for token in forbidden
            ),
            imports,
        )
        self.assertFalse(
            any(isinstance(node, ast.ImportFrom) and node.level for node in ast.walk(tree))
        )

    def test_selection_dtos_are_frozen_slotted_dataclasses(self):
        path = Path(__file__).parents[1] / "presentation" / "selection.py"
        tree = ast.parse(path.read_text(encoding="utf-8"))
        expected = {
            "SelectionIdentity",
            "SelectionContext",
            "SelectionSnapshot",
        }
        decorators = {
            node.name: tuple(ast.unparse(item) for item in node.decorator_list)
            for node in ast.walk(tree)
            if isinstance(node, ast.ClassDef) and node.name in expected
        }
        self.assertEqual(set(decorators), expected)
        for values in decorators.values():
            self.assertTrue(
                any(
                    "frozen=True" in item and "slots=True" in item
                    for item in values
                ),
                values,
            )


if __name__ == "__main__":
    unittest.main()
