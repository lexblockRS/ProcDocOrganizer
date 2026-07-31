"""Infraestrutura SQLite do ProcDoc Organizer."""

from .database import ProjectDatabase, get_schema_version, initialize_database
from .migrations import (
    DatabaseError,
    FTS5UnavailableError,
    MigrationError,
    SchemaVersionError,
    apply_migrations,
)
from .schema import INDEX_VERSION, SUPPORTED_SCHEMA_VERSION
from .project_store import (
    ProjectNotFoundError,
    ProjectPersistenceError,
    SQLiteProjectStore,
)
from .evidence_store import (
    EvidenceNotFoundError,
    EvidencePersistenceError,
    SQLiteEvidenceStore,
)
from .execution_fact_store import (
    ExecutionFactNotFoundError,
    ExecutionFactPersistenceError,
    SQLiteExecutionFactStore,
)
from .execution_binding_store import (
    ExecutionBindingNotFoundError,
    ExecutionBindingPersistenceError,
    SQLiteExecutionBindingStore,
)

__all__ = [
    "DatabaseError", "FTS5UnavailableError", "INDEX_VERSION",
    "EvidenceNotFoundError", "EvidencePersistenceError",
    "ExecutionFactNotFoundError", "ExecutionFactPersistenceError",
    "ExecutionBindingNotFoundError", "ExecutionBindingPersistenceError",
    "MigrationError", "ProjectDatabase", "SUPPORTED_SCHEMA_VERSION",
    "ProjectNotFoundError", "ProjectPersistenceError", "SQLiteProjectStore",
    "SQLiteEvidenceStore",
    "SQLiteExecutionFactStore",
    "SQLiteExecutionBindingStore",
    "SchemaVersionError", "apply_migrations", "get_schema_version",
    "initialize_database",
]
