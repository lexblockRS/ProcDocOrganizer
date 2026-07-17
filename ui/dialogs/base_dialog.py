"""
Classe base para todos os diálogos da aplicação.
"""

from PySide6.QtWidgets import QDialog


class BaseDialog(QDialog):
    """
    Classe base para os diálogos do ProcDocOrganizer.
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        self._configure_window()

    # ------------------------------------------------------------------

    def _configure_window(self) -> None:
        """
        Configurações comuns dos diálogos.
        """

        self.setModal(True)