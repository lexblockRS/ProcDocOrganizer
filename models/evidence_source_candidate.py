"""Dados neutros transferidos da pesquisa para a criação de evidência."""

from dataclasses import dataclass
from pathlib import PurePath
import re
import unicodedata


@dataclass(frozen=True, init=False)
class EvidenceSourceCandidate:
    document_identity: str
    page_number: int | None
    source_snippet: str = ""
    document_name: str | None = None
    document_path: str | None = None
    document_type: str | None = None
    search_term: str | None = None
    suggested_title: str | None = None

    MAX_TITLE_LENGTH = 300

    def __init__(
        self,
        document_identity: str | None = None,
        page_number: int | None = None,
        source_snippet: str = "",
        document_name: str | None = None,
        document_path: str | None = None,
        document_type: str | None = None,
        search_term: str | None = None,
        suggested_title: str | None = None,
        **legacy,
    ) -> None:
        legacy_identity = legacy.pop("document_sha256", None)
        if legacy:
            raise TypeError(f"Argumentos desconhecidos: {', '.join(legacy)}")
        identity = (
            document_identity
            if document_identity is not None
            else legacy_identity
        )
        for field, value in (
            ("document_identity", identity),
            ("page_number", page_number),
            ("source_snippet", source_snippet),
            ("document_name", document_name),
            ("document_path", document_path),
            ("document_type", document_type),
            ("search_term", search_term),
            ("suggested_title", suggested_title),
        ):
            object.__setattr__(self, field, value)
        self.__post_init__()

    def __post_init__(self) -> None:
        if (
            not isinstance(self.document_identity, str)
            or not self.document_identity.strip()
        ):
            raise ValueError("O resultado não possui identidade documental válida.")
        if self.page_number is not None and (
            isinstance(self.page_number, bool)
            or not isinstance(self.page_number, int)
            or self.page_number < 1
        ):
            raise ValueError("A página do resultado é inválida.")
        object.__setattr__(
            self, "document_identity", self.document_identity.strip()
        )
        object.__setattr__(self, "source_snippet", self._snippet(self.source_snippet))
        for field in (
            "document_name", "document_type", "search_term", "suggested_title",
        ):
            object.__setattr__(self, field, self._optional(getattr(self, field)))
        object.__setattr__(
            self, "document_path", self._optional_path(self.document_path)
        )

    @classmethod
    def from_search_result(cls, result) -> "EvidenceSourceCandidate":
        title = cls.suggest_title(
            getattr(result, "document_title", None),
            getattr(result, "file_path", None),
            getattr(result, "document_type", None),
            getattr(result, "snippet", ""),
        )
        terms = tuple(getattr(result, "matched_terms", ()) or ())
        return cls(
            document_identity=getattr(result, "document_sha256", ""),
            page_number=getattr(result, "page_number", None),
            source_snippet=getattr(result, "snippet", ""),
            document_name=getattr(result, "document_title", None),
            document_path=getattr(result, "file_path", None),
            document_type=getattr(result, "document_type", None),
            search_term=terms[0] if terms else None,
            suggested_title=title,
        )

    @classmethod
    def from_search_hit(cls, hit) -> "EvidenceSourceCandidate":
        """Adapta o contrato SearchHit na fronteira com Evidence."""
        title = cls.suggest_title(
            getattr(hit, "document_name", None),
            None,
            None,
            getattr(hit, "snippet", ""),
        )
        return cls(
            document_identity=getattr(hit, "document_identity", ""),
            page_number=getattr(hit, "page_number", None),
            source_snippet=getattr(hit, "snippet", ""),
            document_name=getattr(hit, "document_name", None),
            suggested_title=title,
        )

    @property
    def document_sha256(self) -> str:
        return self.document_identity

    @classmethod
    def suggest_title(cls, document_title, file_path, document_type, snippet) -> str:
        candidates = [document_title]
        if file_path:
            candidates.append(PurePath(str(file_path)).stem)
        candidates.append(document_type)
        useful_line = next(
            (line.strip() for line in str(snippet or "").splitlines() if line.strip()),
            None,
        )
        candidates.append(useful_line)
        candidates.append("Evidência da pesquisa")
        for candidate in candidates:
            normalized = cls._single_line(candidate)
            if normalized:
                return normalized[:cls.MAX_TITLE_LENGTH].rstrip()
        return "Evidência da pesquisa"

    @staticmethod
    def _single_line(value) -> str:
        return " ".join(str(value or "").split())

    @staticmethod
    def _optional(value) -> str | None:
        normalized = EvidenceSourceCandidate._single_line(value)
        return normalized or None

    @staticmethod
    def _optional_path(value) -> str | None:
        if value is None:
            return None
        normalized = "".join(
            character for character in str(value)
            if ord(character) >= 32
        ).strip()
        return normalized or None

    @staticmethod
    def _snippet(value) -> str:
        text = unicodedata.normalize("NFC", str(value or ""))
        text = "".join(char for char in text if char in "\n\t" or ord(char) >= 32)
        lines = [re.sub(r"[ \t]+", " ", line).strip() for line in text.splitlines()]
        return re.sub(r"\n{3,}", "\n\n", "\n".join(lines)).strip()
