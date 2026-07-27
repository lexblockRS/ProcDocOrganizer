"""Interface do motor OCR e implementação encapsulada com Tesseract."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
import os
from pathlib import Path
import shutil
import subprocess
from tempfile import TemporaryDirectory

from .ocr_result import OCRResult


class OCREngine(ABC):
    @abstractmethod
    def recognize_page(self, pdf_path: Path, page_number: int) -> OCRResult:
        """Executa OCR em uma página numerada a partir de 1."""


@dataclass(frozen=True)
class OCRDiagnostic:
    available: bool
    executable: str | None
    language: str
    message: str


class TesseractOCREngine(OCREngine):
    """Renderiza com QtPdf e executa o Tesseract CLI em uma imagem temporária."""

    def __init__(
        self,
        executable: str | None = None,
        language: str = "por",
        dpi: int = 300,
        timeout_seconds: int = 120,
    ):
        self.executable = (
            executable
            or os.environ.get("PROCDOC_TESSERACT_PATH")
            or "tesseract"
        )
        self.language = language
        self.dpi = dpi
        self.timeout_seconds = timeout_seconds

    def diagnose(self) -> OCRDiagnostic:
        executable = shutil.which(self.executable)
        if executable is None:
            return OCRDiagnostic(
                False,
                None,
                self.language,
                f"Executável OCR '{self.executable}' não encontrado. "
                "Instale o Tesseract ou configure PROCDOC_TESSERACT_PATH.",
            )
        try:
            process = subprocess.run(
                [executable, "--list-langs"],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=min(self.timeout_seconds, 30),
                check=False,
            )
        except Exception as exc:
            return OCRDiagnostic(
                False, executable, self.language,
                f"Não foi possível consultar os idiomas do Tesseract: {exc}",
            )
        languages = {
            line.strip()
            for line in process.stdout.splitlines()
            if line.strip()
        }
        if process.returncode != 0:
            return OCRDiagnostic(
                False, executable, self.language,
                process.stderr.strip()
                or "O Tesseract não respondeu à verificação de idiomas.",
            )
        if self.language not in languages:
            return OCRDiagnostic(
                False,
                executable,
                self.language,
                f"O idioma OCR '{self.language}' não está instalado.",
            )
        return OCRDiagnostic(
            True,
            executable,
            self.language,
            "Tesseract e idioma OCR disponíveis.",
        )

    def recognize_page(self, pdf_path: Path, page_number: int) -> OCRResult:
        diagnostic = self.diagnose()
        if not diagnostic.available:
            return OCRResult(
                page_number=page_number,
                success=False,
                error=diagnostic.message,
            )
        executable = diagnostic.executable

        try:
            image = self._render_page(pdf_path, page_number)
            with TemporaryDirectory() as temporary_directory:
                image_path = Path(temporary_directory) / "page.png"
                if not image.save(str(image_path), "PNG"):
                    raise RuntimeError("Não foi possível salvar a página para OCR.")
                process = subprocess.run(
                    [
                        executable,
                        str(image_path),
                        "stdout",
                        "-l",
                        self.language,
                    ],
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    timeout=self.timeout_seconds,
                    check=False,
                )
            if process.returncode != 0:
                return OCRResult(
                    page_number=page_number,
                    success=False,
                    error=(process.stderr.strip() or "Falha desconhecida no OCR."),
                )
            return OCRResult(page_number=page_number, text=process.stdout)
        except Exception as exc:
            return OCRResult(
                page_number=page_number,
                success=False,
                error=str(exc),
            )

    def _render_page(self, pdf_path: Path, page_number: int):
        from PySide6.QtCore import QSize
        from PySide6.QtPdf import QPdfDocument

        document = QPdfDocument()
        error = document.load(str(pdf_path))
        if error != QPdfDocument.Error.None_:
            raise ValueError(f"Não foi possível abrir '{pdf_path.name}' para OCR.")
        page_index = page_number - 1
        if page_index < 0 or page_index >= document.pageCount():
            raise ValueError(f"Página inválida para OCR: {page_number}.")
        points = document.pagePointSize(page_index)
        scale = self.dpi / 72
        size = QSize(
            max(1, round(points.width() * scale)),
            max(1, round(points.height() * scale)),
        )
        return document.render(page_index, size)

