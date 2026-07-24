"""Modelo de domínio imutável de evidência documental."""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import date, datetime
from uuid import UUID, uuid4


@dataclass(frozen=True, init=False)
class Evidence:
    """Evidência vinculada a uma identidade documental opaca."""

    MAX_TITLE_LENGTH = 300

    id: str
    document_identity: str
    page_number: int | None
    title: str
    source_snippet: str | None
    user_notes: str | None
    category: str | None
    start_date: str | None
    end_date: str | None
    created_at: str
    updated_at: str

    def __init__(
        self,
        id: str,
        document_identity: str | None = None,
        page_number: int | None = None,
        title: str = "",
        source_snippet: str | None = None,
        user_notes: str | None = None,
        category: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        created_at: str = "",
        updated_at: str = "",
    ) -> None:
        for field, value in (
            ("id", id),
            ("document_identity", document_identity),
            ("page_number", page_number),
            ("title", title),
            ("source_snippet", source_snippet),
            ("user_notes", user_notes),
            ("category", category),
            ("start_date", start_date),
            ("end_date", end_date),
            ("created_at", created_at),
            ("updated_at", updated_at),
        ):
            object.__setattr__(self, field, value)
        self.__post_init__()

    def __post_init__(self) -> None:
        object.__setattr__(self, "id", self._uuid(self.id))
        object.__setattr__(
            self, "document_identity", self._identity(self.document_identity)
        )
        if (
            self.page_number is not None
            and (isinstance(self.page_number, bool) or not isinstance(self.page_number, int) or self.page_number < 1)
        ):
            raise ValueError("page_number deve ser um inteiro maior ou igual a 1.")
        title = self._required_text(self.title, "title")
        if len(title) > self.MAX_TITLE_LENGTH:
            raise ValueError(f"title deve possuir no máximo {self.MAX_TITLE_LENGTH} caracteres.")
        object.__setattr__(self, "title", title)
        for field in ("source_snippet", "user_notes", "category"):
            object.__setattr__(self, field, self._optional_text(getattr(self, field), field))
        start = self._date(self.start_date, "start_date")
        end = self._date(self.end_date, "end_date")
        if start and end and start > end:
            raise ValueError("end_date não pode ser anterior a start_date.")
        object.__setattr__(self, "start_date", start)
        object.__setattr__(self, "end_date", end)
        created = self._timestamp(self.created_at, "created_at")
        updated = self._timestamp(self.updated_at, "updated_at")
        try:
            updated_value = datetime.fromisoformat(updated)
            created_value = datetime.fromisoformat(created)
            if updated_value < created_value:
                raise ValueError("updated_at não pode ser anterior a created_at.")
        except TypeError as exc:
            raise ValueError(
                "created_at e updated_at devem usar o mesmo padrão de timezone."
            ) from exc
        object.__setattr__(self, "created_at", created)
        object.__setattr__(self, "updated_at", updated)

    @classmethod
    def create(
        cls,
        document_identity: str | None = None,
        title: str = "",
        page_number: int | None = None,
        source_snippet: str | None = None,
        user_notes: str | None = None,
        category: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        evidence_id: str | None = None,
        timestamp: str | None = None,
    ) -> "Evidence":
        instant = timestamp or cls.now()
        return cls(
            id=evidence_id or str(uuid4()),
            document_identity=document_identity,
            page_number=page_number, title=title, source_snippet=source_snippet,
            user_notes=user_notes, category=category, start_date=start_date,
            end_date=end_date, created_at=instant, updated_at=instant,
        )

    @staticmethod
    def now() -> str:
        return datetime.now().isoformat(timespec="seconds")

    def with_changes(self, **changes) -> "Evidence":
        """Cria uma nova versão; o repositório controla os timestamps persistidos."""
        return replace(self, **changes)

    @staticmethod
    def _uuid(value: object) -> str:
        if not isinstance(value, str) or not value.strip():
            raise ValueError("id deve ser um UUID válido.")
        try:
            return str(UUID(value.strip()))
        except (ValueError, AttributeError) as exc:
            raise ValueError("id deve ser um UUID válido.") from exc

    @staticmethod
    def _identity(value: object) -> str:
        if not isinstance(value, str) or not value.strip():
            raise ValueError("document_identity deve ser um texto não vazio.")
        return value.strip()

    @staticmethod
    def _required_text(value: object, field: str) -> str:
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{field} deve ser um texto não vazio.")
        return value.strip()

    @classmethod
    def _optional_text(cls, value: object, field: str) -> str | None:
        if value is None:
            return None
        if isinstance(value, str) and not value.strip():
            return None
        return cls._required_text(value, field)

    @staticmethod
    def _date(value: object, field: str) -> str | None:
        if value is None:
            return None
        if not isinstance(value, str):
            raise ValueError(f"{field} deve usar o formato ISO AAAA-MM-DD.")
        try:
            return date.fromisoformat(value.strip()).isoformat()
        except ValueError as exc:
            raise ValueError(f"{field} deve usar o formato ISO AAAA-MM-DD.") from exc

    @staticmethod
    def _timestamp(value: object, field: str) -> str:
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{field} deve ser um timestamp ISO válido.")
        normalized = value.strip()
        if "T" not in normalized:
            raise ValueError(f"{field} deve ser um timestamp ISO válido.")
        try:
            parsed = datetime.fromisoformat(normalized)
        except ValueError as exc:
            raise ValueError(f"{field} deve ser um timestamp ISO válido.") from exc
        return parsed.isoformat(timespec="seconds")
