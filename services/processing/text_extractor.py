"""
Ponto de extensão para extração futura de texto.
"""

from pathlib import Path

from PySide6.QtPdf import QPdfDocument


class TextExtractor:
    """
    Extrai o texto nativo disponível em cada página de um PDF.
    """

    def extract(self, file_path: Path) -> list[dict]:
        """
        Retorna o texto de cada página sem usar OCR.
        """

        document = QPdfDocument()
        error = document.load(str(file_path))

        if error != QPdfDocument.Error.None_:
            raise ValueError(
                f"Não foi possível ler o PDF '{file_path.name}'."
            )

        pages = []

        for page_index in range(document.pageCount()):
            selection = document.getAllText(page_index)

            pages.append(
                {
                    "page": page_index + 1,
                    "text": selection.text(),
                }
            )

        return pages
