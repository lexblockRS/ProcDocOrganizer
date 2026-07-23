"""Erros neutros da camada de parsing documental."""


class DocumentParserError(Exception):
    """Erro ocorrido durante a interpretação de um documento."""


class UnsupportedDocumentFormatError(DocumentParserError):
    """Nenhum parser registrado reconhece o documento."""


class ParserRegistrationError(DocumentParserError):
    """O registro de um parser é inválido ou duplicado."""


class InvalidDocumentSourceError(DocumentParserError):
    """A origem não existe ou não é um arquivo regular."""


class PDFParserError(DocumentParserError):
    """Falha encapsulada do pipeline específico de PDF."""
