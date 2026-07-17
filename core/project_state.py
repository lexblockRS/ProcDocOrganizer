"""
Estado da aplicação.

Mantém informações sobre o projeto atualmente aberto.
"""

from __future__ import annotations

from typing import Optional

from models.project import Project


class ProjectState:
    """
    Mantém o estado atual da aplicação.

    Esta classe não possui lógica de negócio.
    Ela apenas informa qual projeto está aberto no momento.
    """

    def __init__(self):

        self._current_project: Optional[Project] = None

    # ------------------------------------------------------------------

    @property
    def current_project(self) -> Optional[Project]:
        """
        Retorna o projeto atualmente aberto.
        """

        return self._current_project

    # ------------------------------------------------------------------

    @property
    def has_project(self) -> bool:
        """
        Indica se existe um projeto aberto.
        """

        return self._current_project is not None

    # ------------------------------------------------------------------

    def open_project(self, project: Project):
        """
        Define o projeto atualmente aberto.
        """

        self._current_project = project

    # ------------------------------------------------------------------

    def close_project(self):
        """
        Fecha o projeto atual.
        """

        self._current_project = None