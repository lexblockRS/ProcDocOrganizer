import ast
from dataclasses import FrozenInstanceError
from datetime import date, datetime
from pathlib import Path
import sqlite3
from tempfile import TemporaryDirectory
import unittest

from services.search import (
    IndexMaintenanceIssue,
    IndexReconcileReport,
    InvalidIndexDocumentError,
    SearchIndexDocument,
    SearchIndexPage,
    SearchIndexRebuildError,
    SearchIndexStatus,
    SearchIndexWriteError,
    SearchQuery,
    SearchService,
    SqliteFtsIndexMaintainer,
    SqliteFtsSearchIndex,
)


class Source:
    def __init__(self, documents=(), error=None):
        self.documents = tuple(documents)
        self.error = error

    def iter_documents(self):
        if self.error:
            raise self.error
        return self.documents

    def get_document(self, identity):
        return next(
            (item for item in self.documents
             if item.document_identity == identity),
            None,
        )


def document(identity="opaque:A", name="Documento", pages=None):
    return SearchIndexDocument(
        document_identity=identity,
        document_name=name,
        document_type="portaria",
        document_date=date(2026, 7, 23),
        pages=tuple(pages or (
            SearchIndexPage(1, "Administração pública"),
            SearchIndexPage(2, ""),
        )),
    )


class MaintenanceContractTests(unittest.TestCase):
    def test_page_validation_empty_text_and_immutability(self):
        page = SearchIndexPage(1, "")
        self.assertEqual(page.text, "")
        with self.assertRaises(InvalidIndexDocumentError):
            SearchIndexPage(0, "x")
        with self.assertRaises(InvalidIndexDocumentError):
            SearchIndexPage(1, None)
        with self.assertRaises(FrozenInstanceError):
            page.text = "outro"

    def test_document_normalizes_identity_sorts_and_rejects_duplicates(self):
        value = SearchIndexDocument(
            " opaque:42 ", " Nome ",
            (SearchIndexPage(2, "b"), SearchIndexPage(1, "a")),
        )
        self.assertEqual(value.document_identity, "opaque:42")
        self.assertEqual(value.document_name, "Nome")
        self.assertEqual([page.page_number for page in value.pages], [1, 2])
        self.assertFalse(hasattr(value, "file_path"))
        with self.assertRaises(InvalidIndexDocumentError):
            SearchIndexDocument("", "Nome", ())
        with self.assertRaises(InvalidIndexDocumentError):
            SearchIndexDocument("id", "", ())
        with self.assertRaises(InvalidIndexDocumentError):
            SearchIndexDocument(
                "id", "Nome",
                (SearchIndexPage(1, "a"), SearchIndexPage(1, "b")),
            )

    def test_reports_are_immutable_and_validate_totals(self):
        issue = IndexMaintenanceIssue("code", "message")
        report = IndexReconcileReport(1, 0, inserted=1, issues=(issue,))
        self.assertIsInstance(report.issues, tuple)
        with self.assertRaises(FrozenInstanceError):
            report.inserted = 2
        with self.assertRaises(ValueError):
            IndexReconcileReport(1, 0)
        with self.assertRaises(ValueError):
            SearchIndexStatus(True, True, document_count=-1)


