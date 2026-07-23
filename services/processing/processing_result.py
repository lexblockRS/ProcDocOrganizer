"""
Representação canônica do processamento de qualquer documento suportado.
"""

from dataclasses import asdict, dataclass, field
from datetime import datetime


@dataclass
class ProcessingResult:
    """
    Contrato persistido consumido por indexação, pesquisa e evidências.

    ``pages`` preserva o contrato atual para formatos paginados. Um futuro
    formato não paginado poderá representá-lo como uma unidade lógica, sem
    remover ou reinterpretar campos existentes.
    """

    document_sha256: str
    processed_at: str
    status: str
    page_count: int = 0
    pages: list[dict] = field(default_factory=list)
    error: str | None = None
    metadata: dict = field(default_factory=dict)
    metadata_extractor_version: int | None = None
    text_source: str = "native"
    ocr_used: bool = False

    # ------------------------------------------------------------------

    @staticmethod
    def now() -> str:
        """
        Retorna a data/hora atual em formato ISO 8601.
        """

        return datetime.now().isoformat(timespec="seconds")

    # ------------------------------------------------------------------

    def to_dict(self) -> dict:
        """
        Converte o resultado para persistência.
        """

        return asdict(self)

    # ------------------------------------------------------------------

    @classmethod
    def from_dict(cls, data: dict) -> "ProcessingResult":
        """
        Cria um resultado a partir de dados persistidos.
        """

        return cls(**data)

    # ------------------------------------------------------------------

    def is_valid_for(self, document_sha256: str) -> bool:
        """
        Informa se o resultado pode ser reutilizado para o documento.
        """

        return (
            self.status == "processed"
            and self.document_sha256 == document_sha256
            and self.has_searchable_text()
        )

    # ------------------------------------------------------------------

    def has_searchable_text(self) -> bool:
        """
        Informa se ao menos uma página possui texto nativo pesquisável.
        """

        if not isinstance(self.pages, list):
            return False

        return any(
            isinstance(page, dict)
            and isinstance(page.get("text"), str)
            and page["text"].strip()
            for page in self.pages
        )
