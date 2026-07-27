"""Adapter SQLite de exercícios funcionais e sua proveniência."""

from collections import defaultdict
from datetime import date
from pathlib import Path
import sqlite3

from database import ProjectDatabase

from applications.rsc.models import (
    FunctionalAssignmentEvidenceId,
    FunctionalContext,
    FunctionalExercise,
    FunctionalExerciseId,
    FunctionalExerciseStatus,
    FunctionalExerciseType,
    FunctionalPeriod,
    FunctionalRole,
)
from applications.rsc.ports import (
    FunctionalExerciseAssignmentEvidenceNotFoundError,
    FunctionalExercisePersistenceError,
)


class SQLiteFunctionalExerciseRepository:
    """Persiste exercícios e proveniência ordenada no banco do projeto."""

    TABLE = "rsc_functional_exercises"
    PROVENANCE_TABLE = (
        "rsc_functional_exercise_assignment_evidences"
    )
    COLUMNS = (
        "id",
        "person_id",
        "exercise_type_code",
        "exercise_type_label",
        "role",
        "context_organization",
        "context_unit",
        "context_reference",
        "start_date",
        "end_date",
        "status",
    )

    def __init__(self, database_path: str | Path) -> None:
        self.database_path = Path(database_path)

    def save(self, exercise: FunctionalExercise) -> None:
        if not isinstance(exercise, FunctionalExercise):
            raise TypeError("exercise deve ser FunctionalExercise.")
        if not exercise.functional_assignment_evidence_ids:
            raise FunctionalExercisePersistenceError(
                "Exercício funcional exige ao menos uma evidência."
            )
        try:
            with ProjectDatabase(self.database_path) as database:
                with database.transaction() as connection:
                    self._require_assignment_evidences(
                        connection,
                        exercise.functional_assignment_evidence_ids,
                    )
                    existing = connection.execute(
                        f"SELECT insertion_order FROM {self.TABLE} "
                        "WHERE id = ?",
                        (str(exercise.id),),
                    ).fetchone()
                    if existing is None:
                        self._insert(connection, exercise)
                    else:
                        self._update(connection, exercise)
                    self._replace_provenance(connection, exercise)
        except sqlite3.Error as exc:
            raise FunctionalExercisePersistenceError(
                "Falha ao salvar exercício funcional."
            ) from exc

    def get_by_id(
        self,
        exercise_id: FunctionalExerciseId,
    ) -> FunctionalExercise | None:
        if not isinstance(exercise_id, FunctionalExerciseId):
            raise TypeError("exercise_id deve ser FunctionalExerciseId.")
        try:
            with ProjectDatabase(self.database_path) as database:
                row = database.connection.execute(
                    f"SELECT {', '.join(self.COLUMNS)} "
                    f"FROM {self.TABLE} WHERE id = ?",
                    (str(exercise_id),),
                ).fetchone()
                if row is None:
                    return None
                provenance = self._fetch_provenance(
                    database.connection,
                    (str(exercise_id),),
                )
            return self._from_row(row, provenance[str(exercise_id)])
        except sqlite3.Error as exc:
            raise FunctionalExercisePersistenceError(
                "Falha ao recuperar exercício funcional."
            ) from exc

    def list_all(self) -> tuple[FunctionalExercise, ...]:
        try:
            with ProjectDatabase(self.database_path) as database:
                rows = database.connection.execute(
                    f"SELECT {', '.join(self.COLUMNS)} "
                    f"FROM {self.TABLE} ORDER BY insertion_order"
                ).fetchall()
                identifiers = tuple(row["id"] for row in rows)
                provenance = self._fetch_provenance(
                    database.connection,
                    identifiers,
                )
            return tuple(
                self._from_row(row, provenance[row["id"]])
                for row in rows
            )
        except sqlite3.Error as exc:
            raise FunctionalExercisePersistenceError(
                "Falha ao listar exercícios funcionais."
            ) from exc

    def _insert(self, connection, exercise: FunctionalExercise) -> None:
        placeholders = ", ".join("?" for _ in self.COLUMNS)
        next_order = (
            f"(SELECT COALESCE(MAX(insertion_order), 0) + 1 "
            f"FROM {self.TABLE})"
        )
        connection.execute(
            f"INSERT INTO {self.TABLE} "
            f"(insertion_order, {', '.join(self.COLUMNS)}) "
            f"VALUES ({next_order}, {placeholders})",
            self._to_row(exercise),
        )

    def _update(self, connection, exercise: FunctionalExercise) -> None:
        assignments = ", ".join(
            f"{column} = ?" for column in self.COLUMNS[1:]
        )
        values = self._to_row(exercise)
        connection.execute(
            f"UPDATE {self.TABLE} SET {assignments} WHERE id = ?",
            values[1:] + (values[0],),
        )

    def _replace_provenance(
        self,
        connection,
        exercise: FunctionalExercise,
    ) -> None:
        connection.execute(
            f"DELETE FROM {self.PROVENANCE_TABLE} "
            "WHERE exercise_id = ?",
            (str(exercise.id),),
        )
        connection.executemany(
            f"INSERT INTO {self.PROVENANCE_TABLE} "
            "(exercise_id, assignment_evidence_id, ordinal) "
            "VALUES (?, ?, ?)",
            tuple(
                (str(exercise.id), str(evidence_id), ordinal)
                for ordinal, evidence_id in enumerate(
                    exercise.functional_assignment_evidence_ids
                )
            ),
        )

    @staticmethod
    def _require_assignment_evidences(
        connection,
        evidence_ids: tuple[FunctionalAssignmentEvidenceId, ...],
    ) -> None:
        for evidence_id in evidence_ids:
            exists = connection.execute(
                "SELECT 1 FROM rsc_functional_assignment_evidences "
                "WHERE id = ?",
                (str(evidence_id),),
            ).fetchone()
            if exists is None:
                raise FunctionalExerciseAssignmentEvidenceNotFoundError(
                    "Evidência de atribuição funcional não encontrada: "
                    f"{evidence_id}."
                )

    @classmethod
    def _fetch_provenance(
        cls,
        connection,
        exercise_ids: tuple[str, ...],
    ) -> dict[str, tuple[FunctionalAssignmentEvidenceId, ...]]:
        grouped = defaultdict(list)
        if exercise_ids:
            placeholders = ", ".join("?" for _ in exercise_ids)
            rows = connection.execute(
                f"SELECT exercise_id, assignment_evidence_id "
                f"FROM {cls.PROVENANCE_TABLE} "
                f"WHERE exercise_id IN ({placeholders}) "
                "ORDER BY exercise_id, ordinal",
                exercise_ids,
            ).fetchall()
            try:
                for row in rows:
                    grouped[row["exercise_id"]].append(
                        FunctionalAssignmentEvidenceId(
                            row["assignment_evidence_id"]
                        )
                    )
            except (KeyError, TypeError, ValueError) as exc:
                raise FunctionalExercisePersistenceError(
                    "A proveniência persistida contém dados inválidos."
                ) from exc
        return {
            exercise_id: tuple(grouped[exercise_id])
            for exercise_id in exercise_ids
        }

    @classmethod
    def _to_row(cls, exercise: FunctionalExercise) -> tuple[object, ...]:
        return (
            str(exercise.id),
            exercise.person_id,
            exercise.exercise_type.code,
            exercise.exercise_type.label,
            exercise.role.name,
            exercise.context.organization,
            exercise.context.unit,
            exercise.context.reference,
            exercise.period.start_date.isoformat(),
            (
                exercise.period.end_date.isoformat()
                if exercise.period.end_date is not None
                else None
            ),
            exercise.status.value,
        )

    @classmethod
    def _from_row(
        cls,
        row,
        provenance: tuple[FunctionalAssignmentEvidenceId, ...],
    ) -> FunctionalExercise:
        try:
            if not provenance:
                raise ValueError("proveniência ausente")
            return FunctionalExercise(
                id=FunctionalExerciseId(row["id"]),
                person_id=row["person_id"],
                exercise_type=FunctionalExerciseType(
                    row["exercise_type_code"],
                    row["exercise_type_label"],
                ),
                role=FunctionalRole(row["role"]),
                context=FunctionalContext(
                    organization=row["context_organization"],
                    unit=row["context_unit"],
                    reference=row["context_reference"],
                ),
                period=FunctionalPeriod(
                    start_date=date.fromisoformat(row["start_date"]),
                    end_date=(
                        date.fromisoformat(row["end_date"])
                        if row["end_date"] is not None
                        else None
                    ),
                ),
                status=FunctionalExerciseStatus(row["status"]),
                functional_assignment_evidence_ids=provenance,
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise FunctionalExercisePersistenceError(
                "O exercício funcional persistido contém dados inválidos."
            ) from exc
