"""Atualização transacional dos metadados documentais já consolidados."""

from models import DocumentType


class DocumentMetadataError(ValueError):
    """Falha de validação ou localização durante atualização editorial."""


class DocumentMetadataService:
    """Edita somente campos já pertencentes a Document e ao SQLite."""

    def __init__(self, document_repository) -> None:
        self.document_repository = document_repository

    def update_document_type(
        self,
        document_identity: str,
        document_type: str,
    ):
        if not isinstance(document_identity, str) or not document_identity:
            raise DocumentMetadataError(
                "A identidade do documento é obrigatória."
            )
        try:
            normalized_type = DocumentType(document_type).value
        except (TypeError, ValueError) as exc:
            raise DocumentMetadataError(
                "O tipo documental informado não é válido."
            ) from exc
        document = self.document_repository.find_by_hash(document_identity)
        if document is None:
            raise DocumentMetadataError(
                "O documento selecionado não foi localizado."
            )
        document.document_type = normalized_type
        self.document_repository.update(document)
        return document
