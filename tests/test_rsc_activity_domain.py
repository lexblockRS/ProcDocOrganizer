from dataclasses import FrozenInstanceError
import unittest

from applications.rsc.models import (
    Activity,
    ActivityState,
    FunctionalAssignmentEvidenceId,
    FunctionalExerciseId,
)


EVIDENCE_ID = FunctionalAssignmentEvidenceId(
    "12345678-1234-5678-1234-567812345678"
)
EXERCISE_ID = FunctionalExerciseId(
    "87654321-4321-8765-4321-876543218765"
)


def activity(**changes):
    values = {
        "activity_id": "activity-1",
        "description": "Fiscalização de contrato",
    }
    values.update(changes)
    return Activity(**values)


class ActivityTests(unittest.TestCase):
    def test_creates_remembered_activity_without_relations(self):
        item = activity()

        self.assertEqual(item.state, ActivityState.REMEMBERED)
        self.assertEqual(item.functional_assignment_evidence_ids, ())
        self.assertEqual(item.functional_exercise_ids, ())

    def test_normalizes_identity_and_description(self):
        item = activity(
            activity_id="  activity-1  ",
            description="  Fiscalização   de contrato  ",
        )

        self.assertEqual(item.activity_id, "activity-1")
        self.assertEqual(item.description, "Fiscalização de contrato")

    def test_rejects_empty_identity_and_description(self):
        for field in ("activity_id", "description"):
            with self.subTest(field=field):
                with self.assertRaises(ValueError):
                    activity(**{field: " "})

    def test_rejects_untyped_state_and_relations(self):
        invalid_values = (
            {"state": "lembrada"},
            {"functional_assignment_evidence_ids": (object(),)},
            {"functional_exercise_ids": (object(),)},
        )
        for values in invalid_values:
            with self.subTest(values=values):
                with self.assertRaises(TypeError):
                    activity(**values)

    def test_rejects_duplicate_relations(self):
        with self.assertRaises(ValueError):
            activity(
                functional_assignment_evidence_ids=(
                    EVIDENCE_ID,
                    EVIDENCE_ID,
                )
            )
        with self.assertRaises(ValueError):
            activity(
                functional_exercise_ids=(EXERCISE_ID, EXERCISE_ID)
            )

    def test_is_immutable(self):
        item = activity()

        with self.assertRaises(FrozenInstanceError):
            item.description = "Outra"

    def test_evolves_through_the_complete_flow(self):
        remembered = activity()
        investigating = remembered.start_investigation()
        with_evidence = investigating.relate_assignment_evidence(EVIDENCE_ID)
        partially_proven = with_evidence.mark_partially_proven()
        with_exercise = partially_proven.relate_functional_exercise(
            EXERCISE_ID
        )
        proven = with_exercise.mark_proven()

        self.assertEqual(remembered.state, ActivityState.REMEMBERED)
        self.assertEqual(
            investigating.state,
            ActivityState.UNDER_INVESTIGATION,
        )
        self.assertEqual(
            partially_proven.state,
            ActivityState.PARTIALLY_PROVEN,
        )
        self.assertEqual(proven.state, ActivityState.PROVEN)

    def test_rejects_skipped_or_repeated_transitions(self):
        with self.assertRaises(ValueError):
            activity().mark_partially_proven()
        with self.assertRaises(ValueError):
            activity().mark_proven()
        with self.assertRaises(ValueError):
            activity().start_investigation().start_investigation()

    def test_partial_proof_requires_evidence(self):
        with self.assertRaises(ValueError):
            activity(
                state=ActivityState.PARTIALLY_PROVEN,
            )

    def test_proof_requires_evidence_and_exercise(self):
        with self.assertRaises(ValueError):
            activity(
                state=ActivityState.PROVEN,
                functional_assignment_evidence_ids=(EVIDENCE_ID,),
            )
        with self.assertRaises(ValueError):
            activity(
                state=ActivityState.PROVEN,
                functional_exercise_ids=(EXERCISE_ID,),
            )

    def test_relations_are_idempotent_and_preserve_order(self):
        first_evidence = EVIDENCE_ID
        second_evidence = FunctionalAssignmentEvidenceId(
            "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
        )
        item = (
            activity()
            .relate_assignment_evidence(first_evidence)
            .relate_assignment_evidence(second_evidence)
            .relate_assignment_evidence(first_evidence)
            .relate_functional_exercise(EXERCISE_ID)
            .relate_functional_exercise(EXERCISE_ID)
        )

        self.assertEqual(
            item.functional_assignment_evidence_ids,
            (first_evidence, second_evidence),
        )
        self.assertEqual(item.functional_exercise_ids, (EXERCISE_ID,))

    def test_relationship_methods_reject_wrong_id_types(self):
        with self.assertRaises(TypeError):
            activity().relate_assignment_evidence(EXERCISE_ID)
        with self.assertRaises(TypeError):
            activity().relate_functional_exercise(EVIDENCE_ID)


if __name__ == "__main__":
    unittest.main()
