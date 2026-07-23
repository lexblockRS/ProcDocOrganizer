"""
Tipos de documento reconhecidos pelo ProcDocOrganizer.
"""

from enum import Enum


class DocumentType(str, Enum):
    """
    Representa o tipo conhecido de um documento.
    """

    UNKNOWN = "unknown"
    PORTARIA = "portaria"
    RESOLUCAO = "resolucao"
    OFICIO = "oficio"
    MEMORANDO = "memorando"
    DECLARACAO = "declaracao"
    CERTIFICADO = "certificado"
    EDITAL = "edital"
