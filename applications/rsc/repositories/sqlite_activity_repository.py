"""Adapter SQLite de atividades e suas relações funcionais."""

from collections import defaultdict
from pathlib import Path
import sqlite3

from database import ProjectDatabase

from applications.rsc.models import (
    Activity,
    ActivityState,
    FunctionalAssignmentEvidenceId,
    FunctionalExerciseId,
)
from applications.rsc.ports import (
    ActivityPersistenceError,
    ActivityRelationNotFoundError,
)


class SQLiteActivityRepository:
    """Persiste versões imutáveis de Activity no banco do projeto."""

    TABLE = "rsc_activities"
    EVIDENCE_TABLE = "rsc_activity_functional_assignment_evidences"
    EXERCISE_TABLE = "rsc_activity_functional_exercises"
    COLUMNS = ("activity_id", "description", "state")

    def __init__(self, database_path: str | Path) -> None:
        self.database_path = Path(database_path)

    def add(self, activity: Activity) -> None:
        self._store(activity, allow_update=False)

    def save(self, activity: Activity) -> None:
        self._store(activity, allow_update=True)

    def get(self, activity_id: str) -> Activity | None:
        if not isinstance(activity_id, str):
            raise TypeError("activity_id deve ser uma string.")
        normalized_id = activity_id.strip()
        if not normalized_id:
            raise ValueError("activity_id não pode ser vazio.")
        try:
            with ProjectDatabase(self.database_path) as database:
                row = database.connection.execute(
                    f"SELECT {', '.join(self.COLUMNS)} "
                    f"FROM {self.TABLE} WHERE activity_id = ?",
                    (normalized_id,),
                ).fetchone()
                if row is None:
                    return None
                evidence_ids, exercise_ids = self._fetch_relations(
                    database.connection,
                    (normalized_id,),
                )
            return self._from_row(
                row,
                evidence_ids[normalized_id],
                exercise_ids[normalized_id],
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise ActivityPersistenceError(
                "A atividade persistida contém relações inválidas."
            ) from exc
        except sqlite3.Error as exc:
            raise ActivityPersistenceError(
                "Falha ao recuperar atividade."
            ) from exc

    def list_all(self) -> tuple[Activity, ...]:
        try:
            with ProjectDatabase(self.database_path) as database:
                rows = database.connection.execute(
                    f"SELECT {', '.join(self.COLUMNS)} "
                    f"FROM {self.TABLE} ORDER BY insertion_order"
                ).fetchall()
                activity_ids = tuple(row["activity_id"] for row in rows)
                evidence_ids, exercise_ids = self._fetch_relations(
                    database.connection,
                    activity_ids,
                )
            return tuple(
                self._from_row(
                    row,
                    evidence_ids[row["activity_id"]],
                    exercise_ids[row["activity_id"]],
                )
                for row in rows
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise ActivityPersistenceError(
                "Uma atividade persistida contém relações inválidas."
            ) from exc
        except sqlite3.Error as exc:
            raise ActivityPersistenceError(
                "Falha ao listar atividades."
            ) from exc

    def _store(self, activity: Activity, *, allow_update: bool) -> None:
        if not isinstance(activity, Activity):
            raise TypeError("activity deve ser Activity.")
        try:
            with ProjectDatabase(self.database_path) as database:
                with database.transaction() as connection:
                    self._require_relations(connection, activity)
                    existing = connection.execute(
                        f"SELECT 1 FROM {self.TABLE} WHERE activity_id = ?",
                        (activity.activity_id,),
                    ).fetchone()
                    if existing is None:
                        self._insert(connection, activity)
                    elif allow_update:
                        connection.execute(
                            f"UPDATE {self.TABLE} "
                            "SET description = ?, state = ? "
                            "WHERE activity_id = ?",
                            (
                                activity.description,
                                activity.state.value,
                                activity.activity_id,
                            ),
                        )
                    else:
                        raise ActivityPersistenceError(
                            "A atividade já existe."
                        )
                    self._replace_relations(connection, activity)
        except ActivityRelationNotFoundError:
            raise
        except ActivityPersistenceError:
            raise
        except sqlite3.Error as exc:
            raise ActivityPersistenceError(
                "Falha ao salvar atividade."
            ) from exc

    def _insert(self, connection, activity: Activity) -> None:
        next_order = (
            f"(SELECT COALESCE(MAX(insertion_order), 0) + 1 "
            f"FROM {self.TABLE})"
        )
        connection.execute(
            f"INSERT INTO {self.TABLE} "
            "(insertion_order, activity_id, description, state) "
            f"VALUES ({next_order}, ?, ?, ?)",
            (
                activity.activity_id,
                activity.description,
                activity.state.value,
            ),
        )

    @classmethod
    def _require_relations(cls, connection, activity: Activity) -> None:
        for evidence_id in activity.functional_assignment_evidence_ids:
            if connection.execute(
                "SELECT 1 FROM rsc_functional_assignment_evidences "
                "WHERE id = ?",
                (str(evidence_id),),
            ).fetchone() is None:
                raise ActivityRelationNotFoundError(
                    "Evidência funcional não encontrada: "
                    f"{evidence_id}."
                )
        for exercise_id in activity.functional_exercise_ids:
            if connection.execute(
                "SELECT 1 FROM rsc_functional_exercises WHERE id = ?",
                (str(exercise_id),),
            ).fetchone() is None:
                raise ActivityRelationNotFoundError(
                    f"Exercício funcional não encontrado: {exercise_id}."
                )

    @classmethod
    def _replace_relations(cls, connection, activity: Activity) -> None:
        connection.execute(
            f"DELETE FROM {cls.EVIDENCE_TABLE} WHERE activity_id = ?",
            (activity.activity_id,),
        )
        connection.executemany(
            f"INSERT INTO {cls.EVIDENCE_TABLE} "
            "(activity_id, evidence_id, ordinal) VALUES (?, ?, ?)",
            tuple(
                (activity.activity_id, str(item), ordinal)
                for ordinal, item in enumerate(
                    activity.functional_assignment_evidence_ids
                )
            ),
        )
        connection.execute(
            f"DELETE FROM {cls.EXERCISE_TABLE} WHERE activity_id = ?",
            (activity.activity_id,),
        )
        connection.executemany(
            f"INSERT INTO {cls.EXERCISE_TABLE} "
            "(activity_id, exercise_id, ordinal) VALUES (?, ?, ?)",
            tuple(
                (activity.activity_id, str(item), ordinal)
                for ordinal, item in enumerate(
                    activity.functional_exercise_ids
                )
            ),
        )

    @classmethod
    def _fetch_relations(cls, connection, activity_ids):
        evidences = defaultdict(list)
        exercises = defaultdict(list)
        if activity_ids:
            placeholders = ", ".join("?" for _ in activity_ids)
            for row in connection.execute(
                f"SELECT activity_id, evidence_id FROM {cls.EVIDENCE_TABLE} "
                f"WHERE activity_id IN ({placeholders}) "
                "ORDER BY activity_id, ordinal",
                activity_ids,
            ).fetchall():
                evidences[row["activity_id"]].append(
                    FunctionalAssignmentEvidenceId(row["evidence_id"])
                )
            for row in connection.execute(
                f"SELECT activity_id, exercise_id FROM {cls.EXERCISE_TABLE} "
                f"WHERE activity_id IN ({placeholders}) "
                "ORDER BY activity_id, ordinal",
                activity_ids,
            ).fetchall():
                exercises[row["activity_id"]].append(
                    FunctionalExerciseId(row["exercise_id"])
                )
        return (
            {item: tuple(evidences[item]) for item in activity_ids},
            {item: tuple(exercises[item]) for item in activity_ids},
        )

    @staticmethod
    def _from_row(row, evidence_ids, exercise_ids) -> Activity:
        try:
            return Activity(
                activity_id=row["activity_id"],
                description=row["description"],
                state=ActivityState(row["state"]),
                functional_assignment_evidence_ids=evidence_ids,
                functional_exercise_ids=exercise_ids,
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise ActivityPersistenceError(
                "A atividade persistida contém dados inválidos."
            ) from exc
