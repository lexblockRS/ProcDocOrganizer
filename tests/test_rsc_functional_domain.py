from dataclasses import FrozenInstanceError
from datetime import date, datetime
import unittest

from applications.rsc.models import (
    Activity,
    FunctionalContext,
    FunctionalExercise,
    FunctionalExerciseId,
    FunctionalExerciseStatus,
    FunctionalExerciseType,
    FunctionalPeriod,
    FunctionalRole,
    Project,
)


UUID_TEXT = "12345678-1234-5678-1234-567812345678"


def exercise(
    *,
    period=None,
    status=FunctionalExerciseStatus.ACTIVE,
    person_id="person-1",
):
    return FunctionalExercise(
        id=FunctionalExerciseId(UUID_TEXT),
        person_id=person_id,
        exercise_type=FunctionalExerciseType("gestao", "Gestão"),
        role=FunctionalRole("Presidente"),
        context=FunctionalContext("Instituição"),
        period=period or FunctionalPeriod(date(2024, 1, 1)),
        status=status,
    )


class FunctionalExerciseIdTests(unittest.TestCase):
    def test_accepts_valid_uuid(self):
        identifier = FunctionalExerciseId(UUID_TEXT)

        self.assertEqual(identifier.value, UUID_TEXT)

    def test_normalizes_uuid(self):
        identifier = FunctionalExerciseId(
            "12345678123456781234567812345678"
        )

        self.assertEqual(identifier.value, UUID_TEXT)

    def test_removes_external_spaces(self):
        identifier = FunctionalExerciseId(f"  {UUID_TEXT}  ")

        self.assertEqual(identifier.value, UUID_TEXT)

    def test_rejects_empty_value(self):
        with self.assertRaises(ValueError):
            FunctionalExerciseId("  ")

    def test_rejects_invalid_uuid(self):
        with self.assertRaises(ValueError):
            FunctionalExerciseId("not-a-uuid")

    def test_rejects_invalid_type(self):
        with self.assertRaises(TypeError):
            FunctionalExerciseId(None)

    def test_string_returns_normalized_value(self):
        identifier = FunctionalExerciseId.from_string(
            "12345678123456781234567812345678"
        )

        self.assertEqual(str(identifier), UUID_TEXT)


class FunctionalExerciseTypeTests(unittest.TestCase):
    def test_creates_valid_type(self):
        exercise_type = FunctionalExerciseType(
            "fiscal_contrato",
            "Fiscalização de contrato",
        )

        self.assertEqual(exercise_type.code, "fiscal_contrato")
        self.assertEqual(
            exercise_type.label,
            "Fiscalização de contrato",
        )

    def test_normalizes_code(self):
        exercise_type = FunctionalExerciseType(
            "  Fiscal Contrato-A  ",
            "Fiscal",
        )

        self.assertEqual(exercise_type.code, "fiscal_contrato-a")

    def test_normalizes_label_spaces(self):
        exercise_type = FunctionalExerciseType(
            "fiscal",
            "  Fiscalização   de contrato  ",
        )

        self.assertEqual(
            exercise_type.label,
            "Fiscalização de contrato",
        )

    def test_rejects_empty_code(self):
        with self.assertRaises(ValueError):
            FunctionalExerciseType(" ", "Fiscal")

    def test_rejects_empty_label(self):
        with self.assertRaises(ValueError):
            FunctionalExerciseType("fiscal", " ")

    def test_rejects_invalid_types(self):
        with self.assertRaises(TypeError):
            FunctionalExerciseType(None, "Fiscal")
        with self.assertRaises(TypeError):
            FunctionalExerciseType("fiscal", None)

    def test_equality_is_by_value(self):
        self.assertEqual(
            FunctionalExerciseType(" Fiscal ", " Fiscal "),
            FunctionalExerciseType("fiscal", "Fiscal"),
        )


class FunctionalRoleTests(unittest.TestCase):
    def test_creates_valid_role(self):
        self.assertEqual(
            FunctionalRole("Presidente").name,
            "Presidente",
        )

    def test_normalizes_spaces(self):
        self.assertEqual(
            FunctionalRole("  Representante   institucional ").name,
            "Representante institucional",
        )

    def test_rejects_empty_name(self):
        with self.assertRaises(ValueError):
            FunctionalRole(" ")

    def test_rejects_invalid_type(self):
        with self.assertRaises(TypeError):
            FunctionalRole(None)


