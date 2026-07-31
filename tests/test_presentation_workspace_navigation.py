import ast
from dataclasses import FrozenInstanceError
from pathlib import Path
import unittest

from presentation import (
    ApplicationStateStore,
    NavigationContractError,
    NavigationController,
    NavigationIntent,
    NavigationIntentType,
    PerspectiveDefinition,
    PerspectiveId,
    PerspectiveStore,
    PresentationContextStore,
    SelectionKind,
    SelectionStore,
    WorkspaceFilter,
    WorkspaceStore,
)


def perspective(value="home"):
    return PerspectiveDefinition(
        PerspectiveId(value), "Início", 10, None, False, lambda: object()
    )


class NavigationIntentContractTests(unittest.TestCase):
    def test_deep_navigation_factories_use_one_typed_contract(self):
        values = (
            (NavigationIntent.open_dashboard(), NavigationIntentType.OPEN_DASHBOARD),
            (NavigationIntent.open_document("doc"), NavigationIntentType.OPEN_DOCUMENT),
            (NavigationIntent.open_evidence("ev"), NavigationIntentType.OPEN_EVIDENCE),
            (NavigationIntent.open_execution_fact("fact"), NavigationIntentType.OPEN_EXECUTION_FACT),
            (NavigationIntent.open_requirement("req"), NavigationIntentType.OPEN_REQUIREMENT),
            (NavigationIntent.open_criterion("criterion"), NavigationIntentType.OPEN_CRITERION),
            (NavigationIntent.open_evaluation("evaluation"), NavigationIntentType.OPEN_EVALUATION),
            (NavigationIntent.open_report("report"), NavigationIntentType.OPEN_REPORT),
        )
        for intent, expected in values:
            with self.subTest(expected=expected):
                self.assertIs(intent.intent_type, expected)
                self.assertFalse(hasattr(intent, "__dict__"))

    def test_intent_filters_and_metadata_are_deeply_immutable(self):
        source = {"state": "unused"}
        filter_ = WorkspaceFilter("documents", source)
        intent = NavigationIntent.open_document(
            "doc-1", filters=(filter_,), metadata={"source": "dashboard"}
        )
        source["state"] = "changed"

        self.assertEqual(filter_.parameters["state"], "unused")
        with self.assertRaises(TypeError):
            intent.metadata["source"] = "other"
        with self.assertRaises(FrozenInstanceError):
            intent.target_id = "doc-2"

    def test_rejects_untyped_or_non_scalar_contract_values(self):
        with self.assertRaises(NavigationContractError):
            NavigationIntent("open_document", "doc")
        with self.assertRaises(NavigationContractError):
            NavigationIntent.open_document("doc", metadata={"entity": object()})
        with self.assertRaises(NavigationContractError):
            NavigationIntent.open_document("doc", filters=("unused",))


