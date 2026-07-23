"""
Repositório de documentos do ProcDocOrganizer.
"""

from __future__ import annotations

import json
from pathlib import Path

from models import Document, Project


class DocumentRepository:
    """
    Gerencia os documentos de um projeto.
    """

    FILE_NAME = "documents.db.json"

    # ------------------------------------------------------------------

    def __init__(
        self,
        project: Project,
    ):
        self.project = project
        self.documents: list[Document] = []

    # ------------------------------------------------------------------

    @property
    def repository_file(self) -> Path:
        """
        Retorna o caminho do arquivo de persistência.
        """

        return self.project.project_path / self.FILE_NAME

    # ------------------------------------------------------------------

    def load(self) -> None:
        """
        Carrega os documentos do projeto.
        """

        if not self.repository_file.exists():
            self.documents = []
            return

        data = json.loads(
            self.repository_file.read_text(
                encoding="utf-8"
            )
        )

        if not isinstance(data, list):
            raise ValueError(
                "O arquivo de documentos possui formato inválido."
            )

        self.documents = [
            Document.from_dict(item)
            for item in data
        ]

    # ------------------------------------------------------------------

    def save(self) -> None:
        """
        Salva os documentos do projeto.
        """

        data = [
            document.to_dict()
            for document in self.documents
        ]

        temporary_file = self.repository_file.with_suffix(
            self.repository_file.suffix + ".tmp"
        )

        try:
            temporary_file.write_text(
                json.dumps(
                    data,
                    indent=4,
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            temporary_file.replace(self.repository_file)

        finally:
            temporary_file.unlink(missing_ok=True)

    # ------------------------------------------------------------------

    def list_documents(self) -> list[Document]:
        """
        Retorna uma cópia da lista de documentos.
        """

        return sorted(
            self.documents,
            key=lambda document: document.name.lower(),
        )

    # ------------------------------------------------------------------

    def add(
        self,
        document: Document,
    ) -> None:
        """
        Adiciona um documento ao repositório.
        """

        for existing in self.documents:
            if existing.relative_path == document.relative_path:
                raise ValueError(
                    f"O documento '{document.name}' já existe no projeto."
                )

        self.documents.append(document)

    # ------------------------------------------------------------------

    def update(self, document: Document) -> None:
        """
        Atualiza os metadados de um documento existente.
        """

        for index, existing in enumerate(self.documents):
            if existing.relative_path == document.relative_path:
                self.documents[index] = document
                return

        raise ValueError(
            f"O documento '{document.name}' não existe no projeto."
        )

    # ------------------------------------------------------------------

    def remove(
        self,
        document: Document,
    ) -> None:
        """
        Remove um documento do repositório.
        """

        self.documents.remove(document)

    # ------------------------------------------------------------------

    def clear(self) -> None:
        """
        Remove todos os documentos do repositório.
        """

        self.documents.clear()

    # ------------------------------------------------------------------

    def __len__(self) -> int:
        """
        Retorna a quantidade de documentos.
        """

        return len(self.documents)

    # ------------------------------------------------------------------

    def __iter__(self):
        """
        Permite iterar diretamente sobre o repositório.
        """

        return iter(self.documents)
