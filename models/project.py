"""
Modelo de Projeto do ProcDocOrganizer.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
import json


PROJECT_FORMAT_VERSION = 1


@dataclass
class Project:
    """
    Representa um projeto ProcDocOrganizer.
    """

    project_name: str
    project_path: Path
    created_at: str
    last_opened_at: str

    format_version: int = PROJECT_FORMAT_VERSION
    application: str = "ProcDocOrganizer"
    database: str = "database.db"

    # ---------------------------------------------------------

    @staticmethod
    def now() -> str:
        """
        Retorna a data e hora atual em formato ISO.
        """

        return datetime.now().isoformat(timespec="seconds")

    # ---------------------------------------------------------

    @classmethod
    def create(cls, project_name: str, project_path: Path):
        """
        Cria um novo projeto em memória.
        """

        timestamp = cls.now()

        return cls(
            project_name=project_name,
            project_path=project_path,
            created_at=timestamp,
            last_opened_at=timestamp,
        )

    # ---------------------------------------------------------

    @property
    def project_file(self) -> Path:
        """
        Caminho do arquivo project.json.
        """

        return self.project_path / "project.json"

    # ---------------------------------------------------------

    def to_dict(self) -> dict:
        """
        Converte o projeto para um dicionário.

        O caminho do projeto (project_path) NÃO é salvo,
        pois ele pode ser obtido pela localização do
        próprio project.json.
        """

        data = asdict(self)

        # Remove o caminho do projeto antes de salvar.
        data.pop("project_path", None)

        return data

    # ---------------------------------------------------------

    @classmethod
    def from_dict(cls, data: dict):
        """
        Constrói um objeto Project a partir de um dicionário.
        """

        return cls(**data)

    # ---------------------------------------------------------

    def save(self):
        """
        Salva o projeto em project.json.
        """

        with open(self.project_file, "w", encoding="utf-8") as file:

            json.dump(
                self.to_dict(),
                file,
                indent=4,
                ensure_ascii=False,
            )

    # ---------------------------------------------------------

    @classmethod
    def load(cls, project_file: Path):
        """
        Carrega um projeto existente.
        """

        with open(project_file, "r", encoding="utf-8") as file:

            data = json.load(file)

        # O caminho do projeto é reconstruído automaticamente.
        data["project_path"] = project_file.parent

        return cls.from_dict(data)