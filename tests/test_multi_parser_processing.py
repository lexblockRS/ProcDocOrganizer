import hashlib
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from models import Document, Project
from services.processing import DocumentProcessor, ProcessingResult
from services.processing.ocr import OCRResult, PageClassifier, TextMerger
from services.processing.parsers import (
    DocumentParser,
    InvalidDocumentSourceError,
    ParserRegistrationError,
    ParserRegistry,
    PDFParserError,
    UnsupportedDocumentFormatError,
)
from services.processing.parsers.pdf_parser import PDFParser


class FakeParser(DocumentParser):
    def __init__(self, parser_id="fake", suffix=".fake", text="texto fictício"):
        self.parser_id = parser_id
        self.suffix = suffix
        self.text = text
        self.calls = []

    def supports(self, source):
        return source.suffix.lower() == self.suffix

    def parse(self, source, context=None):
        self.calls.append(source)
        return ProcessingResult(
            document_sha256=context["document_sha256"],
            processed_at="2026-01-01T00:00:00",
            status="processed",
            page_count=1,
            pages=[{"page": 1, "text": self.text}],
        )


class FakeTextExtractor:
    def __init__(self, pages=None, error=None):
        self.pages = pages or []
        self.error = error

    def extract(self, source):
        if self.error:
            raise self.error
        return [dict(page) for page in self.pages]


class FakeOCREngine:
    def __init__(self, results=None):
        self.results = results or {}

    def recognize_page(self, source, page_number):
        return self.results[page_number]


class MultiParserTests(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = TemporaryDirectory()
        self.root = Path(self.temporary_directory.name)

    def tearDown(self):
        self.temporary_directory.cleanup()

    def touch(self, name, content=b"content"):
        path = self.root / name
        path.write_bytes(content)
        return path

    def test_register_get_and_list_are_deterministic(self):
        first = FakeParser("first")
        second = FakeParser("second")
        registry = ParserRegistry((first, second))
        self.assertIs(registry.get_by_id("first"), first)
        self.assertEqual(registry.list_parser_ids(), ("first", "second"))

    def test_duplicate_and_invalid_parser_ids_are_rejected(self):
        registry = ParserRegistry((FakeParser("same"),))
        with self.assertRaises(ParserRegistrationError):
            registry.register(FakeParser("same"))
        with self.assertRaises(ParserRegistrationError):
            registry.register(FakeParser(""))

    def test_pdf_resolution_is_case_insensitive(self):
        parser = PDFParser(FakeTextExtractor(), PageClassifier(), FakeOCREngine(), TextMerger())
        registry = ParserRegistry((parser,))
        self.assertIs(registry.resolve(self.touch("lower.pdf")), parser)
        self.assertIs(registry.resolve(self.touch("upper.PDF")), parser)

    def test_valid_signature_allows_pdf_without_extension(self):
        parser = PDFParser(FakeTextExtractor(), PageClassifier(), FakeOCREngine(), TextMerger())
        self.assertTrue(parser.supports(self.touch("document", b"%PDF-1.7")))

    def test_pdf_extension_preserves_legacy_acceptance_before_deep_validation(self):
        parser = PDFParser(FakeTextExtractor(), PageClassifier(), FakeOCREngine(), TextMerger())
        self.assertTrue(parser.supports(self.touch("legacy.pdf", b"not a signature")))

    def test_unsupported_xml_and_other_file_are_rejected(self):
        registry = ParserRegistry((FakeParser(),))
        for name in ("curriculo.xml", "document.docx"):
            with self.subTest(name=name), self.assertRaises(UnsupportedDocumentFormatError):
                registry.resolve(self.touch(name))

    def test_missing_file_and_directory_are_invalid_sources(self):
        registry = ParserRegistry((FakeParser(),))
        with self.assertRaises(InvalidDocumentSourceError):
            registry.resolve(self.root / "missing.pdf")
        directory = self.root / "folder"
        directory.mkdir()
        with self.assertRaises(InvalidDocumentSourceError):
            registry.resolve(directory)
        self.assertFalse(registry.supports(directory))

    def test_first_supporting_parser_wins_deterministically(self):
        source = self.touch("sample.fake")
        first = FakeParser("first")
        second = FakeParser("second")
        self.assertIs(ParserRegistry((first, second)).resolve(source), first)

    def test_fake_parser_extends_processor_only_by_injection(self):
        project = Project.create("Multi", self.root / "Multi.pdop")
        documents = project.project_path / "documents"
        documents.mkdir(parents=True)
        source = documents / "note.fake"
        source.write_text("source", encoding="utf-8")
        sha256 = hashlib.sha256(source.read_bytes()).hexdigest()
        document = Document.create("note.fake", "documents/note.fake", 0, sha256)
        parser = FakeParser()

        result = DocumentProcessor(
            parser_registry=ParserRegistry((parser,))
        ).process(project, document)

        self.assertEqual(parser.calls, [source])
        self.assertEqual(result.pages[0]["text"], "texto fictício")
        stored = json.loads(
            (project.project_path / "processing" / f"{sha256}.json").read_text(encoding="utf-8")
        )
        self.assertEqual(stored, result.to_dict())

    def test_pdf_parser_wraps_extractor_error_and_preserves_cause(self):
        parser = PDFParser(
            FakeTextExtractor(error=ValueError("internal library detail")),
            PageClassifier(), FakeOCREngine(), TextMerger(),
        )
        with self.assertRaises(PDFParserError) as raised:
            parser.parse(self.touch("broken.pdf"), {"document_sha256": "a" * 64})
        self.assertIsInstance(raised.exception.__cause__, ValueError)

    def test_pdf_characterization_preserves_native_mixed_and_ocr_contract(self):
        cases = (
            ([{"page": 1, "text": "Texto nativo longo e suficiente"}], {}, "native", False),
            ([{"page": 1, "text": ""}], {1: OCRResult(1, "Texto OCR suficiente")}, "ocr", True),
            ([{"page": 1, "text": "Texto nativo longo e suficiente"}, {"page": 2, "text": ""}],
             {2: OCRResult(2, "Texto OCR suficiente")}, "mixed", True),
        )
        for pages, ocr, source_kind, used in cases:
            with self.subTest(source_kind=source_kind):
                parser = PDFParser(
                    FakeTextExtractor(pages), PageClassifier(),
                    FakeOCREngine(ocr), TextMerger(),
                )
                result = parser.parse(
                    self.touch(f"{source_kind}.pdf"),
                    {"document_sha256": "a" * 64},
                )
                expected_merged = TextMerger().merge(pages, ocr)
                self.assertEqual(result.pages, expected_merged.pages)
                self.assertEqual(result.page_count, len(pages))
                self.assertEqual(result.text_source, source_kind)
                self.assertEqual(result.ocr_used, used)
                self.assertEqual(result.status, "processed")


if __name__ == "__main__":
    unittest.main()
