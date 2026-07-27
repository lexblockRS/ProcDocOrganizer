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

    def __init__(self, *, title="", icon=None, parent=None):
        super().__init__(parent)
        self.title = title
        self.icon = icon
        self.state = None

    # ------------------------------------------------------------------

    def on_project_opened(self, project):
        """
        Chamado quando um projeto é aberto.
        """
        pass

    def on_project_open(self, project):
        """Contrato padronizado para abertura de projeto."""

        return self.on_project_opened(project)

    def on_project_changed(self, project):
        """Contrato padronizado para troca do projeto ativo."""

        return self.on_project_opened(project)

    # ------------------------------------------------------------------

    def on_project_closed(self):
        """
        Chamado quando um projeto é fechado.
        """
        pass

    def on_project_close(self):
        """Contrato padronizado para fechamento de projeto."""

        return self.on_project_closed()

    # ------------------------------------------------------------------

    def refresh(self):
        """
        Atualiza os dados exibidos na View.
        """
        pass
