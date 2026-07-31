"""Persistência SQLite específica do Aggregate ExecutionFact."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
import json
from pathlib import Path
import sqlite3
from typing import TYPE_CHECKING

from .database import initialize_database

if TYPE_CHECKING:
    from platform_sdk.execution_fact import ExecutionFact


class ExecutionFactPersistenceError(RuntimeError):
    """Falha ao persistir ou reidratar um ExecutionFact."""


class ExecutionFactNotFoundError(ExecutionFactPersistenceError):
    """O ExecutionFact solicitado não existe."""


class SQLiteExecutionFactStore:
    """Store SQLite direto, sem ORM ou Repository genérico."""

    def __init__(self, database_path: str | Path) -> None:
        self.database_path = Path(database_path)
        initialize_database(self.database_path)
        self._connection = sqlite3.connect(self.database_path)
        self._connection.row_factory = sqlite3.Row
        self._connection.execute("PRAGMA foreign_keys = ON")

    def save(self, fact: ExecutionFact) -> None:
        ExecutionFact, _ExecutionFactState = _fact_types()
        if not isinstance(fact, ExecutionFact):
            raise TypeError("fact deve ser platform_sdk.ExecutionFact.")
        try:
            with self._connection:
                self._connection.execute(
                    """
                    INSERT INTO platform_execution_facts (
                        execution_fact_id, project_id, evidence_id,
                        fact_type, description, quantity, unit,
                        period_start, period_end, metadata_json,
                        created_at, updated_at, state
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(execution_fact_id) DO UPDATE SET
                        project_id = excluded.project_id,
                        evidence_id = excluded.evidence_id,
                        fact_type = excluded.fact_type,
                        description = excluded.description,
                        quantity = excluded.quantity,
                        unit = excluded.unit,
                        period_start = excluded.period_start,
                        period_end = excluded.period_end,
                        metadata_json = excluded.metadata_json,
                        created_at = excluded.created_at,
                        updated_at = excluded.updated_at,
                        state = excluded.state
                    """,
                    (
                        fact.execution_fact_id,
                        fact.project_id,
                        fact.evidence_id,
                        fact.fact_type,
                        fact.description,
                        (
                            None
                            if fact.quantity is None
                            else str(fact.quantity)
                        ),
                        fact.unit,
                        (
                            None
                            if fact.period_start is None
                            else fact.period_start.isoformat()
                        ),
                        (
                            None
                            if fact.period_end is None
                            else fact.period_end.isoformat()
                        ),
                        json.dumps(
                            list(fact.metadata),
                            ensure_ascii=False,
                            separators=(",", ":"),
                        ),
                        fact.created_at.isoformat(),
                        fact.updated_at.isoformat(),
                        fact.state.value,
                    ),
                )
        except sqlite3.IntegrityError as exc:
            raise ExecutionFactPersistenceError(
                "Project ou Evidence vinculada é inválida."
            ) from exc
        except sqlite3.Error as exc:
            raise ExecutionFactPersistenceError(
                "Não foi possível salvar o ExecutionFact."
            ) from exc

    def get(self, execution_fact_id: str) -> ExecutionFact:
        normalized = _required(execution_fact_id, "execution_fact_id")
        try:
            row = self._connection.execute(
                """
                SELECT *
                FROM platform_execution_facts
                WHERE execution_fact_id = ?
                """,
                (normalized,),
            ).fetchone()
        except sqlite3.Error as exc:
            raise ExecutionFactPersistenceError(
                "Não foi possível abrir o ExecutionFact."
            ) from exc
        if row is None:
            raise ExecutionFactNotFoundError(
                f"ExecutionFact não encontrado: {normalized}."
            )
        try:
            ExecutionFact, ExecutionFactState = _fact_types()
            metadata = json.loads(row["metadata_json"])
            return ExecutionFact(
                execution_fact_id=row["execution_fact_id"],
                project_id=row["project_id"],
                evidence_id=row["evidence_id"],
                fact_type=row["fact_type"],
                description=row["description"],
                quantity=(
                    None
                    if row["quantity"] is None
                    else Decimal(row["quantity"])
                ),
                unit=row["unit"],
                period_start=(
                    None
                    if row["period_start"] is None
                    else date.fromisoformat(row["period_start"])
                ),
                period_end=(
                    None
                    if row["period_end"] is None
                    else date.fromisoformat(row["period_end"])
                ),
                metadata=tuple((item[0], item[1]) for item in metadata),
                created_at=datetime.fromisoformat(row["created_at"]),
                updated_at=datetime.fromisoformat(row["updated_at"]),
                state=ExecutionFactState(row["state"]),
            )
        except (TypeError, ValueError, KeyError, json.JSONDecodeError) as exc:
            raise ExecutionFactPersistenceError(
                "O ExecutionFact persistido contém dados inválidos."
            ) from exc

    def list_for_evidence(
        self, evidence_id: str
    ) -> tuple[ExecutionFact, ...]:
        normalized = _required(evidence_id, "evidence_id")
        try:
            rows = self._connection.execute(
                """
                SELECT execution_fact_id
                FROM platform_execution_facts
                WHERE evidence_id = ?
                ORDER BY created_at, execution_fact_id
                """,
                (normalized,),
            ).fetchall()
        except sqlite3.Error as exc:
            raise ExecutionFactPersistenceError(
                "Não foi possível listar ExecutionFacts."
            ) from exc
        return tuple(self.get(row["execution_fact_id"]) for row in rows)

    def delete(self, execution_fact_id: str) -> None:
        normalized = _required(execution_fact_id, "execution_fact_id")
        try:
            with self._connection:
                result = self._connection.execute(
                    """
                    DELETE FROM platform_execution_facts
                    WHERE execution_fact_id = ?
                    """,
                    (normalized,),
                )
                if result.rowcount != 1:
                    raise ExecutionFactNotFoundError(
                        f"ExecutionFact não encontrado: {normalized}."
                    )
        except ExecutionFactNotFoundError:
            raise
        except sqlite3.Error as exc:
            raise ExecutionFactPersistenceError(
                "Não foi possível remover o ExecutionFact."
            ) from exc

    def close(self) -> None:
        if self._connection is not None:
            self._connection.close()
            self._connection = None

    def __enter__(self) -> "SQLiteExecutionFactStore":
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        self.close()


def _fact_types():
    from platform_sdk.execution_fact import ExecutionFact, ExecutionFactState

    return ExecutionFact, ExecutionFactState


def _required(value: object, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} deve ser texto não vazio.")
    return value.strip()


__all__ = [
    "ExecutionFactNotFoundError",
    "ExecutionFactPersistenceError",
    "SQLiteExecutionFactStore",
]
