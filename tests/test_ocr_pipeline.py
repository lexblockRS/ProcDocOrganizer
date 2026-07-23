import hashlib
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from models import Document, Project
from services.indexing import DocumentIndexer
from services.processing.document_processor import DocumentProcessor
from services.processing.ocr import (
    OCREngine,
    OCRResult,
    PageClassifier,
    TesseractOCREngine,
    TextThresholdStrategy,
)
from services.processing.processing_result import ProcessingResult


class FakeTextExtractor:
    def __init__(self, pages):
        self.pages = pages

    def extract(self, file_path):
        return [dict(page) for page in self.pages]


class FakeOCREngine(OCREngine):
    def __init__(self, results=None, raised_pages=None):
        self.results = results or {}
        self.raised_pages = set(raised_pages or ())
        self.calls = []

    def recognize_page(self, pdf_path, page_number):
        self.calls.append(page_number)
        if page_number in self.raised_pages:
            raise RuntimeError("falha simulada do motor")
        return self.results.get(
            page_number,
            OCRResult(page_number, "", False, "OCR sem resultado"),
        )


class OCRPipelineTests(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = TemporaryDirectory()
        self.root = Path(self.temporary_directory.name)
        self.project = Project.create("OCR", self.root / "OCR.pdop")
        documents = self.project.project_path / "documents"
        documents.mkdir(parents=True)
        self.pdf_path = documents / "documento.pdf"
        self.pdf_bytes = b"conteudo deterministico do PDF"
        self.pdf_path.write_bytes(self.pdf_bytes)
        self.sha256 = hashlib.sha256(self.pdf_bytes).hexdigest()
        self.document = Document.create(
            name="documento.pdf",
            relative_path="documents/documento.pdf",
            pages=0,
            sha256=self.sha256,
        )

    def tearDown(self):
        self.temporary_directory.cleanup()

    def processor(self, pages, engine):
        return DocumentProcessor(
            text_extractor=FakeTextExtractor(pages),
            page_classifier=PageClassifier(
                TextThresholdStrategy(minimum_characters=10, minimum_words=2)
            ),
            ocr_engine=engine,
        )

    def test_page_classifier_uses_replaceable_threshold_strategy(self):
        classifier = PageClassifier(
            TextThresholdStrategy(minimum_characters=10, minimum_words=2)
        )

        self.assertFalse(classifier.requires_ocr("Texto nativo suficiente"))
        self.assertTrue(classifier.requires_ocr("curto"))

    def test_textual_pdf_does_not_execute_ocr(self):
        engine = FakeOCREngine()
        result = self.processor(
            [{"page": 1, "text": "Texto nativo suficientemente completo"}],
            engine,
        ).process(self.project, self.document)

        self.assertEqual(result.status, "processed")
        self.assertEqual(result.text_source, "native")
        self.assertFalse(result.ocr_used)
        self.assertEqual(engine.calls, [])

    def test_fully_scanned_pdf_uses_ocr_on_every_page(self):
        engine = FakeOCREngine({
            1: OCRResult(1, "Primeira página reconhecida"),
            2: OCRResult(2, "Segunda página reconhecida"),
        })
        result = self.processor(
            [{"page": 1, "text": ""}, {"page": 2, "text": "  "}],
            engine,
        ).process(self.project, self.document)

        self.assertEqual(result.status, "processed")
        self.assertEqual(result.text_source, "ocr")
        self.assertTrue(result.ocr_used)
        self.assertEqual(engine.calls, [1, 2])
        self.assertEqual(result.page_count, 2)
        self.assertEqual(result.document_sha256, self.sha256)

    def test_mixed_pdf_runs_ocr_only_on_required_page(self):
        engine = FakeOCREngine({2: OCRResult(2, "Texto obtido por OCR")})
        result = self.processor(
            [
                {"page": 1, "text": "Texto nativo suficientemente completo"},
                {"page": 2, "text": ""},
            ],
            engine,
        ).process(self.project, self.document)

        self.assertEqual(engine.calls, [2])
        self.assertEqual(result.text_source, "mixed")
        self.assertEqual(
            [page["text"] for page in result.pages],
            ["Texto nativo suficientemente completo", "Texto obtido por OCR"],
        )

    def test_total_ocr_failure_produces_failed_without_ocr_required(self):
        engine = FakeOCREngine(raised_pages={1})
        result = self.processor(
            [{"page": 1, "text": ""}], engine
        ).process(self.project, self.document)

        self.assertEqual(result.status, "failed")
        self.assertNotEqual(result.status, "ocr_required")
        self.assertEqual(result.page_count, 1)
        self.assertEqual(result.document_sha256, self.sha256)
        self.assertEqual(result.text_source, "ocr")
        self.assertTrue(result.ocr_used)
        self.assertIn("falha simulada", result.error)

    def test_partial_ocr_preserves_successful_pages_and_reports_error(self):
        engine = FakeOCREngine(
            {1: OCRResult(1, "Página reconhecida com sucesso")},
            raised_pages={2},
        )
        result = self.processor(
            [{"page": 1, "text": ""}, {"page": 2, "text": ""}],
            engine,
        ).process(self.project, self.document)

        self.assertEqual(result.status, "processed")
        self.assertEqual(result.text_source, "ocr")
        self.assertEqual(result.pages[0]["text"], "Página reconhecida com sucesso")
        self.assertEqual(result.pages[1]["text"], "")
        self.assertIn("Página 2", result.error)

    def test_metadata_is_extracted_from_ocr_text(self):
        engine = FakeOCREngine({
            1: OCRResult(
                1,
                "PORTARIA Nº 42/2025\n"
                "Gabinete da Reitoria, 15 de março de 2025.",
            )
        })
        result = self.processor(
            [{"page": 1, "text": ""}], engine
        ).process(self.project, self.document)

        self.assertEqual(result.metadata["document_type"], "portaria")
        self.assertEqual(result.metadata["document_number"], "42/2025")
        self.assertEqual(result.metadata["document_date"], "2025-03-15")

    def test_ocr_text_is_searchable_in_existing_fts_index(self):
        engine = FakeOCREngine({
            1: OCRResult(1, "Servidor digitalizado pesquisável")
        })
        result = self.processor(
            [{"page": 1, "text": ""}], engine
        ).process(self.project, self.document)
        json_path = (
            self.project.project_path / "processing" / f"{self.sha256}.json"
        )
        database_path = self.project.project_path / "database.db"

        indexing = DocumentIndexer(database_path).index_processing_result(
            json_path
        )
        self.assertEqual(indexing.status, "indexed")
        import sqlite3
        connection = sqlite3.connect(database_path)
        try:
            count = connection.execute(
                "SELECT COUNT(*) FROM document_pages_fts "
                "WHERE document_pages_fts MATCH ?",
                ("digitalizado",),
            ).fetchone()[0]
        finally:
            connection.close()
        self.assertEqual(count, 1)
        self.assertEqual(result.text_source, "ocr")

    def test_json_adds_only_backward_compatible_ocr_fields(self):
        engine = FakeOCREngine({1: OCRResult(1, "Texto reconhecido pelo OCR")})
        self.processor(
            [{"page": 1, "text": ""}], engine
        ).process(self.project, self.document)
        json_path = (
            self.project.project_path / "processing" / f"{self.sha256}.json"
        )
        data = json.loads(json_path.read_text(encoding="utf-8"))

        self.assertEqual(data["text_source"], "ocr")
        self.assertTrue(data["ocr_used"])
        for field in (
            "document_sha256", "processed_at", "status", "page_count",
            "pages", "error", "metadata", "metadata_extractor_version",
        ):
            self.assertIn(field, data)

    def test_old_json_without_ocr_fields_remains_compatible(self):
        result = ProcessingResult.from_dict({
            "document_sha256": self.sha256,
            "processed_at": "2025-01-01T00:00:00",
            "status": "ocr_required",
            "page_count": 3,
            "pages": [],
        })

        self.assertEqual(result.text_source, "native")
        self.assertFalse(result.ocr_used)
        self.assertFalse(result.is_valid_for(self.sha256))

    def test_missing_tesseract_is_reported_without_leaking_exception(self):
        engine = TesseractOCREngine(
            executable="tesseract-certainly-not-installed"
        )
        result = engine.recognize_page(self.pdf_path, 1)

        self.assertFalse(result.success)
        self.assertIn("não encontrado", result.error)


if __name__ == "__main__":
    unittest.main()
