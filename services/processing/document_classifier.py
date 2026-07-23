"""
Classificador básico de documentos.
"""

from models import Document, DocumentType


class DocumentClassifier:
    """
    Define o ponto de extensão para classificação futura.
    """

    def classify(self, document: Document) -> DocumentType:
        """
        Retorna o tipo ainda não classificado do documento.
        """

        return DocumentType.UNKNOWN
