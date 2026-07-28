"""Armazenamento documental RSC exclusivamente em memória."""

from applications.rsc.domain import RscDocument


class RscDocumentService:
    def __init__(self) -> None:
        self._documents: dict[str, RscDocument] = {}

    def create_document(self, **values) -> RscDocument:
        document = RscDocument(**values)
        self.add_document(document)
        return document

    def add_document(self, document: RscDocument) -> None:
        if not isinstance(document, RscDocument):
            raise TypeError("document deve ser RscDocument.")
        if document.id in self._documents:
            raise ValueError(f"documento duplicado: {document.id}")
        self._documents[document.id] = document

    def get_document(self, document_id: str) -> RscDocument:
        try:
            return self._documents[document_id]
        except KeyError as exc:
            raise KeyError(f"documento inexistente: {document_id}") from exc

    def list_documents(self) -> tuple[RscDocument, ...]:
        return tuple(self._documents.values())

    def remove_document(self, document_id: str) -> RscDocument:
        try:
            return self._documents.pop(document_id)
        except KeyError as exc:
            raise KeyError(f"documento inexistente: {document_id}") from exc

    def replace_document(self, document: RscDocument) -> None:
        if not isinstance(document, RscDocument):
            raise TypeError("document deve ser RscDocument.")
        if document.id not in self._documents:
            raise KeyError(f"documento inexistente: {document.id}")
        self._documents[document.id] = document

    def clear(self) -> None:
        self._documents.clear()
