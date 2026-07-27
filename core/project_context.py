"""Contexto permanente e neutro de um projeto aberto."""

from dataclasses import dataclass, field
from pathlib import Path
from types import MappingProxyType
from collections.abc import Mapping


@dataclass(frozen=True, slots=True)
class ProjectContext:
    """Snapshot passivo das informações permanentes de um projeto."""

    project: object
    application_id: str
    project_path: Path
    project_version: int
    permanent_metadata: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.project is None:
            raise ValueError("project não pode ser None.")
        if (
            not isinstance(self.application_id, str)
            or not self.application_id.strip()
        ):
            raise ValueError("application_id deve ser um texto não vazio.")
        if not isinstance(self.project_path, Path):
            raise TypeError("project_path deve ser um Path.")
        if (
            isinstance(self.project_version, bool)
            or not isinstance(self.project_version, int)
            or self.project_version < 1
        ):
            raise ValueError(
                "project_version deve ser um inteiro positivo."
            )
        try:
            metadata = dict(self.permanent_metadata)
        except (TypeError, ValueError) as exc:
            raise TypeError(
                "permanent_metadata deve ser um mapeamento."
            ) from exc
        if any(
            not isinstance(key, str) or not key.strip()
            for key in metadata
        ):
            raise ValueError(
                "permanent_metadata deve possuir chaves textuais não vazias."
            )

        object.__setattr__(
            self,
            "application_id",
            self.application_id.strip(),
        )
        object.__setattr__(
            self,
            "permanent_metadata",
            MappingProxyType(metadata),
        )
