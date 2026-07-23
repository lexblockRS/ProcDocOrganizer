"""Parâmetros imutáveis de uma pesquisa textual."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Iterable


@dataclass(frozen=True)
class SearchFilters:
    """Descreve uma pesquisa sem conhecer SQL ou infraestrutura."""

    terms: tuple[str, ...] = ()
    phrase: str | None = None
    match_mode: str = "all"
    document_type: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    only_processed: bool = True
    limit: int = 50
    offset: int = 0

    def __post_init__(self) -> None:
        if isinstance(self.terms, str) or not isinstance(self.terms, Iterable):
            raise TypeError("terms deve ser uma coleção de textos.")
        terms = tuple(self._required_text(term, "terms") for term in self.terms)
        object.__setattr__(self, "terms", terms)
        object.__setattr__(self, "phrase", self._optional_text(self.phrase, "phrase"))
        object.__setattr__(
            self, "document_type",
            self._optional_text(self.document_type, "document_type"),
        )
        if self.match_mode not in {"all", "any", "phrase"}:
            raise ValueError("match_mode deve ser 'all', 'any' ou 'phrase'.")
        if not isinstance(self.only_processed, bool):
            raise TypeError("only_processed deve ser booleano.")
        if isinstance(self.limit, bool) or not isinstance(self.limit, int) or self.limit < 1:
            raise ValueError("limit deve ser um inteiro positivo.")
        if isinstance(self.offset, bool) or not isinstance(self.offset, int) or self.offset < 0:
            raise ValueError("offset deve ser um inteiro não negativo.")
        start = self._date(self.start_date, "start_date")
        end = self._date(self.end_date, "end_date")
        object.__setattr__(self, "start_date", start)
        object.__setattr__(self, "end_date", end)
        if start and end and start > end:
            raise ValueError("start_date não pode ser posterior a end_date.")
        if self.match_mode == "phrase" and not self.phrase:
            raise ValueError("phrase é obrigatória no modo phrase.")
        if self.match_mode != "phrase" and not terms and not self.phrase:
            raise ValueError("Informe ao menos um termo ou uma frase.")

    @staticmethod
    def _required_text(value: object, field: str) -> str:
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{field} deve conter apenas textos não vazios.")
        return value.strip()

    @classmethod
    def _optional_text(cls, value: object, field: str) -> str | None:
        if value is None:
            return None
        return cls._required_text(value, field)

    @staticmethod
    def _date(value: object, field: str) -> str | None:
        if value is None:
            return None
        if not isinstance(value, str):
            raise TypeError(f"{field} deve usar o formato ISO AAAA-MM-DD.")
        try:
            return date.fromisoformat(value.strip()).isoformat()
        except ValueError as exc:
            raise ValueError(f"{field} deve usar o formato ISO AAAA-MM-DD.") from exc
