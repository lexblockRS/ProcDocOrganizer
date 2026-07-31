"""
Estado da aplicação.

Mantém informações sobre o projeto atualmente aberto.
"""

from __future__ import annotations

class ProjectState:
    """
    Mantém o estado atual da aplicação.

    Esta classe não possui lógica de negócio.
    Ela apenas informa qual projeto está aberto no momento.
    """

    def __init__(self, lifecycle_host):
        if lifecycle_host is None:
            raise ValueError("lifecycle_host é obrigatório.")
        self._lifecycle_host = lifecycle_host

    # ------------------------------------------------------------------

    @property
    def current_project(self):
        """
        Retorna o projeto atualmente aberto.
        """

        session = self._lifecycle_host.current_session
        return None if session is None else session.project

    # ------------------------------------------------------------------

    @property
    def has_project(self) -> bool:
        """
        Indica se existe um projeto aberto.
        """

        return self._lifecycle_host.current_session is not None
