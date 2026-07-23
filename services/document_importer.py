"""
Serviço de importação de documentos.
"""

from __future__ import annotations

import hashlib
import shutil
from pathlib import Path

from models import Document, Project


class DocumentImporter:
    """
    Responsável por importar documentos para um projeto.
    """

    def __init__(self, project: Project):
        self.project = project

    # ------------------------------------------------------------------

    @property
    def documents_folder(self) -> Path:
        """
        Retorna a pasta de documentos do projeto.
        """

        return self.project.project_path / "documents"

    # ------------------------------------------------------------------

    def import_file(
        self,
        source_file: str | Path,
    ) -> Document:
        """
        Importa um único arquivo para o projeto.
        """

        documents = self.import_files([source_file])

        return documents[0]

    # ------------------------------------------------------------------

    def import_files(
        self,
        source_files: list[str | Path],
    ) -> list[Document]:
        """
        Importa vários arquivos para o projeto.

        A operação é atômica: todos os arquivos são importados
        ou nenhum é importado.
        """

        sources: list[Path] = []
        destination_names: set[str] = set()

        # --------------------------------------------------------------
        # Validação
        # --------------------------------------------------------------

        for source_file in source_files:

            source = Path(source_file)

            if not source.exists():
                raise FileNotFoundError(
                    f"Arquivo não encontrado:\n{source}"
                )

            if not source.is_file():
                raise ValueError(
                    f"O caminho '{source}' não é um arquivo."
                )

            destination = self.documents_folder / source.name

            destination_name = source.name.casefold()

            if destination_name in destination_names:
                raise FileExistsError(
                    f"O arquivo '{source.name}' foi selecionado mais de uma vez."
                )

            if destination.exists():
                raise FileExistsError(
                    f"O arquivo '{source.name}' já existe no projeto."
                )

            sources.append(source)
            destination_names.add(destination_name)

        # --------------------------------------------------------------
        # Importação
        # --------------------------------------------------------------

        documents: list[Document] = []
        copied_files: list[Path] = []

        try:

            self.documents_folder.mkdir(parents=True, exist_ok=True)

            for source in sources:

                destination = self.documents_folder / source.name

                shutil.copy2(source, destination)
                copied_files.append(destination)

                documents.append(
                    Document.create(
                        name=source.name,
                        relative_path=f"documents/{source.name}",
                        pages=self._get_page_count(destination),
                        sha256=self._calculate_sha256(destination),
                    )
                )

        except Exception:

            for copied_file in copied_files:
                copied_file.unlink(missing_ok=True)

            raise

        return documents

    # ------------------------------------------------------------------

    def remove_imported_files(
        self,
        documents: list[Document],
    ) -> None:
        """
        Remove os arquivos copiados durante uma importação cancelada.
        """

        for document in documents:
            document_file = self.project.project_path / document.relative_path
            document_file.unlink(missing_ok=True)

    # ------------------------------------------------------------------

    @staticmethod
    def _calculate_sha256(file_path: Path) -> str:
        digest = hashlib.sha256()

        with file_path.open("rb") as file:
            for chunk in iter(lambda: file.read(1024 * 1024), b""):
                digest.update(chunk)

        return digest.hexdigest()

    # ------------------------------------------------------------------

    @staticmethod
    def _get_page_count(file_path: Path) -> int:
        if file_path.suffix.lower() != ".pdf":
            return 0

        from PySide6.QtPdf import QPdfDocument

        document = QPdfDocument()
        error = document.load(str(file_path))

        if error != QPdfDocument.Error.None_:
            raise ValueError(
                f"Não foi possível ler o PDF '{file_path.name}'."
            )

        return document.pageCount()
