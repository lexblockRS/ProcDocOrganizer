from copy import deepcopy
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from applications.rsc import RscApplication, RscApplicationFacade
from applications.rsc.infrastructure import (
    CURRENT_SCHEMA_VERSION,
    FutureSchemaError,
    IdentityMigration,
    InvalidMigrationChainError,
    MigrationNotFoundError,
    MigrationPipeline,
    ProjectRepository,
    SchemaMigration,
    SchemaRegistry,
    UnknownSchemaError,
    create_default_schema_registry,
)
from applications.rsc.use_cases import (
    CreateProcessCommand,
    LoadProjectCommand,
    SaveProjectCommand,
)


class EvidenceLookup:
    def exists(self, _evidence_id):
        return True


def payload(version=1):
    return {"metadata.json": {"schema_version": version}}


class VersionMigration(SchemaMigration):
    def __init__(self, source, target, produced=None):
        self.source = source
        self.target = target
        self.produced = target if produced is None else produced

    def source_version(self):
        return self.source

    def target_version(self):
        return self.target

    def migrate(self, payloads):
        migrated = deepcopy(dict(payloads))
        migrated["metadata.json"]["schema_version"] = self.produced
        migrated.setdefault("steps", []).append((self.source, self.target))
        return migrated


class SchemaRegistryTests(unittest.TestCase):
    def test_empty_registry_and_known_schema(self):
        empty = SchemaRegistry()
        with self.assertRaises(UnknownSchemaError):
            _ = empty.current_version

        registry = SchemaRegistry()
        registry.register_schema(CURRENT_SCHEMA_VERSION, current=True)
        self.assertEqual(registry.current_version, 1)
        self.assertTrue(registry.is_known(1))
        registry.require_known(1)

    def test_unknown_and_future_schemas_have_specific_errors(self):
        registry = SchemaRegistry()
        registry.register_schema(2, current=True)
        with self.assertRaises(UnknownSchemaError):
            registry.require_known(1)
        with self.assertRaises(FutureSchemaError):
            registry.require_known(3)

    def test_identity_migration_validates_and_returns_schema_one(self):
        original = payload()
        migrated = IdentityMigration().migrate(original)
        self.assertEqual(migrated, original)
        self.assertIsNot(migrated, original)
        with self.assertRaises(InvalidMigrationChainError):
            IdentityMigration().migrate(payload(2))

    def test_pipeline_executes_sequential_chain(self):
        registry = SchemaRegistry()
        for version in (1, 2, 3):
            registry.register_schema(version, current=version == 3)
        registry.register_migration(VersionMigration(1, 2))
        registry.register_migration(VersionMigration(2, 3))

        migrated = MigrationPipeline(registry).migrate(payload(1), 1)

        self.assertEqual(migrated["metadata.json"]["schema_version"], 3)
        self.assertEqual(migrated["steps"], [(1, 2), (2, 3)])

    def test_pipeline_rejects_missing_and_invalid_chains(self):
        registry = SchemaRegistry()
        registry.register_schema(1)
        registry.register_schema(2, current=True)
        pipeline = MigrationPipeline(registry)
        with self.assertRaises(MigrationNotFoundError):
            pipeline.migrate(payload(1), 1)

        registry.register_migration(VersionMigration(1, 2, produced=1))
        with self.assertRaises(InvalidMigrationChainError):
            pipeline.migrate(payload(1), 1)

        registry.register_schema(3, current=True)
        with self.assertRaises(InvalidMigrationChainError):
            registry.register_migration(VersionMigration(1, 3))

    def test_default_registry_exposes_only_current_identity(self):
        registry = create_default_schema_registry()
        self.assertEqual(registry.current_version, CURRENT_SCHEMA_VERSION)
        self.assertIsInstance(registry.find_migration(1, 1), IdentityMigration)
        with self.assertRaises(MigrationNotFoundError):
            registry.find_migration(1, 2)


class RepositoryMigrationIntegrationTests(unittest.TestCase):
    def test_repository_and_load_use_case_open_current_ep04_projects(self):
        with TemporaryDirectory() as temporary:
            path = Path(temporary) / "compatible.pdop"
            source_session = RscApplication().create_project_session(
                EvidenceLookup()
            )
            source_facade = RscApplicationFacade(source_session)
            created = source_facade.create_process(
                CreateProcessCommand("Pessoa", "Instituição")
            )
            source_facade.save_project(SaveProjectCommand(path))

            payloads = ProjectRepository().validate(path)
            self.assertEqual(
                payloads["metadata.json"]["schema_version"],
                CURRENT_SCHEMA_VERSION,
            )
            restored = RscApplication().create_project_session(
                EvidenceLookup()
            )
            result = RscApplicationFacade(restored).load_project(
                LoadProjectCommand(path)
            )
            self.assertEqual(result.process_count, 1)
            self.assertEqual(
                restored.rsc_process_service.list_processes()[0].id,
                created.process_id,
            )


if __name__ == "__main__":
    unittest.main()
