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

__all__ = [
    "DatabaseError", "FTS5UnavailableError", "INDEX_VERSION",
    "MigrationError", "ProjectDatabase", "SUPPORTED_SCHEMA_VERSION",
    "SchemaVersionError", "apply_migrations", "get_schema_version",
    "initialize_database",
]