class FunctionalContextTests(unittest.TestCase):
    def test_creates_context_with_only_organization(self):
        context = FunctionalContext("Instituição")

        self.assertEqual(context.organization, "Instituição")
        self.assertIsNone(context.unit)
        self.assertIsNone(context.reference)

    def test_creates_complete_context(self):
        context = FunctionalContext(
            "Instituição",
            "Comissão",
            "Processo 123",
        )

        self.assertEqual(context.unit, "Comissão")
        self.assertEqual(context.reference, "Processo 123")

    def test_normalizes_spaces(self):
        context = FunctionalContext(
            "  Instituto   Federal ",
            " Comissão   Permanente ",
            " Processo   123 ",
        )

        self.assertEqual(context.organization, "Instituto Federal")
        self.assertEqual(context.unit, "Comissão Permanente")
        self.assertEqual(context.reference, "Processo 123")

    def test_rejects_empty_organization(self):
        with self.assertRaises(ValueError):
            FunctionalContext(" ")

    def test_rejects_empty_unit_when_provided(self):
        with self.assertRaises(ValueError):
            FunctionalContext("Instituição", unit=" ")

    def test_rejects_empty_reference_when_provided(self):
        with self.assertRaises(ValueError):
            FunctionalContext("Instituição", reference=" ")

    def test_rejects_invalid_types(self):
        with self.assertRaises(TypeError):
            FunctionalContext(None)
        with self.assertRaises(TypeError):
            FunctionalContext("Instituição", unit=123)
        with self.assertRaises(TypeError):
            FunctionalContext("Instituição", reference=123)


class FunctionalExerciseStatusTests(unittest.TestCase):
    def test_has_exactly_active_and_ended(self):
        self.assertEqual(
            tuple(FunctionalExerciseStatus),
            (
                FunctionalExerciseStatus.ACTIVE,
                FunctionalExerciseStatus.ENDED,
            ),
        )

    def test_has_expected_text_values(self):
        self.assertEqual(FunctionalExerciseStatus.ACTIVE.value, "active")
        self.assertEqual(FunctionalExerciseStatus.ENDED.value, "ended")


