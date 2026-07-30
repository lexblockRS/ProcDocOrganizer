"""Adapter SQLite de atribuições funcionais documentais."""

from datetime import date
from pathlib import Path
import sqlite3

from database import ProjectDatabase

from applications.rsc.models import (
    FunctionalAssignmentEvidence,
    FunctionalAssignmentEvidenceId,
    FunctionalAssignmentEvidenceStatus,
    SourceEvidenceReference,
)
from applications.rsc.ports import (
    DuplicateFunctionalAssignmentEvidenceError,
    FunctionalAssignmentEvidencePersistenceError,
)


class SQLiteFunctionalAssignmentEvidenceRepository:
    """Persiste atribuições funcionais no banco de um projeto."""

    TABLE = "rsc_functional_assignment_evidences"
    COLUMNS = (
        "id",
        "person_id",
        "source_evidence_reference",
        "exercise_type_code",
        "exercise_type_label",
        "role",
        "organization",
        "start_date",
        "end_date",
        "unit",
        "administrative_reference",
        "status",
    )

    def __init__(self, database_path: str | Path) -> None:
        self.database_path = Path(database_path)

    def save(
        self,
        evidence: FunctionalAssignmentEvidence,
    ) -> FunctionalAssignmentEvidence:
        if not isinstance(evidence, FunctionalAssignmentEvidence):
            raise TypeError(
                "evidence deve ser FunctionalAssignmentEvidence."
            )
        columns = ("insertion_order",) + self.COLUMNS
        evidence_placeholders = ", ".join("?" for _ in self.COLUMNS)
        next_order = (
            f"(SELECT COALESCE(MAX(insertion_order), 0) + 1 "
            f"FROM {self.TABLE})"
        )
        values = self._to_row(evidence)
        try:
            with ProjectDatabase(self.database_path) as database:
                with database.transaction() as connection:
                    connection.execute(
                        f"INSERT INTO {self.TABLE} "
                        f"({', '.join(columns)}) "
                        f"VALUES ({next_order}, {evidence_placeholders})",
                        values,
                    )
            return evidence
        except sqlite3.IntegrityError as exc:
            if f"{self.TABLE}.id" in str(exc):
                raise DuplicateFunctionalAssignmentEvidenceError(
                    "A atribuição funcional já existe."
                ) from exc
            raise FunctionalAssignmentEvidencePersistenceError(
                "Falha de integridade ao inserir atribuição funcional."
            ) from exc
        except sqlite3.Error as exc:
            raise FunctionalAssignmentEvidencePersistenceError(
                "Falha ao inserir atribuição funcional."
            ) from exc

    def get_by_id(
        self,
        evidence_id: FunctionalAssignmentEvidenceId,
    ) -> FunctionalAssignmentEvidence | None:
        if not isinstance(
            evidence_id,
            FunctionalAssignmentEvidenceId,
        ):
            raise TypeError(
                "evidence_id deve ser FunctionalAssignmentEvidenceId."
            )
        try:
            with ProjectDatabase(self.database_path) as database:
                row = database.connection.execute(
                    f"SELECT {', '.join(self.COLUMNS)} "
                    f"FROM {self.TABLE} WHERE id = ?",
                    (str(evidence_id),),
                ).fetchone()
            return self._from_row(row) if row is not None else None
        except sqlite3.Error as exc:
            raise FunctionalAssignmentEvidencePersistenceError(
                "Falha ao recuperar atribuição funcional."
            ) from exc

    def list_all(
        self,
    ) -> tuple[FunctionalAssignmentEvidence, ...]:
        try:
            with ProjectDatabase(self.database_path) as database:
                rows = database.connection.execute(
                    f"SELECT {', '.join(self.COLUMNS)} "
                    f"FROM {self.TABLE} ORDER BY insertion_order"
                ).fetchall()
            return tuple(self._from_row(row) for row in rows)
        except sqlite3.Error as exc:
            raise FunctionalAssignmentEvidencePersistenceError(
                "Falha ao listar atribuições funcionais."
            ) from exc

    def update(
        self,
        evidence: FunctionalAssignmentEvidence,
    ) -> FunctionalAssignmentEvidence:
        if not isinstance(evidence, FunctionalAssignmentEvidence):
            raise TypeError(
                "evidence deve ser FunctionalAssignmentEvidence."
            )
        assignments = ", ".join(
            f"{column} = ?" for column in self.COLUMNS[1:]
        )
        values = self._to_row(evidence)[1:] + (str(evidence.id),)
        try:
            with ProjectDatabase(self.database_path) as database:
                with database.transaction() as connection:
                    result = connection.execute(
                        f"UPDATE {self.TABLE} SET {assignments} "
                        "WHERE id = ?",
                        values,
                    )
                    if result.rowcount != 1:
                        raise FunctionalAssignmentEvidencePersistenceError(
                            "A atribuição funcional não existe."
                        )
            return evidence
        except sqlite3.Error as exc:
            raise FunctionalAssignmentEvidencePersistenceError(
                "Falha ao atualizar atribuição funcional."
            ) from exc

    def delete(
        self,
        evidence_id: FunctionalAssignmentEvidenceId,
    ) -> FunctionalAssignmentEvidence | None:
        current = self.get_by_id(evidence_id)
        if current is None:
            return None
        try:
            with ProjectDatabase(self.database_path) as database:
                with database.transaction() as connection:
                    connection.execute(
                        f"DELETE FROM {self.TABLE} WHERE id = ?",
                        (str(evidence_id),),
                    )
            return current
        except sqlite3.Error as exc:
            raise FunctionalAssignmentEvidencePersistenceError(
                "Falha ao remover atribuição funcional."
            ) from exc

    @classmethod
    def _to_row(
        cls,
        evidence: FunctionalAssignmentEvidence,
    ) -> tuple[object, ...]:
        return (
            str(evidence.id),
            evidence.person_id,
            str(evidence.source_evidence_reference),
            evidence.exercise_type_code,
            evidence.exercise_type_label,
            evidence.role,
            evidence.organization,
            cls._serialize_date(evidence.start_date),
            cls._serialize_date(evidence.end_date),
            evidence.unit,
            evidence.administrative_reference,
            evidence.status.value,
        )

    @classmethod
    def _from_row(cls, row) -> FunctionalAssignmentEvidence:
        try:
            return FunctionalAssignmentEvidence(
                id=FunctionalAssignmentEvidenceId(row["id"]),
                person_id=row["person_id"],
                source_evidence_reference=SourceEvidenceReference(
                    row["source_evidence_reference"]
                ),
                exercise_type_code=row["exercise_type_code"],
                exercise_type_label=row["exercise_type_label"],
                role=row["role"],
                organization=row["organization"],
                start_date=cls._deserialize_date(row["start_date"]),
                end_date=cls._deserialize_date(row["end_date"]),
                unit=row["unit"],
                administrative_reference=(
                    row["administrative_reference"]
                ),
                status=FunctionalAssignmentEvidenceStatus(row["status"]),
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise FunctionalAssignmentEvidencePersistenceError(
                "A atribuição funcional persistida contém dados inválidos."
            ) from exc

    @staticmethod
    def _serialize_date(value: date | None) -> str | None:
        return value.isoformat() if value is not None else None

    @staticmethod
    def _deserialize_date(value: str | None) -> date | None:
        return date.fromisoformat(value) if value is not None else None
