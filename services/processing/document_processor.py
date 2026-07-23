"""Orquestrador genérico do processamento documental."""

import hashlib
from pathlib import Path

from models import Document, Project

from .processing_result import ProcessingResult
from .processing_repository import ProcessingRepository
from .document_metadata_extractor import DocumentMetadataExtractor
from .ocr import OCREngine, PageClassifier, TextMerger
from .parsers.default_registry import create_default_parser_registry
from .parsers.parser_registry import ParserRegistry
from .text_extractor import TextExtractor


class DocumentProcessor:
    """
    Resolve um parser, valida seu resultado e gerencia cache e persistência.
    """

    def __init__(
        self,
        text_extractor: TextExtractor | None = None,
        metadata_extractor: DocumentMetadataExtractor | None = None,
        page_classifier: PageClassifier | None = None,
        ocr_engine: OCREngine | None = None,
        text_merger: TextMerger | None = None,
        parser_registry: ParserRegistry | None = None,
    ):
        self.metadata_extractor = (
            metadata_extractor or DocumentMetadataExtractor()
        )
        self.parser_registry = parser_registry or create_default_parser_registry(
            text_extractor=text_extractor,
            page_classifier=page_classifier,
            ocr_engine=ocr_engine,
            text_merger=text_merger,
        )

    # ------------------------------------------------------------------

    def process(
        self,
        project: Project,
        document: Document,
    ) -> ProcessingResult:
        """
        Processa um documento ou reutiliza um resultado válido.
        """

        repository = ProcessingRepository(project)
        document_file = project.project_path / document.relative_path
        document_sha256 = document.sha256

        try:
            document_sha256 = self._calculate_sha256(document_file)
            existing_result = repository.load(document_sha256)

            if existing_result is not None and existing_result.is_valid_for(
                document_sha256
            ):
                metadata_changed = self._enrich_result(existing_result)

                if metadata_changed:
                    repository.save(existing_result)
                return existing_result

            parser = self.parser_registry.resolve(document_file)
            result = parser.parse(
                document_file,
                context={"document_sha256": document_sha256},
            )
            self._validate_result(result, document_sha256)
            self._enrich_result(result)

        except Exception as exc:
            if not document_sha256:
                raise

            result = ProcessingResult(
                document_sha256=document_sha256,
                processed_at=ProcessingResult.now(),
                status="failed",
                error=str(exc),
            )

        repository.save(result)

        return result

    # ------------------------------------------------------------------

    @staticmethod
    def _validate_result(result: ProcessingResult, document_sha256: str) -> None:
        if not isinstance(result, ProcessingResult):
            raise TypeError("O parser não retornou um ProcessingResult.")
        if result.document_sha256 != document_sha256:
            raise ValueError("O resultado do parser possui SHA-256 divergente.")
        if (
            not isinstance(result.pages, list)
            or result.page_count != len(result.pages)
        ):
            raise ValueError("O resultado do parser possui páginas inconsistentes.")

    # ------------------------------------------------------------------

    def get_valid_result(
        self,
        project: Project,
        document: Document,
    ) -> ProcessingResult | None:
        """
        Retorna o resultado reutilizável para o conteúdo atual do arquivo.
        """

        document_file = project.project_path / document.relative_path
        document_sha256 = self._calculate_sha256(document_file)
        repository = ProcessingRepository(project)
        result = repository.load(document_sha256)

        if result is None or not result.is_valid_for(document_sha256):
            return None

        metadata_changed = self._enrich_result(result)

        if metadata_changed:
            repository.save(result)

        return result

    # ------------------------------------------------------------------

    def _enrich_result(self, result: ProcessingResult) -> bool:
        """
        Enriquece apenas resultados processados que possuem texto utilizável.
        """

        if result.status == "ocr_required":
            if result.metadata or result.metadata_extractor_version is not None:
                result.metadata = {}
                result.metadata_extractor_version = None
                return True

            return False

        if result.status != "processed" or not result.has_searchable_text():
            return False

        if (
            result.metadata_extractor_version
            == self.metadata_extractor.VERSION
        ):
            return False

        result.metadata = self.metadata_extractor.extract(result.pages)
        result.metadata_extractor_version = self.metadata_extractor.VERSION

        return True

    # ------------------------------------------------------------------

    @staticmethod
    def _calculate_sha256(file_path: Path) -> str:
        """
        Calcula o hash do arquivo antes de processá-lo.
        """

        digest = hashlib.sha256()

        with file_path.open("rb") as file:
            for chunk in iter(lambda: file.read(1024 * 1024), b""):
                digest.update(chunk)

        return digest.hexdigest()
