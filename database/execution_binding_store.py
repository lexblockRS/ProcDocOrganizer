"""Persistência SQLite específica de ExecutionBinding."""

from __future__ import annotations

from datetime import datetime
import json
from pathlib import Path
import sqlite3
from typing import TYPE_CHECKING

from .database import initialize_database

if TYPE_CHECKING:
    from platform_sdk.execution_binding import ExecutionBinding


class ExecutionBindingPersistenceError(RuntimeError):
    """Falha ao persistir ou reidratar um Binding."""


class ExecutionBindingNotFoundError(ExecutionBindingPersistenceError):
    """O Binding solicitado não existe."""


class SQLiteExecutionBindingStore:
    """Store direto para enquadramentos, sem ORM."""

    def __init__(self, database_path: str | Path) -> None:
        self.database_path = Path(database_path)
        initialize_database(self.database_path)
        self._connection = sqlite3.connect(self.database_path)
        self._connection.row_factory = sqlite3.Row
        self._connection.execute("PRAGMA foreign_keys = ON")

    def save(self, binding: ExecutionBinding) -> None:
        ExecutionBinding, _BindingOrigin = _binding_types()
        if not isinstance(binding, ExecutionBinding):
            raise TypeError(
                "binding deve ser platform_sdk.ExecutionBinding."
            )
        try:
            with self._connection:
                self._connection.execute(
                    """
                    INSERT INTO platform_execution_bindings (
                        binding_id, execution_fact_id, criterion_id,
                        requirement_id, execution_rule_id, origin,
                        created_at, metadata_json
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(binding_id) DO UPDATE SET
                        execution_fact_id = excluded.execution_fact_id,
                        criterion_id = excluded.criterion_id,
                        requirement_id = excluded.requirement_id,
                        execution_rule_id = excluded.execution_rule_id,
                        origin = excluded.origin,
                        created_at = excluded.created_at,
                        metadata_json = excluded.metadata_json
                    """,
                    (
                        binding.binding_id,
                        binding.execution_fact_id,
                        binding.criterion_id,
                        binding.requirement_id,
                        binding.execution_rule_id,
                        binding.origin.value,
                        binding.created_at.isoformat(),
                        json.dumps(
                            list(binding.metadata),
                            ensure_ascii=False,
                            separators=(",", ":"),
                        ),
                    ),
                )
        except sqlite3.IntegrityError as exc:
            raise ExecutionBindingPersistenceError(
                "ExecutionFact inválido ou já associado."
            ) from exc
        except sqlite3.Error as exc:
            raise ExecutionBindingPersistenceError(
                "Não foi possível salvar o Binding."
            ) from exc

    def get(self, binding_id: str) -> ExecutionBinding:
        return self._from_row(self._row_by(
            "binding_id", _required(binding_id, "binding_id")
        ))

    def get_for_fact(self, execution_fact_id: str) -> ExecutionBinding | None:
        normalized = _required(
            execution_fact_id, "execution_fact_id"
        )
        try:
            row = self._connection.execute(
                """
                SELECT *
                FROM platform_execution_bindings
                WHERE execution_fact_id = ?
                """,
                (normalized,),
            ).fetchone()
        except sqlite3.Error as exc:
            raise ExecutionBindingPersistenceError(
                "Não foi possível localizar o Binding."
            ) from exc
        return None if row is None else self._from_row(row)

    def delete(self, binding_id: str) -> None:
        normalized = _required(binding_id, "binding_id")
        try:
            with self._connection:
                result = self._connection.execute(
                    """
                    DELETE FROM platform_execution_bindings
                    WHERE binding_id = ?
                    """,
                    (normalized,),
                )
                if result.rowcount != 1:
                    raise ExecutionBindingNotFoundError(
                        f"Binding não encontrado: {normalized}."
                    )
        except ExecutionBindingNotFoundError:
            raise
        except sqlite3.Error as exc:
            raise ExecutionBindingPersistenceError(
                "Não foi possível remover o Binding."
            ) from exc

    def _row_by(self, column: str, value: str) -> sqlite3.Row:
        try:
            row = self._connection.execute(
                f"SELECT * FROM platform_execution_bindings "
                f"WHERE {column} = ?",
                (value,),
            ).fetchone()
        except sqlite3.Error as exc:
            raise ExecutionBindingPersistenceError(
                "Não foi possível abrir o Binding."
            ) from exc
        if row is None:
            raise ExecutionBindingNotFoundError(
                f"Binding não encontrado: {value}."
            )
        return row

    @staticmethod
    def _from_row(row: sqlite3.Row) -> ExecutionBinding:
        try:
            ExecutionBinding, BindingOrigin = _binding_types()
            metadata = json.loads(row["metadata_json"])
            return ExecutionBinding(
                binding_id=row["binding_id"],
                execution_fact_id=row["execution_fact_id"],
                criterion_id=row["criterion_id"],
                requirement_id=row["requirement_id"],
                execution_rule_id=row["execution_rule_id"],
                origin=BindingOrigin(row["origin"]),
                created_at=datetime.fromisoformat(row["created_at"]),
                metadata=tuple((item[0], item[1]) for item in metadata),
            )
        except (TypeError, ValueError, KeyError, json.JSONDecodeError) as exc:
            raise ExecutionBindingPersistenceError(
                "O Binding persistido contém dados inválidos."
            ) from exc

    def close(self) -> None:
        if self._connection is not None:
            self._connection.close()
            self._connection = None

    def __enter__(self) -> "SQLiteExecutionBindingStore":
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        self.close()


def _binding_types():
    from platform_sdk.execution_binding import BindingOrigin, ExecutionBinding

    return ExecutionBinding, BindingOrigin


def _required(value: object, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} deve ser texto não vazio.")
    return value.strip()


__all__ = [
    "ExecutionBindingNotFoundError",
    "ExecutionBindingPersistenceError",
    "SQLiteExecutionBindingStore",
]
