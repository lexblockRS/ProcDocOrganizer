"""Porta de persistência de exercícios funcionais."""

from typing import Protocol

from applications.rsc.models import (
    FunctionalExercise,
    FunctionalExerciseId,
)


class FunctionalExerciseRepository(Protocol):
    """Persistência de exercícios, em ordem de inserção."""

    def save(self, exercise: FunctionalExercise) -> None:
        """Insere ou substitui pelo ID, preservando a posição original."""
        ...

    def get_by_id(
        self,
        exercise_id: FunctionalExerciseId,
    ) -> FunctionalExercise | None: ...

    def list_all(self) -> tuple[FunctionalExercise, ...]:
        """Retorna todos os exercícios em ordem de inserção."""
        ...

    def update(self, exercise: FunctionalExercise) -> FunctionalExercise: ...

    def delete(
        self,
        exercise_id: FunctionalExerciseId,
    ) -> FunctionalExercise | None: ...
