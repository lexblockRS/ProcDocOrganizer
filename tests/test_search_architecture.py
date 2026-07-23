import ast
import json
from dataclasses import FrozenInstanceError
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from services.indexing import DocumentIndexer
from services.search import (
    InvalidSearchQueryError,
    SearchHit,
    SearchIndexCorruptedError,
    SearchIndexUnavailableError,
    SearchMatchMode,
    SearchOptions,
    SearchQuery,
    SearchResultPage,
    SearchService,
    SearchSort,
    SqliteFtsSearchIndex,
)


class SearchContractsTests(unittest.TestCase):
    def test_query_rejects_empty_text_and_preserves_original(self):
        with self.assertRaises(InvalidSearchQueryError):
            SearchQuery("   ")
        query = SearchQuery("  expressão original  ")
        self.assertEqual(query.text, "  expressão original  ")

    def test_options_validate_limit_offset_dates_and_enums(self):
        invalid = (
            lambda: SearchOptions(limit=0),
            lambda: SearchOptions(limit=SearchOptions.MAX_LIMIT + 1),
            lambda: SearchOptions(offset=-1),
            lambda: SearchOptions(start_date="22/07/2026"),
            lambda: SearchOptions(
                start_date="2026-02-01", end_date="2025-01-01"
            ),
            lambda: SearchOptions(sort="relevance"),
            lambda: SearchOptions(match_mode="all"),
        )
        for factory in invalid:
            with self.subTest(factory=factory):
                with self.assertRaises(InvalidSearchQueryError):
                    factory()

    def test_hit_validates_page_snippet_and_score(self):
        with self.assertRaises(ValueError):
            SearchHit("doc", "Documento", 0, "")
        with self.assertRaises(TypeError):
            SearchHit("doc", "Documento", 1, None)
        with self.assertRaises(ValueError):
            SearchHit("doc", "Documento", 1, "", float("nan"))

    def test_result_page_is_immutable_and_validates_invariants(self):
        source = [SearchHit("doc", "Documento", 1, "trecho", 1.0)]
        page = SearchResultPage(source, 0, 1, None, False)
        source.clear()
        self.assertEqual(len(page.hits), 1)
        self.assertIsInstance(page.hits, tuple)
        with self.assertRaises(FrozenInstanceError):
            page.offset = 1
        with self.assertRaises(ValueError):
            SearchResultPage(page.hits, -1, 1, None, False)
        with self.assertRaises(ValueError):
            SearchResultPage(page.hits, 0, 0, None, False)
        with self.assertRaises(ValueError):
            SearchResultPage(page.hits, 0, 1, 2, False)


class FakeSearchIndex:
    def __init__(self, result=None, error=None):
        self.result = result or SearchResultPage((), 0, 0, None, False)
        self.error = error
        self.queries = []

    def search(self, query):
        self.queries.append(query)
        if self.error:
            raise self.error
        return self.result


