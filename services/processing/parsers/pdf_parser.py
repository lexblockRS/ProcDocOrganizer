"""Parser do pipeline PDF homologado, incluindo OCR seletivo."""

from pathlib import Path
from typing import Any, Mapping

from ..ocr import OCREngine, OCRResult, PageClassifier, TextMerger
from ..processing_result import ProcessingResult
from ..text_extractor import TextExtractor
from .document_parser import DocumentParser
from .parser_errors import PDFParserError


class PDFParser(DocumentParser):
    parser_id = "pdf"

    def __init__(
        self,
        text_extractor: TextExtractor,
        page_classifier: PageClassifier,
        ocr_engine: OCREngine,
        text_merger: TextMerger,
    ):
        self.text_extractor = text_extractor
        self.page_classifier = page_classifier
        self.ocr_engine = ocr_engine
        self.text_merger = text_merger

    def supports(self, source: Path) -> bool:
        if source.suffix.lower() == ".pdf":
            return True
        try:
            with source.open("rb") as stream:
                return stream.read(5) == b"%PDF-"
        except OSError:
            return False

    def parse(
        self,
        source: Path,
        context: Mapping[str, Any] | None = None,
    ) -> ProcessingResult:
        document_sha256 = str((context or {}).get("document_sha256", ""))
        try:
            native_pages = self.text_extractor.extract(source)
            ocr_results = self._run_required_ocr(source, native_pages)
            merged = self.text_merger.merge(native_pages, ocr_results)
            has_text = any(page["text"].strip() for page in merged.pages)
            status = "processed" if has_text else "failed"
            error = "; ".join(merged.ocr_errors) or None
            if not has_text and error is None:
                error = "Nenhum texto pesquisável foi obtido pelo OCR."
            return ProcessingResult(
                document_sha256=document_sha256,
                processed_at=ProcessingResult.now(),
                status=status,
                page_count=len(native_pages),
                pages=merged.pages,
                error=error,
                text_source=merged.text_source,
                ocr_used=merged.ocr_used,
            )
        except PDFParserError:
            raise
        except Exception as exc:
            raise PDFParserError(
                f"Falha ao processar o PDF '{source.name}': {exc}"
            ) from exc

    def _run_required_ocr(
        self, source: Path, native_pages: list[dict]
    ) -> dict[int, OCRResult]:
        results = {}
        for page in native_pages:
            if not self.page_classifier.requires_ocr(page["text"]):
                continue
            page_number = page["page"]
            try:
                result = self.ocr_engine.recognize_page(source, page_number)
                if not isinstance(result, OCRResult):
                    raise TypeError("O motor OCR retornou um resultado inválido.")
            except Exception as exc:
                result = OCRResult(
                    page_number=page_number, success=False, error=str(exc)
                )
            results[page_number] = result
        return results
