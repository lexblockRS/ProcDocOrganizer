"""Registro determinístico e independente de tecnologia de parsers."""

from pathlib import Path

from .document_parser import DocumentParser
from .parser_errors import (
    InvalidDocumentSourceError,
    ParserRegistrationError,
    UnsupportedDocumentFormatError,
)


class ParserRegistry:
    """Mantém parsers na ordem de registro e resolve o primeiro compatível."""

    def __init__(self, parsers=()):
        self._parsers: list[DocumentParser] = []
        self._by_id: dict[str, DocumentParser] = {}
        for parser in parsers:
            self.register(parser)

    def register(self, parser: DocumentParser) -> None:
        parser_id = getattr(parser, "parser_id", None)
        if not isinstance(parser_id, str) or not parser_id.strip():
            raise ParserRegistrationError("parser_id deve ser uma string não vazia.")
        if parser_id in self._by_id:
            raise ParserRegistrationError(
                f"Já existe um parser registrado com o id '{parser_id}'."
            )
        self._parsers.append(parser)
        self._by_id[parser_id] = parser

    def get_by_id(self, parser_id: str) -> DocumentParser | None:
        return self._by_id.get(parser_id)

    def list_parser_ids(self) -> tuple[str, ...]:
        return tuple(self._by_id)

    def supports(self, source_path: str | Path) -> bool:
        try:
            self.resolve(source_path)
        except (InvalidDocumentSourceError, UnsupportedDocumentFormatError):
            return False
        return True

    def resolve(self, source_path: str | Path) -> DocumentParser:
        source = Path(source_path)
        if not source.exists():
            raise InvalidDocumentSourceError(f"O arquivo '{source}' não existe.")
        if not source.is_file():
            raise InvalidDocumentSourceError(f"A origem '{source}' não é um arquivo.")
        for parser in self._parsers:
            if parser.supports(source):
                return parser
        raise UnsupportedDocumentFormatError(
            f"Formato de documento não suportado: '{source.name}'."
        )
