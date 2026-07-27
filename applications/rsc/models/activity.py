"""Atividade profissional acompanhada durante a investigação documental."""

from dataclasses import dataclass, replace
from enum import Enum
from typing import ClassVar

from .functional_assignment_evidence import FunctionalAssignmentEvidenceId
from .functional_exercise import FunctionalExerciseId


class ActivityState(str, Enum):
    """Grau de consolidação documental de uma atividade profissional."""

    REMEMBERED = "lembrada"
    UNDER_INVESTIGATION = "em_investigacao"
    PARTIALLY_PROVEN = "parcialmente_comprovada"
    PROVEN = "comprovada"


@dataclass(frozen=True, slots=True)
class Activity:
    """Hipótese de trabalho que evolui até uma atividade comprovada."""

    INITIAL_STATE: ClassVar[ActivityState] = ActivityState.REMEMBERED

    activity_id: str
    description: str
    state: ActivityState = INITIAL_STATE
    functional_assignment_evidence_ids: tuple[
        FunctionalAssignmentEvidenceId, ...
    ] = ()
    functional_exercise_ids: tuple[FunctionalExerciseId, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "activity_id",
            self._required_text(self.activity_id, "activity_id"),
        )
        object.__setattr__(
            self,
            "description",
            self._required_text(self.description, "description"),
        )
        self._require_instance(self.state, ActivityState, "state")
        self._validate_unique_ids(
            self.functional_assignment_evidence_ids,
            FunctionalAssignmentEvidenceId,
            "functional_assignment_evidence_ids",
        )
        self._validate_unique_ids(
            self.functional_exercise_ids,
            FunctionalExerciseId,
            "functional_exercise_ids",
        )
        if (
            self.state is ActivityState.PARTIALLY_PROVEN
            and not self.functional_assignment_evidence_ids
        ):
            raise ValueError(
                "atividade parcialmente comprovada exige evidência "
                "funcional relacionada."
            )
        if self.state is ActivityState.PROVEN and (
            not self.functional_assignment_evidence_ids
            or not self.functional_exercise_ids
        ):
            raise ValueError(
                "atividade comprovada exige evidência e exercício "
                "funcional relacionados."
            )

    def start_investigation(self) -> "Activity":
        """Inicia a busca e a análise de sustentação documental."""

        return self._transition(
            ActivityState.REMEMBERED,
            ActivityState.UNDER_INVESTIGATION,
        )

    def relate_assignment_evidence(
        self,
        evidence_id: FunctionalAssignmentEvidenceId,
    ) -> "Activity":
        """Relaciona uma afirmação documental sem alterar seu ciclo próprio."""

        self._require_instance(
            evidence_id,
            FunctionalAssignmentEvidenceId,
            "evidence_id",
        )
        if evidence_id in self.functional_assignment_evidence_ids:
            return self
        return replace(
            self,
            functional_assignment_evidence_ids=(
                *self.functional_assignment_evidence_ids,
                evidence_id,
            ),
        )

    def relate_functional_exercise(
        self,
        exercise_id: FunctionalExerciseId,
    ) -> "Activity":
        """Relaciona um fato funcional reconstruído à atividade."""

        self._require_instance(
            exercise_id,
            FunctionalExerciseId,
            "exercise_id",
        )
        if exercise_id in self.functional_exercise_ids:
            return self
        return replace(
            self,
            functional_exercise_ids=(
                *self.functional_exercise_ids,
                exercise_id,
            ),
        )

    def mark_partially_proven(self) -> "Activity":
        """Registra sustentação documental ainda não consolidada por completo."""

        if not self.functional_assignment_evidence_ids:
            raise ValueError(
                "comprovação parcial exige evidência funcional relacionada."
            )
        return self._transition(
            ActivityState.UNDER_INVESTIGATION,
            ActivityState.PARTIALLY_PROVEN,
        )

    def mark_proven(self) -> "Activity":
        """Registra que evidências já sustentam exercício reconstruído."""

        if not self.functional_exercise_ids:
            raise ValueError(
                "comprovação exige exercício funcional relacionado."
            )
        return self._transition(
            ActivityState.PARTIALLY_PROVEN,
            ActivityState.PROVEN,
        )

    def _transition(
        self,
        expected: ActivityState,
        target: ActivityState,
    ) -> "Activity":
        if self.state is not expected:
            raise ValueError(
                f"transição para {target.value} exige estado "
                f"{expected.value}."
            )
        return replace(self, state=target)

    @staticmethod
    def _required_text(value: object, field: str) -> str:
        if not isinstance(value, str):
            raise TypeError(f"{field} deve ser uma string.")
        normalized = " ".join(value.split())
        if not normalized:
            raise ValueError(f"{field} não pode ser vazio.")
        return normalized

    @classmethod
    def _validate_unique_ids(
        cls,
        values: object,
        expected_type: type,
        field: str,
    ) -> None:
        if not isinstance(values, tuple):
            raise TypeError(f"{field} deve ser uma tupla.")
        for value in values:
            cls._require_instance(value, expected_type, field)
        if len(set(values)) != len(values):
            raise ValueError(f"{field} não pode conter duplicidades.")

    @staticmethod
    def _require_instance(
        value: object,
        expected_type: type,
        field: str,
    ) -> None:
        if not isinstance(value, expected_type):
            raise TypeError(f"{field} deve ser {expected_type.__name__}.")
