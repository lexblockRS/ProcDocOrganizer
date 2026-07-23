"""Classifica individualmente páginas que precisam de OCR."""

from abc import ABC, abstractmethod
import re


class PageClassificationStrategy(ABC):
    @abstractmethod
    def has_sufficient_text(self, text: str) -> bool:
        """Informa se o texto nativo pode ser usado sem OCR."""


class TextThresholdStrategy(PageClassificationStrategy):
    """Estratégia inicial baseada em caracteres úteis e palavras."""

    def __init__(self, minimum_characters: int = 20, minimum_words: int = 3):
        if minimum_characters < 0 or minimum_words < 0:
            raise ValueError("Os limites de classificação não podem ser negativos.")
        self.minimum_characters = minimum_characters
        self.minimum_words = minimum_words

    def has_sufficient_text(self, text: str) -> bool:
        if not isinstance(text, str):
            return False
        useful_characters = sum(not character.isspace() for character in text)
        words = re.findall(r"\b\w+\b", text, flags=re.UNICODE)
        return (
            useful_characters >= self.minimum_characters
            and len(words) >= self.minimum_words
        )


class PageClassifier:
    def __init__(self, strategy: PageClassificationStrategy | None = None):
        self.strategy = strategy or TextThresholdStrategy()

    def requires_ocr(self, text: str) -> bool:
        return not self.strategy.has_sufficient_text(text)

