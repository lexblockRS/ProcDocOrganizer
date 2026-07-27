"""Componentes desacoplados de reconhecimento óptico por página."""

from .ocr_engine import OCRDiagnostic, OCREngine, TesseractOCREngine
from .ocr_result import MergedTextResult, OCRResult
from .page_classifier import (
    PageClassificationStrategy,
    PageClassifier,
    TextThresholdStrategy,
)
from .text_merger import TextMerger

__all__ = [
    "MergedTextResult",
    "OCREngine",
    "OCRDiagnostic",
    "OCRResult",
    "PageClassificationStrategy",
    "PageClassifier",
    "TesseractOCREngine",
    "TextMerger",
    "TextThresholdStrategy",
]
