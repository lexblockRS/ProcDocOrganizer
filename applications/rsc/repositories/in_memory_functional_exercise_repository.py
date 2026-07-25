"""Repositório de exercícios funcionais mantido em memória."""

from applications.rsc.models import (
    FunctionalExercise,
    FunctionalExerciseId,
)


class InMemoryFunctionalExerciseRepository:
    """Mantém exercícios funcionais na ordem de inserção."""

    def __init__(self) -> None:
        self._exercises: dict[
            FunctionalExerciseId,
            FunctionalExercise,
        ] = {}

    def save(self, exercise: FunctionalExercise) -> None:
        self._exercises[exercise.id] = exercise

    def get_by_id(
        self,
        exercise_id: FunctionalExerciseId,
    ) -> FunctionalExercise | None:
        return self._exercises.get(exercise_id)

    def list_all(self) -> tuple[FunctionalExercise, ...]:
        return tuple(self._exercises.values())
