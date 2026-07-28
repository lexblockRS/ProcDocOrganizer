"""Infraestrutura de compatibilidade e migração do schema .pdop."""

from abc import ABC, abstractmethod
from collections.abc import Mapping
from typing import Any

CURRENT_SCHEMA_VERSION = 1


class SchemaMigrationError(RuntimeError):
    """Erro esperado na seleção ou execução de migrações."""


class UnknownSchemaError(SchemaMigrationError):
    """A versão informada não pertence ao registry."""


class MigrationNotFoundError(SchemaMigrationError):
    """Não existe migrador para o passo solicitado."""


class InvalidMigrationChainError(SchemaMigrationError):
    """A cadeia contém salto ou produz uma versão inesperada."""


class FutureSchemaError(SchemaMigrationError):
    """O projeto possui schema mais novo que o suportado."""


class SchemaMigration(ABC):
    @abstractmethod
    def source_version(self) -> int:
        """Versão aceita como entrada."""

    @abstractmethod
    def target_version(self) -> int:
        """Versão produzida como saída."""

    @abstractmethod
    def migrate(self, payloads: Mapping[str, Any]) -> dict[str, Any]:
        """Valida e transforma os payloads do contêiner."""


class IdentityMigration(SchemaMigration):
    def source_version(self) -> int:
        return CURRENT_SCHEMA_VERSION

    def target_version(self) -> int:
        return CURRENT_SCHEMA_VERSION

    def migrate(self, payloads: Mapping[str, Any]) -> dict[str, Any]:
        if not isinstance(payloads, Mapping):
            raise InvalidMigrationChainError(
                "payloads da migration identity devem ser um mapping."
            )
        metadata = payloads.get("metadata.json")
        if not isinstance(metadata, dict):
            raise InvalidMigrationChainError(
                "metadata.json ausente ou inválido."
            )
        if metadata.get("schema_version") != CURRENT_SCHEMA_VERSION:
            raise InvalidMigrationChainError(
                "migration identity recebeu schema incompatível."
            )
        return dict(payloads)


class SchemaRegistry:
    """Mantém schemas conhecidos e migradores direcionados."""

    def __init__(self, current_version: int | None = None) -> None:
        self._schemas: set[int] = set()
        self._migrations: dict[tuple[int, int], SchemaMigration] = {}
        self._current_version = current_version

    @property
    def current_version(self) -> int:
        if self._current_version is None:
            raise UnknownSchemaError("registry não possui schema atual.")
        return self._current_version

    def register_schema(self, version: int, *, current: bool = False) -> None:
        self._require_version(version)
        self._schemas.add(version)
        if current or self._current_version is None:
            self._current_version = version

    def register_migration(self, migration: SchemaMigration) -> None:
        if not isinstance(migration, SchemaMigration):
            raise TypeError("migration deve implementar SchemaMigration.")
        source = migration.source_version()
        target = migration.target_version()
        self._require_version(source)
        self._require_version(target)
        if source not in self._schemas or target not in self._schemas:
            raise UnknownSchemaError(
                "schemas de origem e destino devem estar registrados."
            )
        if target != source and target != source + 1:
            raise InvalidMigrationChainError(
                f"salto de schema inválido: {source} -> {target}."
            )
        self._migrations[(source, target)] = migration

    def is_known(self, version: int) -> bool:
        return version in self._schemas

    def require_known(self, version: int) -> None:
        self._require_version(version)
        if version > self.current_version:
            raise FutureSchemaError(
                f"schema futuro incompatível: {version}."
            )
        if version not in self._schemas:
            raise UnknownSchemaError(f"schema desconhecido: {version}.")

    def find_migration(
        self, source: int, target: int
    ) -> SchemaMigration:
        try:
            return self._migrations[(source, target)]
        except KeyError as exc:
            raise MigrationNotFoundError(
                f"migração inexistente: {source} -> {target}."
            ) from exc

    @staticmethod
    def _require_version(version: int) -> None:
        if isinstance(version, bool) or not isinstance(version, int) or version < 1:
            raise UnknownSchemaError(
                f"versão de schema inválida: {version!r}."
            )


class MigrationPipeline:
    """Executa somente passos adjacentes até o schema atual."""

    def __init__(self, registry: SchemaRegistry) -> None:
        if not isinstance(registry, SchemaRegistry):
            raise TypeError("registry deve ser SchemaRegistry.")
        self._registry = registry

    def migrate(
        self,
        payloads: Mapping[str, Any],
        source_version: int,
        target_version: int | None = None,
    ) -> dict[str, Any]:
        self._registry.require_known(source_version)
        target = (
            self._registry.current_version
            if target_version is None
            else target_version
        )
        self._registry.require_known(target)
        if source_version > target:
            raise InvalidMigrationChainError(
                "migração regressiva não é permitida."
            )
        if source_version == target:
            migration = self._registry.find_migration(source_version, target)
            return self._execute(migration, payloads, target)

        migrated = dict(payloads)
        current = source_version
        while current < target:
            next_version = current + 1
            migration = self._registry.find_migration(current, next_version)
            if (
                migration.source_version() != current
                or migration.target_version() != next_version
            ):
                raise InvalidMigrationChainError(
                    "migrador não corresponde ao passo solicitado."
                )
            migrated = self._execute(migration, migrated, next_version)
            current = next_version
        return migrated

    @staticmethod
    def _execute(
        migration: SchemaMigration,
        payloads: Mapping[str, Any],
        expected_version: int,
    ) -> dict[str, Any]:
        migrated = migration.migrate(payloads)
        if not isinstance(migrated, dict):
            raise InvalidMigrationChainError(
                "migrador deve retornar um dicionário."
            )
        metadata = migrated.get("metadata.json")
        if (
            not isinstance(metadata, dict)
            or metadata.get("schema_version") != expected_version
        ):
            raise InvalidMigrationChainError(
                "migrador produziu uma versão inesperada."
            )
        return migrated


def create_default_schema_registry() -> SchemaRegistry:
    registry = SchemaRegistry()
    registry.register_schema(CURRENT_SCHEMA_VERSION, current=True)
    registry.register_migration(IdentityMigration())
    return registry


def create_default_migration_pipeline() -> MigrationPipeline:
    return MigrationPipeline(create_default_schema_registry())
