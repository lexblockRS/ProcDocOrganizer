"""Porta de persistência de exercícios funcionais."""

from typing import Protocol

from applications.rsc.models import (
    FunctionalExercise,
    FunctionalExerciseId,
)


class FunctionalExerciseRepository(Protocol):
    """Operações necessárias ao caso de uso atual de exercício funcional."""

    def save(self, exercise: FunctionalExercise) -> None: ...

    def get_by_id(
        self,
        exercise_id: FunctionalExerciseId,
    ) -> FunctionalExercise | None: ...

    def list_all(self) -> tuple[FunctionalExercise, ...]: ...
