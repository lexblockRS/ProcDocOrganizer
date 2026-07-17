"""
Classe base para todas as Views do ProcDocOrganizer.
"""

from PySide6.QtWidgets import QWidget


class BaseView(QWidget):
    """
    Classe base para todas as telas da aplicação.

    Cada View poderá sobrescrever estes métodos para responder
    aos eventos do ciclo de vida do projeto.
    """

    def __init__(self):
        super().__init__()

    # ------------------------------------------------------------------

    def on_project_opened(self, project):
        """
        Chamado quando um projeto é aberto.
        """
        pass

    # ------------------------------------------------------------------

    def on_project_closed(self):
        """
        Chamado quando um projeto é fechado.
        """
        pass

    # ------------------------------------------------------------------

    def refresh(self):
        """
        Atualiza os dados exibidos na View.
        """
        pass
    