class FunctionalPeriodTests(unittest.TestCase):
    def test_creates_open_period(self):
        period = FunctionalPeriod(date(2024, 1, 1))

        self.assertTrue(period.is_open)
        self.assertFalse(period.is_closed)

    def test_creates_closed_period(self):
        period = FunctionalPeriod(
            date(2024, 1, 1),
            date(2024, 12, 31),
        )

        self.assertFalse(period.is_open)
        self.assertTrue(period.is_closed)

    def test_accepts_equal_start_and_end(self):
        target = date(2024, 1, 1)

        self.assertEqual(
            FunctionalPeriod(target, target).end_date,
            target,
        )

    def test_rejects_end_before_start(self):
        with self.assertRaises(ValueError):
            FunctionalPeriod(
                date(2024, 1, 2),
                date(2024, 1, 1),
            )

    def test_rejects_invalid_types(self):
        with self.assertRaises(TypeError):
            FunctionalPeriod("2024-01-01")
        with self.assertRaises(TypeError):
            FunctionalPeriod(date(2024, 1, 1), "2024-01-02")
        with self.assertRaises(TypeError):
            FunctionalPeriod(date(2024, 1, 1)).contains("2024-01-01")

    def test_rejects_datetime(self):
        instant = datetime(2024, 1, 1)

        with self.assertRaises(TypeError):
            FunctionalPeriod(instant)
        with self.assertRaises(TypeError):
            FunctionalPeriod(date(2024, 1, 1), instant)
        with self.assertRaises(TypeError):
            FunctionalPeriod(date(2024, 1, 1)).contains(instant)

    def test_contains_start(self):
        period = FunctionalPeriod(date(2024, 1, 1), date(2024, 1, 31))

        self.assertTrue(period.contains(date(2024, 1, 1)))

    def test_contains_end(self):
        period = FunctionalPeriod(date(2024, 1, 1), date(2024, 1, 31))

        self.assertTrue(period.contains(date(2024, 1, 31)))

    def test_does_not_contain_date_outside_period(self):
        period = FunctionalPeriod(date(2024, 1, 1), date(2024, 1, 31))

        self.assertFalse(period.contains(date(2023, 12, 31)))
        self.assertFalse(period.contains(date(2024, 2, 1)))

    def test_open_period_contains_any_date_from_start(self):
        period = FunctionalPeriod(date(2024, 1, 1))

        self.assertTrue(period.contains(date(2024, 1, 1)))
        self.assertTrue(period.contains(date(2030, 1, 1)))
        self.assertFalse(period.contains(date(2023, 12, 31)))

    def test_single_day_duration_is_one(self):
        target = date(2024, 1, 1)

        self.assertEqual(
            FunctionalPeriod(target, target).duration_days,
            1,
        )

    def test_duration_uses_inclusive_day_count(self):
        period = FunctionalPeriod(date(2024, 3, 1), date(2024, 3, 3))

        self.assertEqual(period.duration_days, 3)

    def test_open_period_has_no_duration(self):
        self.assertIsNone(
            FunctionalPeriod(date(2024, 1, 1)).duration_days
        )

    def test_closed_periods_overlap(self):
        first = FunctionalPeriod(date(2024, 1, 1), date(2024, 1, 10))
        second = FunctionalPeriod(date(2024, 1, 5), date(2024, 1, 20))

        self.assertTrue(first.overlaps(second))
        self.assertTrue(second.overlaps(first))

    def test_closed_periods_do_not_overlap(self):
        first = FunctionalPeriod(date(2024, 1, 1), date(2024, 1, 9))
        second = FunctionalPeriod(date(2024, 1, 10), date(2024, 1, 20))

        self.assertFalse(first.overlaps(second))
        self.assertFalse(second.overlaps(first))

    def test_periods_overlap_at_shared_boundary(self):
        first = FunctionalPeriod(date(2024, 1, 1), date(2024, 1, 10))
        second = FunctionalPeriod(date(2024, 1, 10), date(2024, 1, 20))

        self.assertTrue(first.overlaps(second))
        self.assertTrue(second.overlaps(first))

    def test_open_period_overlaps_later_closed_period(self):
        open_period = FunctionalPeriod(date(2024, 1, 1))
        closed_period = FunctionalPeriod(
            date(2030, 1, 1),
            date(2030, 1, 31),
        )

        self.assertTrue(open_period.overlaps(closed_period))
        self.assertTrue(closed_period.overlaps(open_period))

    def test_open_period_does_not_overlap_earlier_closed_period(self):
        open_period = FunctionalPeriod(date(2024, 1, 10))
        closed_period = FunctionalPeriod(
            date(2024, 1, 1),
            date(2024, 1, 9),
        )

        self.assertFalse(open_period.overlaps(closed_period))
        self.assertFalse(closed_period.overlaps(open_period))

    def test_two_open_periods_overlap(self):
        first = FunctionalPeriod(date(2024, 1, 1))
        second = FunctionalPeriod(date(2030, 1, 1))

        self.assertTrue(first.overlaps(second))
        self.assertTrue(second.overlaps(first))

    def test_period_overlap_rejects_invalid_type(self):
        with self.assertRaises(TypeError):
            FunctionalPeriod(date(2024, 1, 1)).overlaps(object())

    def test_closed_period_ends_before_later_date(self):
        period = FunctionalPeriod(date(2024, 1, 1), date(2024, 1, 10))

        self.assertTrue(period.ends_before(date(2024, 1, 11)))

    def test_closed_period_does_not_end_before_equal_date(self):
        period = FunctionalPeriod(date(2024, 1, 1), date(2024, 1, 10))

        self.assertFalse(period.ends_before(date(2024, 1, 10)))

    def test_closed_period_does_not_end_before_earlier_date(self):
        period = FunctionalPeriod(date(2024, 1, 1), date(2024, 1, 10))

        self.assertFalse(period.ends_before(date(2024, 1, 9)))

    def test_open_period_never_ends_before_date(self):
        period = FunctionalPeriod(date(2024, 1, 1))

        self.assertFalse(period.ends_before(date(2030, 1, 1)))

    def test_ends_before_rejects_invalid_type(self):
        with self.assertRaises(TypeError):
            FunctionalPeriod(date(2024, 1, 1)).ends_before(
                "2024-01-02"
            )

    def test_ends_before_rejects_datetime(self):
        with self.assertRaises(TypeError):
            FunctionalPeriod(date(2024, 1, 1)).ends_before(
                datetime(2024, 1, 2)
            )