class SqliteFtsIndexMaintainerTests(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = TemporaryDirectory()
        self.root = Path(self.temporary_directory.name)
        self.database_path = self.root / "index.db"
        self.now = datetime(2026, 7, 23, 12, 0, 0)
        self.maintainer = SqliteFtsIndexMaintainer(
            self.database_path, now_factory=lambda: self.now
        )

    def tearDown(self):
        self.temporary_directory.cleanup()

    def rows(self, sql, parameters=()):
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        try:
            return connection.execute(sql, parameters).fetchall()
        finally:
            connection.close()

    def test_upsert_replaces_pages_is_idempotent_and_reader_works(self):
        self.maintainer.upsert(document())
        self.maintainer.upsert(document(
            name="Nome alterado",
            pages=(SearchIndexPage(1, "Texto substituto"),),
        ))
        self.assertEqual(len(self.rows("SELECT * FROM documents")), 1)
        pages = self.rows("SELECT * FROM document_pages")
        self.assertEqual([row["text"] for row in pages], ["Texto substituto"])
        result = SearchService(
            SqliteFtsSearchIndex(self.database_path)
        ).search(SearchQuery("substituto"))
        self.assertEqual(result.hits[0].document_name, "Nome alterado")

    def test_remove_is_idempotent_and_rejects_empty_identity(self):
        self.maintainer.upsert(document())
        self.assertTrue(self.maintainer.remove("opaque:A"))
        self.assertFalse(self.maintainer.remove("opaque:A"))
        with self.assertRaises(InvalidIndexDocumentError):
            self.maintainer.remove(" ")

    def test_rebuild_is_deterministic_and_preserves_previous_on_failure(self):
        self.maintainer.rebuild(Source((document("old"),)))
        with self.assertRaises(SearchIndexRebuildError):
            self.maintainer.rebuild(Source(error=RuntimeError("source failed")))
        self.assertEqual(
            [row["sha256"] for row in self.rows("SELECT sha256 FROM documents")],
            ["old"],
        )
        report = self.maintainer.rebuild(Source((
            document("b"), document("a", pages=(SearchIndexPage(1, "α"),)),
        )))
        self.assertEqual(report.indexed_documents, 2)
        self.assertEqual(report.indexed_pages, 2)
        status = self.maintainer.inspect()
        self.assertEqual(status.last_rebuild_at, self.now)

    def test_rebuild_write_failure_rolls_back_previous_index(self):
        self.maintainer.rebuild(Source((document("old"),)))
        connection = sqlite3.connect(self.database_path)
        try:
            connection.execute(
                """CREATE TRIGGER fail_maintenance_page
                BEFORE INSERT ON document_pages
                BEGIN SELECT RAISE(ABORT, 'simulated failure'); END"""
            )
            connection.commit()
        finally:
            connection.close()
        with self.assertRaises(SearchIndexRebuildError):
            self.maintainer.rebuild(Source((document("new"),)))
        self.assertEqual(
            [row["sha256"] for row in self.rows("SELECT sha256 FROM documents")],
            ["old"],
        )

    def test_reconcile_inserts_updates_removes_and_second_run_is_unchanged(self):
        self.maintainer.upsert(document("updated", name="Antes"))
        self.maintainer.upsert(document("orphan"))
        source = Source((
            document("updated", name="Depois"),
            document("inserted"),
        ))
        first = self.maintainer.reconcile(source)
        self.assertEqual(
            (first.inserted, first.updated, first.removed, first.unchanged),
            (1, 1, 1, 0),
        )
        second = self.maintainer.reconcile(source)
        self.assertEqual(
            (second.inserted, second.updated, second.removed, second.unchanged),
            (0, 0, 0, 2),
        )
        self.assertEqual(self.maintainer.inspect().last_reconcile_at, self.now)

    def test_reconcile_reports_one_document_failure_and_continues(self):
        class FailingMaintainer(SqliteFtsIndexMaintainer):
            def upsert(self, value):
                if value.document_identity == "broken":
                    raise SearchIndexWriteError("simulated")
                return super().upsert(value)

        maintainer = FailingMaintainer(
            self.database_path, now_factory=lambda: self.now
        )
        report = maintainer.reconcile(Source((
            document("broken"), document("valid"),
        )))
        self.assertEqual((report.inserted, report.failed), (1, 1))
        self.assertEqual(report.issues[0].code, "document_write_failed")
        self.assertEqual(
            [row["sha256"] for row in self.rows("SELECT sha256 FROM documents")],
            ["valid"],
        )

    def test_status_distinguishes_missing_schema_empty_and_valid(self):
        missing = self.maintainer.inspect()
        self.assertFalse(missing.available)
        empty_path = self.root / "empty.db"
        sqlite3.connect(empty_path).close()
        empty_schema = SqliteFtsIndexMaintainer(empty_path).inspect()
        self.assertTrue(empty_schema.available)
        self.assertFalse(empty_schema.schema_valid)
        invalid_path = self.root / "invalid.db"
        invalid_path.write_text("not a database", encoding="utf-8")
        invalid = SqliteFtsIndexMaintainer(invalid_path).inspect()
        self.assertFalse(invalid.schema_valid)
        self.assertNotIn("SELECT", invalid.issues[0].message)
        self.maintainer.rebuild(Source())
        valid = self.maintainer.inspect()
        self.assertTrue(valid.schema_valid)
        self.assertEqual((valid.document_count, valid.page_count), (0, 0))

    def test_public_contracts_have_no_forbidden_infrastructure(self):
        root = Path(__file__).parents[1] / "services" / "search"
        for name in (
            "maintenance_contracts.py",
            "search_index_maintainer.py",
            "search_index_source.py",
        ):
            tree = ast.parse((root / name).read_text(encoding="utf-8"))
            imports = " ".join(
                node.module or ""
                for node in ast.walk(tree)
                if isinstance(node, ast.ImportFrom)
            )
            imports += " ".join(
                alias.name
                for node in ast.walk(tree)
                if isinstance(node, ast.Import)
                for alias in node.names
            )
            self.assertNotIn("sqlite3", imports)
            self.assertNotIn("PySide", imports)


if __name__ == "__main__":
    unittest.main()
