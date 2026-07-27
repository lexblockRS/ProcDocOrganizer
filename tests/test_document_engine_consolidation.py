import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import Mock, patch

from core.project_manager import ProjectManager
from models import CreateEvidenceRequest
from services import (
    DocumentImportService,
    DocumentRepository,
    EvidenceService,
    SearchDocumentSourceResolver,
    SQLiteEvidenceRepository,
)
from services.indexing import DocumentIndexer
from services.processing import DocumentProcessor, ProcessingResult
from services.processing.ocr import TesseractOCREngine
from services.processing.parsers import DocumentParser, ParserRegistry
from services.search import SearchQuery, SearchService, SqliteFtsSearchIndex


class TextParser(DocumentParser):
    parser_id = "audit-text"

    def supports(self, source):
        return source.suffix.lower() == ".pdf"

    def parse(self, source, context=None):
        return ProcessingResult(
            document_sha256=context["document_sha256"],
            processed_at="2026-07-27T12:00:00",
            status="processed",
            page_count=1,
            pages=[{
                "page": 1,
                "text": "atividade documental pesquisável consolidada",
            }],
        )


class FailingIndexer:
    def __init__(self):
        self.calls = 0

    def index_processing_result(self, *_args, **_kwargs):
        self.calls += 1
        raise RuntimeError("índice indisponível")


class DocumentEngineConsolidationTests(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = TemporaryDirectory()
        self.addCleanup(self.temporary_directory.cleanup)
        self.root = Path(self.temporary_directory.name)
        self.project = ProjectManager().create_project(
            "Motor", self.root
        )
        self.repository = DocumentRepository(self.project)
        self.repository.load()
        self.importer = DocumentImportService(
            self.project, self.repository
        )
        self.source = self.root / "documento.pdf"
        self.source.write_bytes(b"%PDF-conteudo-controlado")

    def processor(self, indexer):
        return DocumentProcessor(
            parser_registry=ParserRegistry((TextParser(),)),
            document_indexer=indexer,
        )

    def test_complete_flow_and_historical_evidence_after_removal(self):
        imported = self.importer.import_file(self.source).document
        database_path = self.project.project_path / self.project.database
        indexer = DocumentIndexer(database_path)

        result = self.processor(indexer).process(
            self.project, imported
        )

        self.assertEqual(result.status, "processed")
        processing_file = (
            self.project.project_path
            / "processing"
            / f"{imported.sha256}.json"
        )
        self.assertTrue(processing_file.is_file())
        search = SearchService(SqliteFtsSearchIndex(database_path))
        page = search.search(SearchQuery("consolidada"))
        self.assertEqual(len(page.hits), 1)
        self.assertEqual(
            page.hits[0].document_identity, imported.sha256
        )

        evidence_service = EvidenceService(
            SQLiteEvidenceRepository(self.project),
            SearchDocumentSourceResolver(self.project),
            id_factory=lambda: "11111111-1111-4111-8111-111111111111",
            now_factory=lambda: "2026-07-27T12:01:00",
        )
        evidence = evidence_service.create(CreateEvidenceRequest(
            document_identity=imported.sha256,
            page_number=1,
            title="Atividade comprovada",
            source_snippet=page.hits[0].snippet,
        ))

        self.assertTrue(self.importer.remove(imported.id))
        self.assertFalse(processing_file.exists())
        self.assertEqual(
            search.search(SearchQuery("consolidada")).hits, ()
        )
        self.assertEqual(evidence_service.get(evidence.id), evidence)
        self.assertFalse(evidence_service.is_source_available(evidence))

    def test_reopening_preserves_catalog_and_search_projection(self):
        imported = self.importer.import_file(self.source).document
        database_path = self.project.project_path / self.project.database
        self.processor(DocumentIndexer(database_path)).process(
            self.project, imported
        )

        reopened_repository = DocumentRepository(self.project)
        reopened_repository.load()
        reopened = reopened_repository.find_by_hash(imported.sha256)

        self.assertIsNotNone(reopened)
        self.assertEqual(
            SearchService(SqliteFtsSearchIndex(database_path))
            .search(SearchQuery("pesquisável"))
            .hits[0]
            .document_identity,
            imported.sha256,
        )

    def test_index_failure_invalidates_result_and_records_diagnostic(self):
        imported = self.importer.import_file(self.source).document
        indexer = FailingIndexer()

        result = self.processor(indexer).process(
            self.project, imported
        )

        self.assertEqual(result.status, "failed")
        self.assertEqual(indexer.calls, 2)
        self.assertIn("índice indisponível", result.error)
        stored = json.loads(
            (
                self.project.project_path
                / "processing"
                / f"{imported.sha256}.json"
            ).read_text(encoding="utf-8")
        )
        self.assertEqual(stored["status"], "failed")

    def test_duplicate_does_not_create_second_catalog_or_file(self):
        first = self.importer.import_file(self.source)
        duplicate = self.root / "copia.pdf"
        duplicate.write_bytes(self.source.read_bytes())

        second = self.importer.import_file(duplicate)

        self.assertTrue(second.is_duplicate)
        self.assertEqual(first.document.id, second.document.id)
        self.assertEqual(len(self.repository.list_all()), 1)

    def test_remove_restores_files_when_catalog_transaction_fails(self):
        imported = self.importer.import_file(self.source).document
        stored_file = self.project.project_path / imported.relative_path
        processing_file = (
            self.project.project_path
            / "processing"
            / f"{imported.sha256}.json"
        )
        processing_file.parent.mkdir()
        processing_file.write_text("{}", encoding="utf-8")
        repository = Mock()
        repository.find_by_id.return_value = imported
        repository.delete.side_effect = RuntimeError("falha transacional")
        service = DocumentImportService(self.project, repository)

        with self.assertRaisesRegex(RuntimeError, "falha transacional"):
            service.remove(imported.id)

        self.assertTrue(stored_file.is_file())
        self.assertTrue(processing_file.is_file())
        self.assertEqual(
            tuple(self.project.project_path.rglob("*.pending-delete")), ()
        )

    @patch("services.processing.ocr.ocr_engine.subprocess.run")
    @patch("services.processing.ocr.ocr_engine.shutil.which")
    def test_ocr_diagnostic_requires_configured_language(
        self, which, run
    ):
        which.return_value = "C:/Tesseract/tesseract.exe"
        run.return_value = Mock(
            returncode=0,
            stdout="List of available languages (1):\neng\n",
            stderr="",
        )

        diagnostic = TesseractOCREngine().diagnose()

        self.assertFalse(diagnostic.available)
        self.assertEqual(diagnostic.language, "por")
        self.assertIn("'por' não está instalado", diagnostic.message)


if __name__ == "__main__":
    unittest.main()