class PresentationWorkspaceNavigationTests(unittest.TestCase):
    def setUp(self):
        self.application = ApplicationStateStore()
        self.selections = SelectionStore()
        self.perspectives = PerspectiveStore()
        self.home = perspective()
        self.perspectives.register(self.home)
        self.workspace = WorkspaceStore(self.perspectives)
        self.context = PresentationContextStore(
            self.application,
            self.selections,
            self.perspectives,
            self.workspace,
        )
        self.navigation = NavigationController(
            self.perspectives,
            self.workspace,
            self.selections,
            presentation_context=self.context,
        )

    def test_transition_updates_context_atomically_and_records_history(self):
        before = self.context.snapshot.revision
        intent = NavigationIntent(
            NavigationIntentType.OPEN_PERSPECTIVE, self.home.id.value
        )

        result = self.navigation.navigate(intent)

        self.assertEqual(self.context.snapshot.revision, before + 1)
        self.assertIs(self.context.snapshot.workspace, result)
        self.assertEqual(result.perspective, self.home.id)
        self.assertEqual(self.navigation.history[-1].intent, intent)
        self.assertIs(self.navigation.history[-1].snapshot, result)

    def test_deep_navigation_updates_selection_filters_and_revision(self):
        self.navigation.navigate_to(self.home.id)
        filter_ = WorkspaceFilter("unused_documents", {"critical": False})
        before = self.context.snapshot.revision

        result = self.navigation.navigate(NavigationIntent.open_document(
            "document-1",
            project_id="project-1",
            filters=(filter_,),
            metadata={"origin": "dashboard"},
        ))

        self.assertEqual(self.context.snapshot.revision, before + 1)
        self.assertEqual(result.current_document, "document-1")
        self.assertEqual(result.project_id, "project-1")
        self.assertEqual(result.active_filters, (filter_,))
        self.assertIs(
            result.selection.identity.kind, SelectionKind.DOCUMENT
        )
        self.assertEqual(
            self.selections.snapshot.selection.identity.identifier,
            "document-1",
        )

    def test_snapshots_and_history_are_immutable_and_noop_is_not_duplicated(self):
        intent = NavigationIntent.open_evidence("evidence-1")
        first = self.navigation.navigate(intent)
        history = self.navigation.history
        second = self.navigation.navigate(intent)

        self.assertIs(first, second)
        self.assertEqual(self.navigation.history, history)
        with self.assertRaises(FrozenInstanceError):
            first.current_evidence = "other"
        with self.assertRaises(AttributeError):
            history.append("invalid")

    def test_history_boundaries_and_single_entry_are_safe(self):
        self.assertIsNone(self.navigation.history_position)
        self.assertFalse(self.navigation.can_go_back)
        self.assertFalse(self.navigation.can_go_forward)
        self.assertFalse(self.navigation.go_back())
        self.assertFalse(self.navigation.go_forward())
        self.assertFalse(self.navigation.restore_current())

        self.navigation.navigate_to(self.home.id)

        self.assertEqual(self.navigation.history_position, 0)
        self.assertFalse(self.navigation.can_go_back)
        self.assertFalse(self.navigation.can_go_forward)

    def test_back_and_forward_restore_snapshot_without_new_entries(self):
        self.navigation.navigate_to(self.home.id)
        filter_ = WorkspaceFilter("review.category", {"value": "documents"})
        review = self.navigation.navigate(NavigationIntent(
            NavigationIntentType.OPEN_PERSPECTIVE,
            self.home.id.value,
            project_id="project-1",
            filters=(filter_,),
            metadata={"screen": "review"},
        ))
        explorer = self.navigation.navigate(NavigationIntent.open_document(
            "document-1",
            project_id="project-1",
            metadata={"screen": "explorer"},
        ))
        history = self.navigation.history

        restored_review = self.navigation.go_back()

        self.assertEqual(len(self.navigation.history), len(history))
        self.assertEqual(self.navigation.history_position, 1)
        self.assertEqual(restored_review.active_filters, review.active_filters)
        self.assertEqual(restored_review.metadata, review.metadata)
        self.assertEqual(
            self.selections.snapshot.selection, review.selection
        )
        self.assertTrue(self.navigation.can_go_forward)

        restored_explorer = self.navigation.go_forward()

        self.assertEqual(len(self.navigation.history), len(history))
        self.assertEqual(restored_explorer.selection, explorer.selection)
        self.assertEqual(
            self.workspace.snapshot.current_document,
            "document-1",
        )
        self.assertFalse(self.navigation.can_go_forward)

    def test_new_navigation_after_back_discards_future_branch(self):
        self.navigation.navigate_to(self.home.id)
        self.navigation.navigate(NavigationIntent.open_document("document-1"))
        self.navigation.navigate(NavigationIntent.open_evidence("evidence-1"))
        self.navigation.go_back()

        self.navigation.navigate(
            NavigationIntent.open_requirement("requirement-1")
        )

        self.assertEqual(len(self.navigation.history), 3)
        self.assertIs(
            self.navigation.history[-1].intent.intent_type,
            NavigationIntentType.OPEN_REQUIREMENT,
        )
        self.assertFalse(self.navigation.can_go_forward)

    def test_clear_history_resets_cursor_and_boundaries(self):
        self.navigation.navigate_to(self.home.id)
        self.navigation.clear_history()

        self.assertEqual(self.navigation.history, ())
        self.assertIsNone(self.navigation.history_position)
        self.assertFalse(self.navigation.go_back())
        self.assertFalse(self.navigation.go_forward())

    def test_typed_route_activates_registered_perspective(self):
        self.navigation.register_route(
            NavigationIntentType.OPEN_DOCUMENT, self.home.id
        )

        result = self.navigation.navigate(
            NavigationIntent.open_document("document-1")
        )

        self.assertEqual(result.active_perspective, self.home.id)
        self.assertEqual(result.current_document, "document-1")

    def test_history_restore_publishes_one_consolidated_context(self):
        self.navigation.navigate_to(self.home.id)
        self.navigation.navigate(
            NavigationIntent.open_document("document-1")
        )
        observed = []
        self.context.subscribe(observed.append)

        before = self.context.snapshot.revision
        self.navigation.go_back()

        self.assertEqual(len(observed), 1)
        self.assertEqual(self.context.snapshot.revision, before + 1)


class PresentationNavigationArchitectureTests(unittest.TestCase):
    def test_contracts_have_no_toolkit_domain_or_infrastructure_imports(self):
        for filename in (
            "presentation/navigation_contracts.py",
            "presentation/workspace.py",
            "presentation/navigation.py",
        ):
            tree = ast.parse(Path(filename).read_text(encoding="utf-8"))
            modules = {
                node.module or ""
                for node in ast.walk(tree)
                if isinstance(node, ast.ImportFrom)
            }
            for module in modules:
                lowered = module.casefold()
                self.assertFalse(any(name in lowered for name in (
                    "pyside", "pyqt", "domain", "database",
                    "infrastructure", "platform_sdk",
                )), (filename, module))

    def test_dashboard_view_emits_intent_without_importing_other_views(self):
        tree = ast.parse(
            Path("ui/workspace_dashboard.py").read_text(encoding="utf-8")
        )
        modules = {
            node.module or ""
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom)
        }
        self.assertFalse(any(module.startswith("ui.") for module in modules))


if __name__ == "__main__":
    unittest.main()
