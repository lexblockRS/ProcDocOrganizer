"""Solicitacao operacional especifica para a avaliacao RSC."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ExecuteEvaluationAction:
    project_id: str

    def __post_init__(self) -> None:
        if not isinstance(self.project_id, str) or not self.project_id.strip():
            raise ValueError("project_id deve ser string nao vazia.")
        object.__setattr__(self, "project_id", self.project_id.strip())


__all__ = ["ExecuteEvaluationAction"]
