"""
Tela inicial do ProcDocOrganizer.
"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QLabel,
    QVBoxLayout,
    QWidget,
)

from models.project import Project


class HomeView(QWidget):
    """
    Tela inicial da aplicação.
    """

    def __init__(self):
        super().__init__()

        self._build_ui()

    # ------------------------------------------------------------------

    def _build_ui(self):

        layout = QVBoxLayout(self)

        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(20)

        self.title_label = QLabel("ProcDocOrganizer")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        font = self.title_label.font()
        font.setPointSize(22)
        font.setBold(True)

        self.title_label.setFont(font)

        self.message_label = QLabel()
        self.message_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout.addWidget(self.title_label)
        layout.addWidget(self.message_label)

        self.on_project_closed()

    # ------------------------------------------------------------------

    def on_project_opened(
        self,
        project: Project,
    ):
        """
        Atualiza a tela quando um projeto é aberto.
        """

        self.message_label.setText(
            f"Projeto atual\n\n{project.project_name}"
        )

    # ------------------------------------------------------------------

    def on_project_closed(self):
        """
        Atualiza a tela quando nenhum projeto está aberto.
        """

        self.message_label.setText(
            "Nenhum projeto aberto."
        )

    # ------------------------------------------------------------------

    def refresh(self):
        """
        Atualiza a interface.

        Reservado para futuras implementações.
        """

        pass