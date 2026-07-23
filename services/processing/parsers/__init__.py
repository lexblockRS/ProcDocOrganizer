"""Contratos e implementações de parsing documental."""

from .document_parser import DocumentParser
from .parser_errors import (
    DocumentParserError,
    InvalidDocumentSourceError,
    ParserRegistrationError,
    PDFParserError,
    UnsupportedDocumentFormatError,
)
from .parser_registry import ParserRegistry

__all__ = [
    "DocumentParser", "DocumentParserError", "InvalidDocumentSourceError",
    "ParserRegistrationError", "PDFParserError", "ParserRegistry",
    "UnsupportedDocumentFormatError",
]
