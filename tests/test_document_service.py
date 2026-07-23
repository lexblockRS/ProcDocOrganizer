from dataclasses import FrozenInstanceError
import unittest

from models import (
    Document, DocumentAvailability, DocumentDetails, DocumentPageSummary,
    DocumentSummary,
)
from services.document_service import (
    DocumentNotFoundError, DocumentPageNotFoundError, DocumentService,
)
from services.processing import ProcessingResult


SHA_A = "a" * 64
SHA_B = "b" * 64


class DocumentRepositoryDouble:
    def __init__(self, documents):
        self.documents = list(documents)

    def list_documents(self):
        return list(reversed(self.documents))


class ProcessingRepositoryDouble:
    def __init__(self, results=None, broken=()):
        self.results = dict(results or {})
        self.broken = set(broken)
        self.calls = []

    def load(self, sha):
        self.calls.append(sha)
        if sha in self.broken:
            raise ValueError("JSON corrompido")
        return self.results.get(sha)


def document(name, sha, path=None, pages=2, processing_status="pending"):
    return Document.create(
        name=name, relative_path=path or f"documents/{name}", pages=pages,
        sha256=sha, processing_status=processing_status,
    )


def result(sha=SHA_A, status="processed", pages=None):
    pages = pages if pages is not None else [
        {"page": 1, "text": "Texto integral\ncom quebra"},
        {"page": 3, "text": "Terceira página"},
    ]
    return ProcessingResult(
        document_sha256=sha, processed_at="2026-01-02T10:00:00",
        status=status, page_count=len(pages), pages=pages,
        metadata={"document_type": "portaria", "document_date": "2026-01-01"},
        text_source="mixed", ocr_used=True, error="falha parcial",
    )


class DocumentReadModelTests(unittest.TestCase):
    def test_models_are_immutable_and_metadata_is_defensive(self):
        summary = DocumentSummary(
            SHA_A, SHA_A, "Portaria", "documents/Meu  Documento.pdf",
            "portaria", None, 1, "processed",
            DocumentAvailability.AVAILABLE, True,
        )
        metadata = {"title": "Original"}
        details = DocumentDetails(
            summary, "2026-01-01", None, "native", False, None,
            metadata, 1, True,
        )
        metadata["title"] = "Alterado"
        self.assertEqual(details.metadata["title"], "Original")
        with self.assertRaises(TypeError):
            details.metadata["title"] = "x"
        with self.assertRaises(FrozenInstanceError):
            summary.name = "x"

    def test_page_preserves_number_unicode_spaces_and_full_text(self):
        text = "Comissão  Acadêmica\nTexto integral"
        page = DocumentPageSummary(SHA_A, SHA_A, 7, text, "ocr", len(text))
        self.assertEqual(page.page_number, 7)
        self.assertEqual(page.text, text)


class DocumentServiceTests(unittest.TestCase):
    def service(self, documents, results=None, broken=(), available=True):
        processing = ProcessingRepositoryDouble(results, broken)
        service = DocumentService(
            DocumentRepositoryDouble(documents), processing,
            availability_resolver=lambda _document: (
                DocumentAvailability.AVAILABLE if available
                else DocumentAvailability.MISSING
            ),
        )
        return service, processing

    def test_lists_every_imported_document_and_orders_deterministically(self):
        documents = (
            document("Árvore.pdf", SHA_B, "documents/Árvore.pdf"),
            document("ata.pdf", "", "documents/Meu  Documento.pdf"),
            document("Boletim.pdf", SHA_A),
        )
        service, _ = self.service(documents)
        catalog = service.list_documents()
        self.assertEqual(len(catalog), 3)
        self.assertEqual([item.name for item in catalog], ["ata.pdf", "Boletim.pdf", "Árvore.pdf"])
        self.assertEqual(catalog[0].identity, "documents/Meu  Documento.pdf")
        self.assertEqual(catalog[0].relative_path, "documents/Meu  Documento.pdf")

    def test_processed_result_enriches_status_pages_metadata_and_availability(self):
        item = document("doc.pdf", SHA_A, pages=9, processing_status="pending")
        service, _ = self.service((item,), {SHA_A: result()}, available=False)
        summary = service.list_documents()[0]
        details = service.get_document(SHA_A)
        self.assertEqual(summary.page_count, 2)
        self.assertEqual(summary.processing_status, "processed")
        self.assertEqual(summary.document_type, "portaria")
        self.assertEqual(summary.document_date, "2026-01-01")
        self.assertEqual(summary.availability, DocumentAvailability.MISSING)
        self.assertTrue(summary.has_processing_result)
        self.assertEqual(details.text_source, "mixed")
        self.assertTrue(details.ocr_used)
        self.assertEqual(details.processing_error, "falha parcial")

    def test_failed_processing_has_precedence(self):
        item = document("doc.pdf", SHA_A, processing_status="processed")
        service, _ = self.service((item,), {SHA_A: result(status="failed", pages=[])})
        self.assertEqual(service.list_documents()[0].processing_status, "failed")

    def test_absent_corrupt_mismatched_and_empty_sha_results_are_not_used(self):
        items = (
            document("ausente.pdf", SHA_A, pages=4, processing_status="pending"),
            document("corrompido.pdf", SHA_B, pages=5, processing_status="failed"),
            document("antigo.pdf", "", pages=6, processing_status="not_processed"),
        )
        service, processing = self.service(
            items, {SHA_A: result(sha=SHA_B)}, broken=(SHA_B,)
        )
        catalog = {item.name: item for item in service.list_documents()}
        self.assertFalse(catalog["ausente.pdf"].has_processing_result)
        self.assertEqual(catalog["ausente.pdf"].page_count, 4)
        self.assertEqual(catalog["corrompido.pdf"].processing_status, "failed")
        self.assertNotIn("", processing.calls)

    def test_get_document_and_missing_document(self):
        service, _ = self.service((document("doc.pdf", SHA_A),))
        self.assertEqual(service.get_document(SHA_A).summary.name, "doc.pdf")
        with self.assertRaises(DocumentNotFoundError):
            service.get_document("missing")

    def test_pages_load_only_on_demand_and_preserve_real_numbers_and_text(self):
        service, processing = self.service(
            (document("doc.pdf", SHA_A),), {SHA_A: result()}
        )
        self.assertEqual(processing.calls, [])
        pages = service.list_pages(SHA_A)
        self.assertEqual([page.page_number for page in pages], [1, 3])
        self.assertEqual(pages[0].text, "Texto integral\ncom quebra")
        self.assertEqual(pages[0].character_count, len(pages[0].text))
        self.assertEqual(service.get_page(SHA_A, 3).text, "Terceira página")
        with self.assertRaises(DocumentPageNotFoundError):
            service.get_page(SHA_A, 2)

    def test_document_without_processing_has_no_pages(self):
        service, _ = self.service((document("doc.pdf", SHA_A),))
        self.assertEqual(service.list_pages(SHA_A), ())


if __name__ == "__main__":
    unittest.main()
