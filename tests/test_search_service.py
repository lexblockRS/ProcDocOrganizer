import json
from dataclasses import FrozenInstanceError
from pathlib import Path
from tempfile import TemporaryDirectory
import sqlite3
import unittest

from models import Document, Project
from services import SearchService as LegacySearchService
from services.indexing import DocumentIndexer
from services.search import (
    LegacyIndexedSearchService,
    SearchFilters,
    SearchResult,
    SqliteFtsSearchIndex,
)
from services.search.search_query_builder import SearchQueryBuilder


class SearchServiceTests(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = TemporaryDirectory()
        self.root = Path(self.temporary_directory.name)
        self.database_path = self.root / "database.db"
        self.processing = self.root / "processing"
        self.processing.mkdir()
        self.indexer = DocumentIndexer(self.database_path)
        self._index(
            "a" * 64,
            "Portaria de Afastamento",
            "2026-05-20",
            "portaria",
            "documents/nativo.pdf",
            [
                "O afastamento do Professor Alexander Souza Block foi autorizado.",
                "A administração pública observará o prazo regulamentar.",
            ],
            "native.json",
        )
        self._index(
            "b" * 64,
            "Relatório digitalizado",
            "2025-01-10",
            "relatorio",
            "documents/ocr.pdf",
            ["Homologação definitiva com jabuticaba federal reconhecida pelo OCR."],
            "ocr.json",
        )
        self._index(
            "c" * 64,
            "Ato antigo",
            "2024-03-01",
            "portaria",
            "documents/antigo.pdf",
            ["Afastamento e administração constam neste documento."],
            "old.json",
        )
        self.index = SqliteFtsSearchIndex(self.database_path)
        self.service = LegacyIndexedSearchService(self.index)

    def tearDown(self):
        self.temporary_directory.cleanup()

    def _index(self, sha, title, date, kind, path, pages, filename):
        data = {
            "document_sha256": sha,
            "processed_at": "2026-07-22T12:00:00",
            "status": "processed",
            "page_count": len(pages),
            "pages": [
                {"page": number, "text": text}
                for number, text in enumerate(pages, 1)
            ],
            "metadata": {
                "title": title,
                "document_type": kind,
                "document_date": date,
            },
        }
        json_path = self.processing / filename
        json_path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
        self.indexer.index_processing_result(
            json_path, original_filename=Path(path).name, stored_path=path
        )

    def test_filters_are_deeply_immutable_and_normalize_terms(self):
        source = [" afastamento "]
        filters = SearchFilters(terms=source)
        source.append("outro")
        self.assertEqual(filters.terms, ("afastamento",))
        with self.assertRaises(FrozenInstanceError):
            filters.limit = 10

    def test_result_is_immutable_and_has_no_database_dependency(self):
        result = SearchResult("a" * 64, "Título", 1, "trecho", 1.0, None, None, None)
        with self.assertRaises(FrozenInstanceError):
            result.snippet = "alterado"

    def test_query_builder_parameterizes_match_and_filters(self):
        filters = SearchFilters(
            terms=["afastamento"], document_type="portaria",
            start_date="2024-01-01", end_date="2026-12-31", limit=5, offset=2,
        )
        sql, parameters = SearchQueryBuilder().build(filters)
        self.assertNotIn("afastamento", sql)
        self.assertNotIn("portaria", sql)
        self.assertEqual(parameters, (
            '"afastamento"', "portaria", "2024-01-01", "2026-12-31",
            "processed", 5, 2,
        ))
        self.assertIn("document_pages_fts MATCH ?", sql)

    def test_simple_match_returns_native_document(self):
        results = self.service.search(SearchFilters(terms=["afastamento"]))
        self.assertEqual({result.document_identity for result in results}, {"a" * 64, "c" * 64})
        self.assertEqual(results[0].page_number, 1)

    def test_phrase_requires_adjacent_terms(self):
        results = self.service.search_phrase("Professor Alexander Souza Block")
        self.assertEqual(len(results), 1)
        self.assertIn("Professor Alexander Souza Block", results[0].snippet)

    def test_all_terms_uses_and(self):
        results = self.service.search_all_terms(["afastamento", "administração"])
        self.assertEqual([result.document_identity for result in results], ["c" * 64])

    def test_any_terms_uses_or(self):
        results = self.service.search_any_terms(["jabuticaba", "Professor"])
        self.assertEqual({result.document_identity for result in results}, {"a" * 64, "b" * 64})

    def test_ocr_text_is_searched_like_native_text(self):
        result = self.service.search(SearchFilters(terms=["jabuticaba"]))[0]
        self.assertEqual(result.document_title, "Relatório digitalizado")
        self.assertEqual(result.file_path, "documents/ocr.pdf")

    def test_snippet_is_automatic_and_not_the_full_page(self):
        long_text = "prefixo " * 100 + "termoexclusivo " + "sufixo " * 100
        self._index("d" * 64, "Longo", "2023-01-01", "nota", "long.pdf", [long_text], "long.json")
        result = self.service.search(SearchFilters(terms=["termoexclusivo"]))[0]
        self.assertIn("termoexclusivo", result.snippet)
        self.assertLessEqual(len(result.snippet), self.service.MAX_SNIPPET_LENGTH)
        self.assertNotEqual(result.snippet, long_text)

    def test_ordering_uses_score_then_date_then_title(self):
        results = self.service.search(SearchFilters(terms=["afastamento"]))
        self.assertLessEqual(results[0].score, results[1].score)
        if results[0].score == results[1].score:
            self.assertGreaterEqual(results[0].document_date, results[1].document_date)

    def test_zero_results(self):
        self.assertEqual(self.service.search(SearchFilters(terms=["inexistente"])), ())

    def test_accents_and_case_are_normalized_by_fts5(self):
        lower = self.service.search(SearchFilters(terms=["administracao"]))
        upper = self.service.search(SearchFilters(terms=["ADMINISTRAÇÃO"]))
        self.assertEqual(len(lower), 2)
        self.assertEqual(
            [item.document_identity for item in lower],
            [item.document_identity for item in upper],
        )

    def test_metadata_and_date_filters(self):
        results = self.service.search(SearchFilters(
            terms=["afastamento"], document_type="portaria",
            start_date="2025-01-01",
        ))
        self.assertEqual([result.document_identity for result in results], ["a" * 64])

    def test_limit_and_offset(self):
        first = self.service.search(SearchFilters(terms=["afastamento"], limit=1))
        second = self.service.search(SearchFilters(terms=["afastamento"], limit=1, offset=1))
        self.assertEqual(len(first), 1)
        self.assertEqual(len(second), 1)
        self.assertNotEqual(first[0].document_identity, second[0].document_identity)

    def test_invalid_parameters_are_rejected(self):
        invalid = (
            lambda: SearchFilters(terms=[]),
            lambda: SearchFilters(terms=[""]),
            lambda: SearchFilters(terms=["x"], match_mode="near"),
            lambda: SearchFilters(phrase="x", match_mode="phrase", limit=0),
            lambda: SearchFilters(terms=["x"], offset=-1),
            lambda: SearchFilters(terms=["x"], start_date="22/07/2026"),
            lambda: SearchFilters(terms=["x"], start_date="2026-02-01", end_date="2025-01-01"),
        )
        for factory in invalid:
            with self.subTest(factory=factory), self.assertRaises((TypeError, ValueError)):
                factory()

    def test_sql_metacharacters_are_not_concatenated_or_executed(self):
        malicious = "x'); DROP TABLE documents; --"
        sql, parameters = SearchQueryBuilder().build(SearchFilters(terms=[malicious]))
        self.assertNotIn(malicious, sql)
        self.assertEqual(
            self.service.search(SearchFilters(terms=[malicious])), ()
        )
        connection = sqlite3.connect(self.database_path)
        try:
            count = connection.execute("SELECT COUNT(*) FROM documents").fetchone()[0]
        finally:
            connection.close()
        self.assertEqual(count, 3)

    def test_search_connection_is_read_only(self):
        connection = self.index._open_read_only()
        try:
            with self.assertRaises(sqlite3.OperationalError):
                connection.execute("DELETE FROM documents")
        finally:
            connection.close()

    def test_ui_compatibility_adapter_also_uses_fts_index(self):
        project = Project.create("Busca", self.root)
        document = Document.create(
            "nativo.pdf", "documents/nativo.pdf", sha256="a" * 64
        )
        results = LegacySearchService().search(project, [document], "Professor Alexander")
        self.assertEqual(len(results), 1)
        self.assertIs(results[0].document, document)
        self.assertEqual(results[0].page, 1)


if __name__ == "__main__":
    unittest.main()