class SearchServiceArchitectureTests(unittest.TestCase):
    def test_service_delegates_without_sqlite(self):
        expected = SearchResultPage((), 0, 0, None, False)
        index = FakeSearchIndex(expected)
        service = SearchService(index)
        query = SearchQuery("portaria")
        self.assertIs(service.search(query), expected)
        self.assertEqual(index.queries, [query])

    def test_compatibility_methods_delegate_to_same_flow(self):
        index = FakeSearchIndex()
        service = SearchService(index)
        service.search_phrase("ato administrativo")
        service.search_all_terms(["ato", "administrativo"])
        service.search_any_terms(["ato", "portaria"])
        self.assertEqual(
            [query.options.match_mode for query in index.queries],
            [
                SearchMatchMode.EXACT_PHRASE,
                SearchMatchMode.ALL_TERMS,
                SearchMatchMode.ANY_TERM,
            ],
        )

    def test_service_propagates_typed_errors(self):
        error = SearchIndexUnavailableError("indisponível")
        with self.assertRaises(SearchIndexUnavailableError) as raised:
            SearchService(FakeSearchIndex(error=error)).search(
                SearchQuery("consulta")
            )
        self.assertIs(raised.exception, error)

    def test_service_has_no_forbidden_imports(self):
        module_path = (
            Path(__file__).parents[1]
            / "services"
            / "search"
            / "search_service.py"
        )
        tree = ast.parse(module_path.read_text(encoding="utf-8"))
        imports = {
            alias.name
            for node in ast.walk(tree)
            if isinstance(node, ast.Import)
            for alias in node.names
        }
        imports.update(
            node.module or ""
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom)
        )
        forbidden = (
            "sqlite3", "pdf_view", "QPdfSearchModel",
            "project_tree_widget", "PySide6",
        )
        for name in forbidden:
            self.assertFalse(
                any(name.lower() in imported.lower() for imported in imports),
                f"Import proibido no SearchService: {name}",
            )

    def test_ui_search_layers_have_no_infrastructure_or_pdf_imports(self):
        root = Path(__file__).parents[1]
        files = (
            root / "controllers" / "search_controller.py",
            root / "ui" / "views" / "search_workspace.py",
            root / "ui" / "widgets" / "search_results_widget.py",
            root / "ui" / "widgets" / "search_preview_widget.py",
        )
        forbidden = (
            "sqlite3", "SqliteFtsSearchIndex", "SearchQueryBuilder",
            "PdfView", "QPdfSearchModel", "ProjectTreeWidget", "Document",
        )
        for path in files:
            tree = ast.parse(path.read_text(encoding="utf-8"))
            imports = {
                alias.name
                for node in ast.walk(tree)
                if isinstance(node, ast.Import)
                for alias in node.names
            }
            imports.update(
                f"{node.module or ''}.{alias.name}"
                for node in ast.walk(tree)
                if isinstance(node, ast.ImportFrom)
                for alias in node.names
            )
            with self.subTest(path=path.name):
                for name in forbidden:
                    self.assertFalse(
                        any(
                            name.lower()
                            in {
                                segment.lower()
                                for segment in imported.split(".")
                            }
                            for imported in imports
                        ),
                        f"Import proibido em {path.name}: {name}",
                    )

    def test_search_hit_has_no_document_or_evidence_dependency(self):
        root = Path(__file__).parents[1]
        source = (
            root / "services" / "search" / "contracts.py"
        ).read_text(encoding="utf-8")
        tree = ast.parse(source)
        imports = [
            node.module or ""
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom)
        ]
        self.assertFalse(any("document" in item.lower() for item in imports))
        self.assertFalse(any("evidence" in item.lower() for item in imports))

    def test_documents_core_does_not_import_search(self):
        root = Path(__file__).parents[1]
        files = (
            root / "controllers" / "documents_controller.py",
            root / "services" / "document_service.py",
            root / "models" / "document_read_models.py",
            root / "ui" / "views" / "documents_workspace.py",
        )
        for path in files:
            with self.subTest(path=path.name):
                self.assertNotIn(
                    "services.search", path.read_text(encoding="utf-8")
                )

    def test_navigation_contract_is_shared_and_neutral(self):
        root = Path(__file__).parents[1]
        source = (
            root / "contracts" / "navigation.py"
        ).read_text(encoding="utf-8")
        for forbidden in (
            "services.search", "ui.", "PdfView", "ProjectTreeWidget",
            "sqlite3", "file_path",
        ):
            self.assertNotIn(forbidden, source)

    def test_search_controller_does_not_import_documents_or_viewers(self):
        root = Path(__file__).parents[1]
        source = (
            root / "controllers" / "search_controller.py"
        ).read_text(encoding="utf-8")
        for forbidden in (
            "DocumentsController", "DocumentsWorkspace", "PdfView",
            "ProjectTreeWidget", "sqlite3",
        ):
            self.assertNotIn(forbidden, source)

    def test_project_controller_composes_core_service_and_index(self):
        root = Path(__file__).parents[1]
        source = (
            root / "core" / "project_controller.py"
        ).read_text(encoding="utf-8")
        self.assertIn("SearchService(", source)
        self.assertIn("SqliteFtsSearchIndex(", source)
        self.assertNotIn("LegacyIndexedSearchService(", source)


