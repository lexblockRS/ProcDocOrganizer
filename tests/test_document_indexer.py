import json
from pathlib import Path
import sqlite3
from tempfile import TemporaryDirectory
import unittest

from database import DatabaseError, ProjectDatabase
from services.indexing import (
    DocumentIndexer,
    IndexingResult,
    IndexingValidationError,
)


SHA = "a" * 64
OTHER_SHA = "b" * 64
NOW = "2026-07-22T12:00:00"


class DocumentIndexerTests(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = TemporaryDirectory()
        self.root = Path(self.temporary_directory.name)
        self.database_path = self.root / "database.db"
        self.processing_directory = self.root / "processing"
        self.processing_directory.mkdir()
        self.indexer = DocumentIndexer(
            self.database_path, now_factory=lambda: NOW
        )

    def tearDown(self):
        self.temporary_directory.cleanup()

    def write_result(self, name="result.json", **changes):
        data = {
            "document_sha256": SHA,
            "processed_at": NOW,
            "status": "processed",
            "page_count": 2,
            "pages": [
                {"page": 1, "text": "Administração pública"},
                {"page": 2, "text": "Segunda página"},
            ],
            "error": None,
            "metadata": {
                "title": " Portaria 10 ",
                "document_type": "portaria",
                "document_number": "10",
                "document_date": "2026-07-22",
                "issuing_organization": "UNIPAMPA",
                "sei_process_number": None,
                "sei_code": "123",
            },
            "metadata_extractor_version": 1,
        }
        data.update(changes)
        path = self.processing_directory / name
        path.write_text(
            json.dumps(data, ensure_ascii=False), encoding="utf-8"
        )
        return path

    def rows(self, statement, parameters=()):
        with ProjectDatabase(self.database_path) as database:
            return database.connection.execute(
                statement, parameters
            ).fetchall()

    def test_indexes_processed_document_metadata_pages_and_accents(self):
        path = self.write_result()
        result = self.indexer.index_processing_result(
            path, "portaria.pdf", "documents/portaria.pdf"
        )
        self.assertEqual(result.status, "indexed")
        self.assertEqual(result.pages_indexed, 2)

        document = self.rows("SELECT * FROM documents")[0]
        self.assertEqual(document["sha256"], SHA)
        self.assertEqual(document["title"], "Portaria 10")
        self.assertEqual(document["document_date"], "2026-07-22")
        self.assertEqual(document["original_filename"], "portaria.pdf")
        self.assertEqual(len(self.rows("SELECT * FROM document_pages")), 2)
        match = self.rows(
            "SELECT * FROM document_pages_fts "
            "WHERE document_pages_fts MATCH ?", ("administracao",)
        )
        self.assertEqual(len(match), 1)
        self.assertTrue(self.indexer.is_indexed(SHA))

    def test_empty_page_is_persisted_but_not_added_to_fts(self):
        path = self.write_result(
            pages=[
                {"page": 1, "text": "Texto"},
                {"page": 2, "text": "  \n"},
            ]
        )
        result = self.indexer.index_processing_result(path)
        self.assertEqual(result.pages_indexed, 1)
        self.assertEqual(len(self.rows("SELECT * FROM document_pages")), 2)
        self.assertEqual(len(self.rows("SELECT * FROM document_pages_fts")), 1)
        empty_text = self.rows(
            "SELECT text FROM document_pages WHERE page_number = 2"
        )[0]["text"]
        self.assertEqual(empty_text, "  \n")

    def test_null_characters_are_removed_from_relational_and_fts_text(self):
        path = self.write_result(
            page_count=1,
            pages=[{"page": 1, "text": "servid\x00ór efetivo"}],
        )
        self.indexer.index_processing_result(path)

        relational_text = self.rows(
            "SELECT text FROM document_pages"
        )[0]["text"]
        fts_text = self.rows(
            "SELECT text FROM document_pages_fts"
        )[0]["text"]
        self.assertEqual(relational_text, "servidór efetivo")
        self.assertEqual(fts_text, "servidór efetivo")
        accentless_match = self.rows(
            "SELECT page_number FROM document_pages_fts "
            "WHERE document_pages_fts MATCH ?", ("servidor",)
        )
        phrase_match = self.rows(
            "SELECT page_number FROM document_pages_fts "
            "WHERE document_pages_fts MATCH ?", ('"servidor efetivo"',)
        )
        self.assertEqual(len(accentless_match), 1)
        self.assertEqual(len(phrase_match), 1)

    def test_reindex_replaces_pages_and_updates_metadata_without_duplicates(self):
        path = self.write_result()
        self.indexer.index_processing_result(path)
        path = self.write_result(
            page_count=1,
            pages=[{"page": 1, "text": "Texto substituto"}],
            metadata={"title": "Novo título"},
        )
        result = self.indexer.index_processing_result(path)

        self.assertEqual(result.status, "updated")
        self.assertEqual(len(self.rows("SELECT * FROM documents")), 1)
        pages = self.rows("SELECT * FROM document_pages")
        self.assertEqual(len(pages), 1)
        self.assertEqual(pages[0]["text"], "Texto substituto")
        self.assertEqual(len(self.rows("SELECT * FROM document_pages_fts")), 1)
        self.assertEqual(
            self.rows("SELECT title FROM documents")[0]["title"],
            "Novo título",
        )

    def test_reindex_preserves_created_at_and_updates_other_timestamps(self):
        timestamps = iter((
            "2026-07-22T12:00:00",
            "2026-07-22T13:00:00",
        ))
        indexer = DocumentIndexer(
            self.database_path, now_factory=lambda: next(timestamps)
        )
        path = self.write_result()
        indexer.index_processing_result(path)
        indexer.index_processing_result(path)

        document = self.rows("SELECT * FROM documents")[0]
        self.assertEqual(document["created_at"], "2026-07-22T12:00:00")
        self.assertEqual(document["updated_at"], "2026-07-22T13:00:00")
        self.assertEqual(document["indexed_at"], "2026-07-22T13:00:00")

    def test_ocr_required_registers_document_and_removes_previous_index(self):
        path = self.write_result()
        self.indexer.index_processing_result(path)
        path = self.write_result(
            status="ocr_required", page_count=4, pages=[], metadata={}
        )
        result = self.indexer.index_processing_result(path)

        document = self.rows("SELECT * FROM documents")[0]
        self.assertEqual(result.status, "skipped")
        self.assertEqual(document["processing_status"], "ocr_required")
        self.assertEqual(document["page_count"], 4)
        self.assertIsNone(document["indexed_at"])
        self.assertEqual(len(self.rows("SELECT * FROM document_pages")), 0)
        self.assertEqual(len(self.rows("SELECT * FROM document_pages_fts")), 0)
        self.assertFalse(self.indexer.is_indexed(SHA))

    def test_failed_status_removes_old_textual_index(self):
        path = self.write_result()
        self.indexer.index_processing_result(path)
        path = self.write_result(
            status="failed", page_count=0, pages=[], metadata={}, error="erro"
        )
        result = self.indexer.index_processing_result(path)

        self.assertEqual(result.status, "removed")
        document = self.rows("SELECT * FROM documents")[0]
        self.assertEqual(document["processing_status"], "failed")
        self.assertIsNone(document["indexed_at"])
        self.assertEqual(len(self.rows("SELECT * FROM document_pages_fts")), 0)

    def test_remove_document_cleans_relational_and_fts_rows(self):
        self.indexer.index_processing_result(self.write_result())
        result = self.indexer.remove_document(SHA)
        self.assertEqual(result.status, "removed")
        self.assertEqual(len(self.rows("SELECT * FROM documents")), 0)
        self.assertEqual(len(self.rows("SELECT * FROM document_pages")), 0)
        self.assertEqual(len(self.rows("SELECT * FROM document_pages_fts")), 0)
        self.assertEqual(self.indexer.remove_document(SHA).status, "skipped")

    def test_incremental_rebuild_continues_after_invalid_json(self):
        self.write_result("b.json")
        self.write_result(
            "a.json", document_sha256=OTHER_SHA,
            status="ocr_required", pages=[], metadata={},
        )
        (self.processing_directory / "c.json").write_text(
            "{invalid", encoding="utf-8"
        )
        report = self.indexer.rebuild_incremental(self.processing_directory)

        self.assertEqual(report.total, 3)
        self.assertEqual(report.indexed, 1)
        self.assertEqual(report.skipped, 1)
        self.assertEqual(report.failed, 1)
        self.assertEqual(report.successful, 2)
        self.assertEqual(len(report.errors), 1)
        self.assertIn("c.json", report.errors[0].file)
        self.assertEqual(len(self.rows("SELECT * FROM documents")), 2)

    def test_rebuild_processes_json_files_in_deterministic_name_order(self):
        class RecordingIndexer(DocumentIndexer):
            def __init__(self, database_path):
                super().__init__(database_path)
                self.files = []

            def index_processing_result(self, processing_json_path, **kwargs):
                self.files.append(Path(processing_json_path).name)
                return IndexingResult(SHA, "indexed", 1, 0)

        for name in ("z.json", "A.json", "m.json"):
            (self.processing_directory / name).write_text("{}", encoding="utf-8")
        indexer = RecordingIndexer(self.database_path)
        report = indexer.rebuild_incremental(self.processing_directory)

        self.assertEqual(indexer.files, ["A.json", "m.json", "z.json"])
        self.assertEqual(report.indexed, 3)

    def test_full_rebuild_explicitly_removes_stale_documents(self):
        self.indexer.index_processing_result(self.write_result("old.json"))
        (self.processing_directory / "old.json").unlink()
        self.write_result("new.json", document_sha256=OTHER_SHA)

        report = self.indexer.rebuild_full(self.processing_directory)
        self.assertEqual(report.mode, "full")
        self.assertEqual(report.documents_removed_before_rebuild, 1)
        documents = self.rows("SELECT sha256 FROM documents")
        self.assertEqual([row["sha256"] for row in documents], [OTHER_SHA])

    def test_transaction_rolls_back_and_preserves_previous_index(self):
        path = self.write_result()
        self.indexer.index_processing_result(path)
        path = self.write_result(
            page_count=1,
            pages=[{"page": 1, "text": "Texto que deve falhar"}],
            metadata={"title": "Não persistir"},
        )
        with ProjectDatabase(self.database_path) as database:
            database.connection.execute(
                """CREATE TRIGGER fail_page_insert
                BEFORE INSERT ON document_pages
                BEGIN SELECT RAISE(ABORT, 'falha simulada'); END"""
            )
            database.connection.commit()

        with self.assertRaises(DatabaseError):
            self.indexer.index_processing_result(path)

        pages = self.rows("SELECT text FROM document_pages ORDER BY page_number")
        self.assertEqual(
            [page["text"] for page in pages],
            ["Administração pública", "Segunda página"],
        )
        self.assertEqual(
            self.rows("SELECT title FROM documents")[0]["title"],
            "Portaria 10",
        )

    def test_unknown_status_is_rejected_without_database_change(self):
        path = self.write_result(status="novo_status")
        with self.assertRaises(IndexingValidationError):
            self.indexer.index_processing_result(path)
        self.assertFalse(self.database_path.exists())

    def test_rejects_invalid_sha_page_numbers_and_duplicate_pages(self):
        invalid_cases = (
            {"document_sha256": "invalido"},
            {
                "page_count": 1,
                "pages": [{"page": 0, "text": "Texto"}],
            },
            {
                "page_count": 2,
                "pages": [
                    {"page": 1, "text": "Um"},
                    {"page": 1, "text": "Dois"},
                ],
            },
        )
        for index, changes in enumerate(invalid_cases):
            with self.subTest(changes=changes):
                path = self.write_result(f"invalid-{index}.json", **changes)
                with self.assertRaises(IndexingValidationError):
                    self.indexer.index_processing_result(path)

    def test_processed_rejects_page_count_different_from_pages_length(self):
        path = self.write_result(
            page_count=3,
            pages=[{"page": 1, "text": "Uma página"}],
        )
        with self.assertRaisesRegex(IndexingValidationError, "page_count divergente"):
            self.indexer.index_processing_result(path)

    def test_non_processed_statuses_accept_page_count_without_pages(self):
        for status, sha256 in (("ocr_required", SHA), ("failed", OTHER_SHA)):
            with self.subTest(status=status):
                path = self.write_result(
                    f"{status}.json",
                    document_sha256=sha256,
                    status=status,
                    page_count=9,
                    pages=[],
                    metadata={},
                )
                result = self.indexer.index_processing_result(path)
                self.assertEqual(result.status, "skipped")


if __name__ == "__main__":
    unittest.main()
