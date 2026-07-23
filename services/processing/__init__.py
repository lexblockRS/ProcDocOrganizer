"""
Infraestrutura de processamento de documentos.
"""

from .document_classifier import DocumentClassifier
from .document_metadata_extractor import DocumentMetadataExtractor
from .document_processor import DocumentProcessor
from .processing_result import ProcessingResult
from .processing_repository import ProcessingRepository
from .text_extractor import TextExtractor
from .parsers import (
    DocumentParser,
    ParserRegistry,
)
from .parsers.default_registry import create_default_parser_registry
from .parsers.pdf_parser import PDFParser

__all__ = [
    "DocumentClassifier",
    "DocumentMetadataExtractor",
    "DocumentProcessor",
    "ProcessingResult",
    "ProcessingRepository",
    "TextExtractor",
    "DocumentParser",
    "ParserRegistry",
    "PDFParser",
    "create_default_parser_registry",
]
