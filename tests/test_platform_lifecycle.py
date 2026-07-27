from dataclasses import FrozenInstanceError
from pathlib import Path
import unittest

from contracts.lifecycle import (
    VALID_APPLICATION_LIFECYCLE_TRANSITIONS,
    ApplicationLifecycleState,
    ApplicationLifecycleTransition,
)


class ApplicationLifecycleContractTests(unittest.TestCase):
    def test_defines_expected_stable_states(self):
        self.assertEqual(
            {state.value for state in ApplicationLifecycleState},
            {
                "discovered",
                "registered",
                "project_prepared",
                "session_created",
                "presentation_mounted",
                "active",
                "deactivating",
                "disposed",
            },
        )

    def test_accepts_every_declared_transition_as_immutable_value(self):
        for source, target in VALID_APPLICATION_LIFECYCLE_TRANSITIONS:
            with self.subTest(source=source, target=target):
                transition = ApplicationLifecycleTransition(source, target)
                self.assertEqual(transition.source, source)
                self.assertEqual(transition.target, target)
                with self.assertRaises(FrozenInstanceError):
                    transition.target = source

    def test_rejects_skips_reactivation_and_equal_states(self):
        invalid = (
            (
                ApplicationLifecycleState.DISCOVERED,
                ApplicationLifecycleState.ACTIVE,
            ),
            (
                ApplicationLifecycleState.ACTIVE,
                ApplicationLifecycleState.ACTIVE,
            ),
            (
                ApplicationLifecycleState.DISPOSED,
                ApplicationLifecycleState.REGISTERED,
            ),
        )
        for source, target in invalid:
            with self.subTest(source=source, target=target):
                with self.assertRaises(ValueError):
                    ApplicationLifecycleTransition(source, target)

    def test_rejects_values_outside_the_state_contract(self):
        with self.assertRaises(TypeError):
            ApplicationLifecycleTransition(
                "discovered",
                ApplicationLifecycleState.REGISTERED,
            )

    def test_contract_has_no_qt_rsc_or_dispatcher_dependency(self):
        source = (
            Path(__file__).parents[1] / "contracts" / "lifecycle.py"
        ).read_text(encoding="utf-8")

        for forbidden in (
            "PySide6",
            "applications.rsc",
            "Dispatcher",
            "Signal",
            "Event",
        ):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, source)


if __name__ == "__main__":
    unittest.main()
