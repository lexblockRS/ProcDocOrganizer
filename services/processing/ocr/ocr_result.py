"""Modelos de resultado internos do pipeline de OCR."""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class OCRResult:
    page_number: int
    text: str = ""
    success: bool = True
    error: str | None = None


@dataclass(frozen=True)
class MergedTextResult:
    pages: list[dict] = field(default_factory=list)
    text_source: str = "native"
    ocr_used: bool = False
    ocr_errors: list[str] = field(default_factory=list)

