import json
from pathlib import Path
import sqlite3
from tempfile import TemporaryDirectory
import unittest
from uuid import uuid4

from database import ProjectDatabase, get_schema_version, initialize_database
from database.schema import MIGRATION_V1_STATEMENTS, SUPPORTED_SCHEMA_VERSION
from models import Evidence
from services.evidence_repository import (
    DuplicateEvidenceError,
    EvidenceNotFoundError,
    EvidenceRepository,
    EvidenceRepositoryError,
)
from services.indexing import DocumentIndexer
from services.search import (
    LegacyIndexedSearchService,
    SearchFilters,
    SqliteFtsSearchIndex,
)


SHA_A = "a" * 64
SHA_B = "b" * 64
CREATED = "2026-01-10T10:00:00"
UPDATED = "2026-01-11T11:00:00"


class EvidenceRepositoryTests(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = TemporaryDirectory()
        self.root = Path(self.temporary_directory.name)
        self.database_path = self.root / "database.db"
        self.processing = self.root / "processing"
        self.processing.mkdir()
        self.indexer = DocumentIndexer(self.database_path)
        self.json_a = self._index(SHA_A, "Documento A", "termo pesquisável", "a.json")
        self.json_b = self._index(SHA_B, "Documento B", "outro conteúdo", "b.json")
        self.repository = EvidenceRepository(self.database_path, now_factory=lambda: UPDATED)

    def tearDown(self):
        self.temporary_directory.cleanup()

    def _index(self, sha, title, text, filename):
        path = self.processing / filename
        path.write_text(json.dumps({
            "document_sha256": sha,
            "processed_at": CREATED,
            "status": "processed",
            "page_count": 1,
            "pages": [{"page": 1, "text": text}],
            "metadata": {"title": title},
        }), encoding="utf-8")
        self.indexer.index_processing_result(path, stored_path=f"documents/{filename}.pdf")
        return path

    def evidence(self, **changes):
        values = {
            "document_sha256": SHA_A,
            "title": "Participação em comissão",
            "page_number": 3,
            "source_snippet": "designar o servidor",
            "user_notes": "Atuação institucional",
            "category": None,
            "start_date": "2022-01-01",
            "end_date": "2023-12-31",
            "timestamp": CREATED,
        }
        values.update(changes)
        return Evidence.create(**values)

    def test_new_database_is_created_at_current_version_with_evidences(self):
        path = self.root / "new.db"
        initialize_database(path)
        with ProjectDatabase(path) as database:
            self.assertEqual(
                get_schema_version(database.connection),
                SUPPORTED_SCHEMA_VERSION,
            )
            table = database.connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='evidences'"
            ).fetchone()
            self.assertIsNotNone(table)

    def test_migrates_version_one_database_without_recreating_old_schema(self):
        path = self.root / "old.db"
        connection = sqlite3.connect(path)
        try:
            for statement in MIGRATION_V1_STATEMENTS:
                connection.execute(statement)
            connection.execute("PRAGMA user_version = 1")
            connection.commit()
        finally:
            connection.close()
        initialize_database(path)
        with ProjectDatabase(path) as database:
            self.assertEqual(get_schema_version(database.connection), SUPPORTED_SCHEMA_VERSION)
            self.assertEqual(
                database.connection.execute(
                    "SELECT value FROM index_state WHERE key='schema_version'"
                ).fetchone()[0],
                str(SUPPORTED_SCHEMA_VERSION),
            )

    def test_migration_creates_only_useful_evidence_indexes(self):
        with ProjectDatabase(self.database_path) as database:
            indexes = {
                row["name"] for row in database.connection.execute("PRAGMA index_list(evidences)")
            }
        self.assertIn("idx_evidences_document_sha256", indexes)
        self.assertIn("idx_evidences_start_date", indexes)

    def test_add_and_get_by_id(self):
        evidence = self.evidence()
        self.assertEqual(self.repository.add(evidence), evidence)
        self.assertEqual(self.repository.get_by_id(evidence.id), evidence)

    def test_list_all_and_count(self):
        first = self.evidence(title="Primeira")
        second = self.evidence(title="Segunda", evidence_id=str(uuid4()))
        self.repository.add(first)
        self.repository.add(second)
        self.assertEqual(self.repository.count(), 2)
        self.assertEqual(set(self.repository.list_all()), {first, second})

    def test_list_by_document_and_multiple_documents(self):
        a = self.evidence()
        b = self.evidence(document_sha256=SHA_B, evidence_id=str(uuid4()))
        self.repository.add(a)
        self.repository.add(b)
        self.assertEqual(self.repository.list_by_document(SHA_A), [a])
        self.assertEqual(self.repository.list_by_document(SHA_B), [b])

    def test_multiple_evidences_for_same_document(self):
        items = [
            self.evidence(title=f"Evidência {number}", evidence_id=str(uuid4()))
            for number in range(3)
        ]
        for item in items:
            self.repository.add(item)
        self.assertEqual(len(self.repository.list_by_document(SHA_A)), 3)

    def test_update_preserves_created_at_and_changes_updated_at(self):
        original = self.evidence()
        self.repository.add(original)
        updated = self.repository.update(original.with_changes(
            title="Título atualizado", updated_at=UPDATED
        ))
        self.assertEqual(updated.title, "Título atualizado")
        self.assertEqual(updated.created_at, CREATED)
        self.assertEqual(updated.updated_at, UPDATED)
        self.assertEqual(self.repository.get_by_id(original.id), updated)

    def test_update_can_explicitly_change_existing_document_link(self):
        original = self.evidence()
        self.repository.add(original)
        updated = self.repository.update(original.with_changes(document_sha256=SHA_B))
        self.assertEqual(updated.document_sha256, SHA_B)

    def test_update_requires_existing_evidence_but_not_document_projection(self):
        with self.assertRaises(EvidenceNotFoundError):
            self.repository.update(self.evidence())
        item = self.evidence()
        self.repository.add(item)
        updated = self.repository.update(
            item.with_changes(document_sha256="c" * 64)
        )
        self.assertEqual(updated.document_sha256, "c" * 64)

    def test_delete_and_exists(self):
        item = self.evidence()
        self.repository.add(item)
        self.assertTrue(self.repository.exists(item.id))
        self.assertTrue(self.repository.delete(item.id))
        self.assertFalse(self.repository.exists(item.id))
        self.assertFalse(self.repository.delete(item.id))

    def test_duplicate_id_is_rejected(self):
        item = self.evidence()
        self.repository.add(item)
        with self.assertRaises(DuplicateEvidenceError):
            self.repository.add(item)

    def test_repository_persists_without_querying_document_projection(self):
        item = self.evidence(document_sha256="c" * 64)
        self.assertEqual(self.repository.add(item), item)

    def test_model_preserves_opaque_identity_and_normalizes_other_fields(self):
        item = self.evidence(
            document_sha256=SHA_A.upper(), title="  Título  ", source_snippet="  ",
            user_notes=None, category=" sem classificação ",
        )
        self.assertEqual(item.document_identity, SHA_A.upper())
        self.assertEqual(item.document_sha256, SHA_A.upper())
        self.assertEqual(item.title, "Título")
        self.assertIsNone(item.source_snippet)
        self.assertEqual(item.category, "sem classificação")

    def test_optional_fields_accept_none(self):
        item = self.evidence(
            page_number=None, source_snippet=None, user_notes=None, category=None,
            start_date=None, end_date=None,
        )
        self.repository.add(item)
        self.assertEqual(self.repository.get_by_id(item.id), item)

    def test_invalid_identity_title_page_id_dates_and_timestamps(self):
        invalid = (
            lambda: self.evidence(document_identity=""),
            lambda: self.evidence(title="   "),
            lambda: self.evidence(page_number=0),
            lambda: self.evidence(evidence_id="not-a-uuid"),
            lambda: self.evidence(start_date="2024-02-01", end_date="2024-01-01"),
            lambda: self.evidence(start_date="01/02/2024"),
            lambda: self.evidence(timestamp="not-a-timestamp"),
        )
        for factory in invalid:
            with self.subTest(factory=factory), self.assertRaises(ValueError):
                factory()

    def test_list_all_order_is_start_date_created_at_title(self):
        later = self.evidence(
            title="C", start_date="2024-01-01", end_date=None,
            evidence_id=str(uuid4()),
        )
        earlier_b = self.evidence(title="B", start_date="2023-01-01", evidence_id=str(uuid4()))
        earlier_a = self.evidence(title="A", start_date="2023-01-01", evidence_id=str(uuid4()))
        undated = self.evidence(title="D", start_date=None, end_date=None, evidence_id=str(uuid4()))
        for item in (later, earlier_b, undated, earlier_a):
            self.repository.add(item)
        self.assertEqual([item.title for item in self.repository.list_all()], ["A", "B", "C", "D"])

    def test_list_by_document_orders_page_then_date_then_title_with_nulls_last(self):
        items = (
            self.evidence(title="Sem página", page_number=None, evidence_id=str(uuid4())),
            self.evidence(title="Página dois", page_number=2, evidence_id=str(uuid4())),
            self.evidence(title="Página um", page_number=1, evidence_id=str(uuid4())),
        )
        for item in items:
            self.repository.add(item)
        self.assertEqual(
            [item.title for item in self.repository.list_by_document(SHA_A)],
            ["Página um", "Página dois", "Sem página"],
        )

    def test_transaction_rolls_back_insert_failure(self):
        with ProjectDatabase(self.database_path) as database:
            database.connection.execute(
                "CREATE TRIGGER reject_evidence BEFORE INSERT ON evidences "
                "BEGIN SELECT RAISE(ABORT, 'falha controlada'); END"
            )
            database.connection.commit()
        with self.assertRaises(EvidenceRepositoryError):
            self.repository.add(self.evidence())
        self.assertEqual(self.repository.count(), 0)

    def test_data_survives_close_and_reopen(self):
        item = self.evidence()
        self.repository.add(item)
        reopened = EvidenceRepository(self.database_path)
        self.assertEqual(reopened.get_by_id(item.id), item)

    def test_incremental_rebuild_preserves_evidence(self):
        item = self.evidence()
        self.repository.add(item)
        self.indexer.rebuild_incremental(self.processing)
        self.assertEqual(self.repository.get_by_id(item.id), item)

    def test_full_rebuild_preserves_evidence(self):
        item = self.evidence()
        self.repository.add(item)
        self.indexer.rebuild_full(self.processing)
        self.assertEqual(self.repository.get_by_id(item.id), item)
        self.assertTrue(self.indexer.is_indexed(SHA_A))

    def test_index_document_removal_preserves_domain_evidence(self):
        item = self.evidence()
        self.repository.add(item)
        self.indexer.remove_document(SHA_A)
        self.assertEqual(self.repository.get_by_id(item.id), item)
        self.assertEqual(self.repository.list_by_document(SHA_A), [item])

    def test_update_notes_preserves_unavailable_existing_document_link(self):
        item = self.evidence()
        self.repository.add(item)
        self.indexer.remove_document(SHA_A)

        updated = self.repository.update(
            item.with_changes(user_notes="Nota revisada", updated_at=UPDATED)
        )

        self.assertEqual(updated.document_sha256, SHA_A)
        self.assertEqual(updated.user_notes, "Nota revisada")

    def test_search_service_remains_functional_after_migration(self):
        results = LegacyIndexedSearchService(
            SqliteFtsSearchIndex(self.database_path)
        ).search(SearchFilters(terms=["pesquisavel"]))
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].document_sha256, SHA_A)


if __name__ == "__main__":
    unittest.main()