class FunctionalExerciseTests(unittest.TestCase):
    def test_creates_valid_active_exercise(self):
        item = exercise()

        self.assertEqual(item.status, FunctionalExerciseStatus.ACTIVE)
        self.assertTrue(item.period.is_open)

    def test_creates_valid_ended_exercise(self):
        item = exercise(
            period=FunctionalPeriod(
                date(2024, 1, 1),
                date(2024, 12, 31),
            ),
            status=FunctionalExerciseStatus.ENDED,
        )

        self.assertEqual(item.status, FunctionalExerciseStatus.ENDED)
        self.assertTrue(item.period.is_closed)

    def test_normalizes_person_id(self):
        self.assertEqual(
            exercise(person_id="  person-1  ").person_id,
            "person-1",
        )

    def test_rejects_empty_person_id(self):
        with self.assertRaises(ValueError):
            exercise(person_id=" ")

    def test_rejects_incorrect_attribute_types(self):
        valid = exercise()
        values = {
            "id": valid.id,
            "person_id": valid.person_id,
            "exercise_type": valid.exercise_type,
            "role": valid.role,
            "context": valid.context,
            "period": valid.period,
            "status": valid.status,
        }
        for field in values:
            with self.subTest(field=field):
                invalid = {**values, field: object()}
                with self.assertRaises(TypeError):
                    FunctionalExercise(**invalid)

    def test_rejects_active_with_closed_period(self):
        with self.assertRaises(ValueError):
            exercise(
                period=FunctionalPeriod(
                    date(2024, 1, 1),
                    date(2024, 12, 31),
                ),
            )

    def test_rejects_ended_with_open_period(self):
        with self.assertRaises(ValueError):
            exercise(status=FunctionalExerciseStatus.ENDED)

    def test_is_immutable(self):
        item = exercise()

        with self.assertRaises(FrozenInstanceError):
            item.person_id = "person-2"

    def test_equality_is_by_value(self):
        self.assertEqual(exercise(), exercise())

    def test_active_and_ended_properties(self):
        active = exercise()
        ended = exercise(
            period=FunctionalPeriod(
                date(2024, 1, 1),
                date(2024, 12, 31),
            ),
            status=FunctionalExerciseStatus.ENDED,
        )

        self.assertTrue(active.is_active)
        self.assertFalse(active.is_ended)
        self.assertFalse(ended.is_active)
        self.assertTrue(ended.is_ended)

    def test_was_active_on_closed_period_dates(self):
        item = exercise(
            period=FunctionalPeriod(
                date(2024, 1, 10),
                date(2024, 1, 20),
            ),
            status=FunctionalExerciseStatus.ENDED,
        )

        self.assertTrue(item.was_active_on(date(2024, 1, 10)))
        self.assertTrue(item.was_active_on(date(2024, 1, 15)))
        self.assertTrue(item.was_active_on(date(2024, 1, 20)))
        self.assertFalse(item.was_active_on(date(2024, 1, 9)))
        self.assertFalse(item.was_active_on(date(2024, 1, 21)))

    def test_active_exercise_was_active_on_later_date(self):
        item = exercise(
            period=FunctionalPeriod(date(2024, 1, 10)),
        )

        self.assertTrue(item.was_active_on(date(2030, 1, 1)))

    def test_was_active_on_rejects_invalid_type_and_datetime(self):
        item = exercise()

        with self.assertRaises(TypeError):
            item.was_active_on("2024-01-01")
        with self.assertRaises(TypeError):
            item.was_active_on(datetime(2024, 1, 1))

    def test_exercises_with_overlapping_periods_overlap(self):
        first = exercise(
            period=FunctionalPeriod(date(2024, 1, 1)),
        )
        second = exercise(
            period=FunctionalPeriod(
                date(2024, 2, 1),
                date(2024, 2, 28),
            ),
            status=FunctionalExerciseStatus.ENDED,
        )

        self.assertTrue(first.overlaps(second))

    def test_exercises_without_overlapping_periods_do_not_overlap(self):
        first = exercise(
            period=FunctionalPeriod(
                date(2024, 1, 1),
                date(2024, 1, 31),
            ),
            status=FunctionalExerciseStatus.ENDED,
        )
        second = exercise(
            period=FunctionalPeriod(date(2024, 2, 1)),
        )

        self.assertFalse(first.overlaps(second))

    def test_different_people_can_have_overlapping_exercises(self):
        first = exercise(person_id="person-1")
        second = exercise(person_id="person-2")

        self.assertTrue(first.overlaps(second))

    def test_different_types_can_have_overlapping_exercises(self):
        first = exercise()
        second = FunctionalExercise(
            id=FunctionalExerciseId(
                "87654321-4321-8765-4321-876543218765"
            ),
            person_id="person-1",
            exercise_type=FunctionalExerciseType(
                "representacao",
                "Representação",
            ),
            role=FunctionalRole("Representante"),
            context=FunctionalContext("Instituição"),
            period=FunctionalPeriod(date(2024, 1, 1)),
            status=FunctionalExerciseStatus.ACTIVE,
        )

        self.assertTrue(first.overlaps(second))

    def test_exercise_overlap_rejects_invalid_type(self):
        with self.assertRaises(TypeError):
            exercise().overlaps(object())

    def test_end_closes_active_exercise(self):
        original = exercise()

        ended = original.end(date(2024, 12, 31))

        self.assertIsNot(ended, original)
        self.assertTrue(original.is_active)
        self.assertTrue(original.period.is_open)
        self.assertTrue(ended.is_ended)
        self.assertTrue(ended.period.is_closed)
        self.assertEqual(ended.period.start_date, date(2024, 1, 1))
        self.assertEqual(ended.period.end_date, date(2024, 12, 31))

    def test_end_preserves_identity_and_other_attributes(self):
        original = exercise()

        ended = original.end(date(2024, 12, 31))

        self.assertIs(ended.id, original.id)
        self.assertEqual(ended.person_id, original.person_id)
        self.assertIs(ended.exercise_type, original.exercise_type)
        self.assertIs(ended.role, original.role)
        self.assertIs(ended.context, original.context)

    def test_end_accepts_start_date(self):
        original = exercise()

        ended = original.end(date(2024, 1, 1))

        self.assertEqual(ended.period.duration_days, 1)
        self.assertTrue(ended.is_ended)

    def test_end_rejects_date_before_start(self):
        with self.assertRaises(ValueError):
            exercise().end(date(2023, 12, 31))

    def test_end_rejects_invalid_type(self):
        with self.assertRaises(TypeError):
            exercise().end("2024-12-31")

    def test_end_rejects_datetime(self):
        with self.assertRaises(TypeError):
            exercise().end(datetime(2024, 12, 31))

    def test_end_rejects_already_ended_exercise(self):
        ended = exercise(
            period=FunctionalPeriod(
                date(2024, 1, 1),
                date(2024, 12, 31),
            ),
            status=FunctionalExerciseStatus.ENDED,
        )

        with self.assertRaises(ValueError):
            ended.end(date(2025, 1, 1))


class RscModelExportsTests(unittest.TestCase):
    def test_exports_all_functional_domain_concepts(self):
        self.assertTrue(FunctionalExercise)
        self.assertTrue(FunctionalExerciseId)
        self.assertTrue(FunctionalExerciseType)
        self.assertTrue(FunctionalRole)
        self.assertTrue(FunctionalContext)
        self.assertTrue(FunctionalExerciseStatus)
        self.assertTrue(FunctionalPeriod)

    def test_preserves_existing_exports(self):
        self.assertTrue(Activity)
        self.assertTrue(Project)


if __name__ == "__main__":
    unittest.main()
