"""Contratos neutros de navegação entre módulos."""

from dataclasses import dataclass


@dataclass(frozen=True)
class DocumentNavigationRequest:
    """Solicita a abertura lógica de um documento e de uma página opcional."""

    document_identity: str
    page_number: int | None = None

    def __post_init__(self) -> None:
        if (
            not isinstance(self.document_identity, str)
            or not self.document_identity.strip()
        ):
            raise ValueError(
                "document_identity deve ser um texto não vazio."
            )
        if self.page_number is not None and (
            isinstance(self.page_number, bool)
            or not isinstance(self.page_number, int)
            or self.page_number < 1
        ):
            raise ValueError(
                "page_number deve ser None ou um inteiro a partir de 1."
            )
        object.__setattr__(
            self, "document_identity", self.document_identity.strip()
        )