class SqliteFtsSearchIndexTests(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = TemporaryDirectory()
        self.root = Path(self.temporary_directory.name)
        self.database_path = self.root / "database.db"
        self.processing = self.root / "processing"
        self.processing.mkdir()
        self.indexer = DocumentIndexer(self.database_path)
        self._index(
            "a" * 64,
            "Portaria Alfa",
            "2026-01-01",
            "portaria",
            ["ato administrativo publicado", "termo comum"],
        )
        self._index(
            "b" * 64,
            "Relatório Beta",
            "2025-01-01",
            "relatorio",
            ["ato público administrativo", "termo comum"],
        )
        self.index = SqliteFtsSearchIndex(self.database_path)
        self.service = SearchService(self.index)

    def tearDown(self):
        self.temporary_directory.cleanup()

    def _index(self, sha, title, date, kind, pages):
        data = {
            "document_sha256": sha,
            "processed_at": "2026-07-23T10:00:00",
            "status": "processed",
            "page_count": len(pages),
            "pages": [
                {"page": number, "text": text}
                for number, text in enumerate(pages, 1)
            ],
            "metadata": {
                "title": title,
                "document_date": date,
                "document_type": kind,
            },
        }
        path = self.processing / f"{sha}.json"
        path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
        self.indexer.index_processing_result(path)

    def test_word_all_any_and_exact_phrase(self):
        word = self.service.search(SearchQuery("publicado"))
        all_terms = self.service.search(SearchQuery("ato administrativo"))
        any_term = self.service.search(SearchQuery(
            "publicado público",
            SearchOptions(match_mode=SearchMatchMode.ANY_TERM),
        ))
        phrase = self.service.search(SearchQuery(
            "ato administrativo",
            SearchOptions(match_mode=SearchMatchMode.EXACT_PHRASE),
        ))
        self.assertEqual(len(word.hits), 1)
        self.assertEqual(len(all_terms.hits), 2)
        self.assertEqual(len(any_term.hits), 2)
        self.assertEqual(len(phrase.hits), 1)

    def test_filters_snippet_page_and_normalized_score(self):
        page = self.service.search(SearchQuery(
            "ato",
            SearchOptions(
                document_type="portaria",
                start_date="2026-01-01",
                end_date="2026-12-31",
            ),
        ))
        self.assertEqual(len(page.hits), 1)
        hit = page.hits[0]
        self.assertEqual(hit.document_identity, "a" * 64)
        self.assertEqual(hit.page_number, 1)
        self.assertIn("ato", hit.snippet)
        self.assertIsNotNone(hit.score)
        self.assertGreaterEqual(hit.score, 0)

    def test_pagination_uses_limit_plus_one_without_exact_total(self):
        first = self.service.search(SearchQuery(
            "termo",
            SearchOptions(limit=1),
        ))
        second = self.service.search(SearchQuery(
            "termo",
            SearchOptions(limit=1, offset=1),
        ))
        self.assertEqual(first.page_size, 1)
        self.assertIsNone(first.total_hits)
        self.assertTrue(first.has_more)
        self.assertEqual(second.page_size, 1)
        self.assertFalse(second.has_more)
        self.assertNotEqual(
            first.hits[0].document_identity,
            second.hits[0].document_identity,
        )

    def test_all_sorts_are_stable(self):
        for sort in SearchSort:
            with self.subTest(sort=sort):
                first = self.service.search(SearchQuery(
                    "termo", SearchOptions(sort=sort)
                ))
                second = self.service.search(SearchQuery(
                    "termo", SearchOptions(sort=sort)
                ))
                self.assertEqual(first.hits, second.hits)
        by_date = self.service.search(SearchQuery(
            "termo", SearchOptions(sort=SearchSort.DOCUMENT_DATE_DESC)
        ))
        by_name = self.service.search(SearchQuery(
            "termo", SearchOptions(sort=SearchSort.DOCUMENT_NAME_ASC)
        ))
        self.assertEqual(by_date.hits[0].document_identity, "a" * 64)
        self.assertEqual(by_name.hits[0].document_identity, "a" * 64)

    def test_no_results_and_sql_injection(self):
        self.assertEqual(
            self.service.search(SearchQuery("inexistente")).hits, ()
        )
        malicious = "x'); DROP TABLE documents; --"
        self.assertEqual(
            self.service.search(SearchQuery(
                malicious,
                SearchOptions(match_mode=SearchMatchMode.EXACT_PHRASE),
            )).hits,
            (),
        )
        self.assertEqual(
            len(self.service.search(SearchQuery("ato")).hits), 2
        )

    def test_missing_invalid_and_missing_schema_are_typed(self):
        with self.assertRaises(SearchIndexUnavailableError):
            SqliteFtsSearchIndex(self.root / "missing.db").search(
                SearchQuery("ato")
            )
        invalid = self.root / "invalid.db"
        invalid.write_text("não é sqlite", encoding="utf-8")
        with self.assertRaises(SearchIndexCorruptedError):
            SqliteFtsSearchIndex(invalid).search(SearchQuery("ato"))
        empty = self.root / "empty.db"
        empty.touch()
        with self.assertRaises(SearchIndexCorruptedError):
            SqliteFtsSearchIndex(empty).search(SearchQuery("ato"))

    def test_connection_is_read_only(self):
        connection = self.index._open_read_only()
        try:
            with self.assertRaises(Exception):
                connection.execute("DELETE FROM documents")
        finally:
            connection.close()
