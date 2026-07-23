"""
Modelo de Projeto do ProcDocOrganizer.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path


PROJECT_FORMAT_VERSION = 1


@dataclass
class Project:
    """
    Representa um projeto do ProcDocOrganizer.
    """

    project_name: str
    project_path: Path
    created_at: str
    last_opened_at: str

    application: str = "ProcDocOrganizer"
    format_version: int = PROJECT_FORMAT_VERSION
    database: str = "database.db"

    # ------------------------------------------------------------------

    @staticmethod
    def now() -> str:
        """
        Retorna a data/hora atual em formato ISO 8601.
        """

        return datetime.now().isoformat(timespec="seconds")

    # ------------------------------------------------------------------

    @classmethod
    def create(cls, project_name: str, project_path: Path) -> "Project":
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

    # ------------------------------------------------------------------

    @property
    def project_file(self) -> Path:
        """
        Retorna o caminho do arquivo project.json.
        """

        return self.project_path / "project.json"

    # ------------------------------------------------------------------

    def to_dict(self) -> dict:
        """
        Converte o projeto para um dicionário.

        O caminho do projeto não é salvo porque ele pode ser
        reconstruído a partir da localização do project.json.
        """

        data = asdict(self)

        data.pop("project_path", None)

        return data

    # ------------------------------------------------------------------

    def to_json(self) -> str:
        """
        Converte o projeto para uma string JSON.
        """

        return json.dumps(
            self.to_dict(),
            indent=4,
            ensure_ascii=False,
        )

    # ------------------------------------------------------------------

    @classmethod
    def from_dict(cls, data: dict) -> "Project":
        """
        Cria um objeto Project a partir de um dicionário.
        """

        return cls(**data)

    # ------------------------------------------------------------------

    @classmethod
    def from_json(cls, json_text: str, project_path: Path) -> "Project":
        """
        Cria um objeto Project a partir de um texto JSON.
        """

        data = json.loads(json_text)

        data["project_path"] = project_path

        return cls.from_dict(data)

    # ------------------------------------------------------------------

    def save(self) -> None:
        """
        Salva o projeto no arquivo project.json.
        """

        temporary_file = self.project_file.with_suffix(
            self.project_file.suffix + ".tmp"
        )

        try:
            temporary_file.write_text(
                self.to_json(),
                encoding="utf-8",
            )

            temporary_file.replace(self.project_file)

        finally:
            temporary_file.unlink(missing_ok=True)

    # ------------------------------------------------------------------

    @classmethod
    def load(cls, project_file: Path) -> "Project":
        """
        Carrega um projeto existente.
        """

        json_text = project_file.read_text(
            encoding="utf-8"
        )

        return cls.from_json(
            json_text,
            project_file.parent,
        )
