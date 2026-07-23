"""Composição explícita do conjunto padrão de parsers."""

from ..ocr import OCREngine, PageClassifier, TesseractOCREngine, TextMerger
from ..text_extractor import TextExtractor
from .parser_registry import ParserRegistry
from .pdf_parser import PDFParser


def create_default_parser_registry(
    text_extractor: TextExtractor | None = None,
    page_classifier: PageClassifier | None = None,
    ocr_engine: OCREngine | None = None,
    text_merger: TextMerger | None = None,
) -> ParserRegistry:
    """Cria um registro isolado contendo somente o parser PDF suportado."""

    parser = PDFParser(
        text_extractor or TextExtractor(),
        page_classifier or PageClassifier(),
        ocr_engine or TesseractOCREngine(),
        text_merger or TextMerger(),
    )
    return ParserRegistry((parser,))
