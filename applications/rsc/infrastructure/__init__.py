"""Infraestrutura de persistência do projeto RSC."""

from .project_repository import (
    APPLICATION_VERSION,
    SCHEMA_VERSION,
    InvalidProjectFileError,
    ProjectRepository,
    ProjectSnapshot,
)
from .serializers import (
    ActivitySerializer,
    DocumentSerializer,
    EvidenceSerializer,
    ProcessSerializer,
    ProjectSerializer,
    SummarySerializer,
)
from .document_files import DocumentFileIdentity, DocumentHashService
from .schema_migration import (
    CURRENT_SCHEMA_VERSION,
    FutureSchemaError,
    IdentityMigration,
    InvalidMigrationChainError,
    MigrationNotFoundError,
    MigrationPipeline,
    SchemaMigration,
    SchemaMigrationError,
    SchemaRegistry,
    UnknownSchemaError,
    create_default_migration_pipeline,
    create_default_schema_registry,
)

__all__ = [
    "APPLICATION_VERSION",
    "CURRENT_SCHEMA_VERSION",
    "SCHEMA_VERSION",
    "ActivitySerializer",
    "DocumentSerializer",
    "DocumentFileIdentity",
    "DocumentHashService",
    "EvidenceSerializer",
    "FutureSchemaError",
    "IdentityMigration",
    "InvalidMigrationChainError",
    "InvalidProjectFileError",
    "MigrationNotFoundError",
    "MigrationPipeline",
    "ProcessSerializer",
    "ProjectRepository",
    "ProjectSerializer",
    "ProjectSnapshot",
    "SchemaMigration",
    "SchemaMigrationError",
    "SchemaRegistry",
    "SummarySerializer",
    "UnknownSchemaError",
    "create_default_migration_pipeline",
    "create_default_schema_registry",
]
