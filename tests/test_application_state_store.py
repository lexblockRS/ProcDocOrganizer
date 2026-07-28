from dataclasses import FrozenInstanceError
import unittest

from presentation.application_state import (
    ApplicationState,
    ApplicationStateSnapshot,
    ApplicationStateStore,
    InvalidApplicationStateTransition,
)


class ApplicationStateStoreTests(unittest.TestCase):
    def setUp(self):
        self.store = ApplicationStateStore()

    def test_initial_state_and_snapshot_are_immutable(self):
        snapshot = self.store.snapshot

        self.assertEqual(snapshot.state, ApplicationState.NO_PROJECT)
        self.assertIsNone(snapshot.previous_state)
        self.assertIsNone(snapshot.active_operation_id)
        self.assertIsNone(snapshot.project_id)
        self.assertFalse(snapshot.has_project)
        self.assertFalse(snapshot.is_modified)
        self.assertIsNone(snapshot.error)
        self.assertEqual(snapshot.revision, 0)
        with self.assertRaises(FrozenInstanceError):
            snapshot.state = ApplicationState.ERROR

    def test_valid_project_lifecycle_transitions_preserve_invariants(self):
        opened = self.store.transition_to(
            ApplicationState.PROJECT_OPEN, project_id="project-1"
        )
        modified = self.store.transition_to(
            ApplicationState.PROJECT_MODIFIED
        )
        saved = self.store.transition_to(ApplicationState.PROJECT_OPEN)
        closed = self.store.transition_to(ApplicationState.NO_PROJECT)

        self.assertTrue(opened.has_project)
        self.assertFalse(opened.is_modified)
        self.assertTrue(modified.has_project)
        self.assertTrue(modified.is_modified)
        self.assertEqual(saved.project_id, "project-1")
        self.assertFalse(saved.is_modified)
        self.assertFalse(closed.has_project)
        self.assertIsNone(closed.project_id)
        self.assertEqual(closed.revision, 4)

    def test_all_documented_direct_transitions(self):
        cases = (
            (ApplicationState.NO_PROJECT, ApplicationState.PROJECT_OPEN),
            (ApplicationState.NO_PROJECT, ApplicationState.ERROR),
            (ApplicationState.NO_PROJECT, ApplicationState.CLOSING),
            (ApplicationState.PROJECT_OPEN, ApplicationState.NO_PROJECT),
            (
                ApplicationState.PROJECT_OPEN,
                ApplicationState.PROJECT_MODIFIED,
            ),
            (ApplicationState.PROJECT_OPEN, ApplicationState.ERROR),
            (ApplicationState.PROJECT_OPEN, ApplicationState.CLOSING),
            (
                ApplicationState.PROJECT_MODIFIED,
                ApplicationState.NO_PROJECT,
            ),
            (
                ApplicationState.PROJECT_MODIFIED,
                ApplicationState.PROJECT_OPEN,
            ),
            (
                ApplicationState.PROJECT_MODIFIED,
                ApplicationState.ERROR,
            ),
            (
                ApplicationState.PROJECT_MODIFIED,
                ApplicationState.CLOSING,
            ),
            (ApplicationState.ERROR, ApplicationState.NO_PROJECT),
            (ApplicationState.ERROR, ApplicationState.PROJECT_OPEN),
            (ApplicationState.ERROR, ApplicationState.PROJECT_MODIFIED),
            (ApplicationState.ERROR, ApplicationState.CLOSING),
        )
        for source, target in cases:
            with self.subTest(source=source, target=target):
                store = self._store_in_state(source)
                values = {}
                if target in (
                    ApplicationState.PROJECT_OPEN,
                    ApplicationState.PROJECT_MODIFIED,
                ) and store.snapshot.project_id is None:
                    values["project_id"] = "project-1"
                if target is ApplicationState.ERROR:
                    values["error"] = "falha"
                result = store.transition_to(target, **values)
                self.assertEqual(result.state, target)

    def test_all_undocumented_direct_transitions_are_rejected_atomically(self):
        allowed = {
            ApplicationState.NO_PROJECT: {
                ApplicationState.PROJECT_OPEN,
                ApplicationState.ERROR,
                ApplicationState.CLOSING,
            },
            ApplicationState.PROJECT_OPEN: {
                ApplicationState.NO_PROJECT,
                ApplicationState.PROJECT_MODIFIED,
                ApplicationState.ERROR,
                ApplicationState.CLOSING,
            },
            ApplicationState.PROJECT_MODIFIED: {
                ApplicationState.NO_PROJECT,
                ApplicationState.PROJECT_OPEN,
                ApplicationState.ERROR,
                ApplicationState.CLOSING,
            },
            ApplicationState.ERROR: {
                ApplicationState.NO_PROJECT,
                ApplicationState.PROJECT_OPEN,
                ApplicationState.PROJECT_MODIFIED,
                ApplicationState.CLOSING,
            },
            ApplicationState.BUSY: set(),
            ApplicationState.CLOSING: set(),
        }
        for source in ApplicationState:
            for target in ApplicationState:
                if target in allowed[source]:
                    continue
                with self.subTest(source=source, target=target):
                    store = self._store_in_state(source)
                    before = store.snapshot
                    observed = []
                    store.subscribe(observed.append)
                    with self.assertLogs(
                        "presentation.application_state", level="WARNING"
                    ):
                        with self.assertRaises(
                            InvalidApplicationStateTransition
                        ):
                            store.transition_to(target)
                    self.assertIs(store.snapshot, before)
                    self.assertEqual(observed, [])

    def test_busy_complete_restores_previous_state(self):
        self.store.transition_to(
            ApplicationState.PROJECT_OPEN, project_id="project-1"
        )
        before = self.store.snapshot
        busy = self.store.begin_operation("save-1")
        restored = self.store.complete_operation("save-1")

        self.assertEqual(busy.state, ApplicationState.BUSY)
        self.assertEqual(
            busy.previous_state, ApplicationState.PROJECT_OPEN
        )
        self.assertEqual(busy.active_operation_id, "save-1")
        self.assertEqual(restored.state, before.state)
        self.assertEqual(restored.project_id, before.project_id)
        self.assertIsNone(restored.previous_state)
        self.assertIsNone(restored.active_operation_id)

    def test_operation_can_complete_with_new_stable_state(self):
        self.store.begin_operation("open-1")

        result = self.store.complete_operation(
            "open-1",
            resulting_state=ApplicationState.PROJECT_OPEN,
            project_id="project-1",
        )

        self.assertEqual(result.state, ApplicationState.PROJECT_OPEN)
        self.assertEqual(result.project_id, "project-1")

    def test_cancel_restores_modified_state(self):
        self.store.transition_to(
            ApplicationState.PROJECT_OPEN, project_id="project-1"
        )
        self.store.transition_to(ApplicationState.PROJECT_MODIFIED)
        self.store.begin_operation("verify-1")

        restored = self.store.cancel_operation("verify-1")

        self.assertEqual(restored.state, ApplicationState.PROJECT_MODIFIED)
        self.assertTrue(restored.is_modified)
        self.assertEqual(restored.project_id, "project-1")

    def test_failed_operation_enters_error_without_losing_project_context(self):
        self.store.transition_to(
            ApplicationState.PROJECT_OPEN, project_id="project-1"
        )
        self.store.transition_to(ApplicationState.PROJECT_MODIFIED)
        self.store.begin_operation("save-1")

        result = self.store.fail_operation("save-1", "Falha ao salvar")

        self.assertEqual(result.state, ApplicationState.ERROR)
        self.assertEqual(
            result.previous_state, ApplicationState.PROJECT_MODIFIED
        )
        self.assertEqual(result.error, "Falha ao salvar")
        self.assertTrue(result.has_project)
        self.assertTrue(result.is_modified)

    def test_wrong_operation_id_does_not_change_or_notify(self):
        self.store.begin_operation("open-1")
        before = self.store.snapshot
        observed = []
        self.store.subscribe(observed.append)

        with self.assertRaises(InvalidApplicationStateTransition):
            self.store.complete_operation("other")

        self.assertIs(self.store.snapshot, before)
        self.assertEqual(observed, [])

    def test_revision_and_observer_change_once_per_success(self):
        observed = []
        unsubscribe = self.store.subscribe(observed.append)

        first = self.store.transition_to(
            ApplicationState.PROJECT_OPEN, project_id="project-1"
        )
        second = self.store.transition_to(
            ApplicationState.PROJECT_MODIFIED
        )
        unsubscribe()
        self.store.transition_to(ApplicationState.PROJECT_OPEN)

        self.assertEqual((first.revision, second.revision), (1, 2))
        self.assertEqual(observed, [first, second])

    def test_observer_failure_does_not_corrupt_state_or_other_observers(self):
        observed = []

        def failing(_snapshot):
            raise RuntimeError("observer failure")

        self.store.subscribe(failing)
        self.store.subscribe(observed.append)

        with self.assertLogs(
            "presentation.application_state", level="ERROR"
        ):
            result = self.store.transition_to(
                ApplicationState.PROJECT_OPEN, project_id="project-1"
            )

        self.assertIs(self.store.snapshot, result)
        self.assertEqual(observed, [result])

    def test_snapshot_constructor_enforces_invariants(self):
        invalid_values = (
            {"state": ApplicationState.NO_PROJECT, "project_id": "p"},
            {
                "state": ApplicationState.PROJECT_OPEN,
                "project_id": "p",
                "has_project": True,
                "is_modified": True,
            },
            {
                "state": ApplicationState.PROJECT_MODIFIED,
                "project_id": "p",
                "has_project": True,
                "is_modified": False,
            },
            {"state": ApplicationState.BUSY},
            {"state": ApplicationState.ERROR},
            {
                "state": ApplicationState.CLOSING,
                "active_operation_id": "operation",
            },
        )
        for values in invalid_values:
            with self.subTest(values=values):
                with self.assertRaises(ValueError):
                    ApplicationStateSnapshot(**values)

    def test_closing_is_terminal_and_rejects_new_operations(self):
        closing = self.store.transition_to(ApplicationState.CLOSING)

        for action in (
            lambda: self.store.transition_to(ApplicationState.NO_PROJECT),
            lambda: self.store.begin_operation("late-operation"),
        ):
            with self.subTest(action=action):
                with self.assertRaises(InvalidApplicationStateTransition):
                    action()
                self.assertIs(self.store.snapshot, closing)

    @staticmethod
    def _store_in_state(state):
        store = ApplicationStateStore()
        if state is ApplicationState.NO_PROJECT:
            return store
        if state is ApplicationState.PROJECT_OPEN:
            store.transition_to(state, project_id="project-1")
        elif state is ApplicationState.PROJECT_MODIFIED:
            store.transition_to(
                ApplicationState.PROJECT_OPEN, project_id="project-1"
            )
            store.transition_to(state)
        elif state is ApplicationState.ERROR:
            store.transition_to(
                ApplicationState.PROJECT_OPEN, project_id="project-1"
            )
            store.transition_to(state, error="falha")
        elif state is ApplicationState.BUSY:
            store.begin_operation("operation-1")
        elif state is ApplicationState.CLOSING:
            store.transition_to(state)
        return store


if __name__ == "__main__":
    unittest.main()
