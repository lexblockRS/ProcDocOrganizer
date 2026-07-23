"""
Resultado de uma pesquisa textual em documentos processados.
"""

from dataclasses import dataclass

from .document import Document


@dataclass(frozen=True)
class SearchResult:
    """
    Representa uma ocorrência encontrada em uma página de documento.
    """

    document: Document
    page: int
    excerpt: str
