"""
Persistência dos resultados de processamento de documentos.
"""

from __future__ import annotations

import json
from pathlib import Path

from models import Project

from .processing_result import ProcessingResult


class ProcessingRepository:
    """
    Gerencia os resultados de processamento de um projeto.
    """

    def __init__(self, project: Project):
        self.project = project

    # ------------------------------------------------------------------

    @property
    def processing_folder(self) -> Path:
        """
        Retorna a pasta dos resultados de processamento.
        """

        return self.project.project_path / "processing"

    # ------------------------------------------------------------------

    def result_file(self, document_sha256: str) -> Path:
        """
        Retorna o arquivo de resultado de um documento.
        """

        return self.processing_folder / f"{document_sha256}.json"

    # ------------------------------------------------------------------

    def load(self, document_sha256: str) -> ProcessingResult | None:
        """
        Carrega o resultado persistido, quando existir.
        """

        result_file = self.result_file(document_sha256)

        if not result_file.exists():
            return None

        data = json.loads(result_file.read_text(encoding="utf-8"))

        return ProcessingResult.from_dict(data)

    # ------------------------------------------------------------------

    def list_results(self) -> list[ProcessingResult]:
        """
        Retorna os resultados válidos presentes na pasta de processamento.
        """

        if not self.processing_folder.exists():
            return []

        results = []

        for result_file in self.processing_folder.glob("*.json"):
            try:
                data = json.loads(result_file.read_text(encoding="utf-8"))
                results.append(ProcessingResult.from_dict(data))
            except (OSError, TypeError, ValueError, json.JSONDecodeError):
                continue

        return results

    # ------------------------------------------------------------------

    def save(self, result: ProcessingResult) -> None:
        """
        Salva um resultado de processamento de forma atômica.
        """

        self.processing_folder.mkdir(parents=True, exist_ok=True)

        result_file = self.result_file(result.document_sha256)
        temporary_file = result_file.with_suffix(result_file.suffix + ".tmp")

        try:
            temporary_file.write_text(
                json.dumps(
                    result.to_dict(),
                    indent=4,
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            temporary_file.replace(result_file)

        finally:
            temporary_file.unlink(missing_ok=True)
