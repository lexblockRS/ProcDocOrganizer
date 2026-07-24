"""
Diálogo para criação de um novo projeto.
"""

from pathlib import Path

from PySide6.QtWidgets import (
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from ui.dialogs.base_dialog import BaseDialog


class NewProjectDialog(BaseDialog):
    """
    Diálogo para criação de um novo projeto.
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Novo Projeto")
        self.resize(520, 180)

        self._build_ui()
        self._connect_signals()
        self._validate()

    # ------------------------------------------------------------------

    def _build_ui(self):

        layout = QVBoxLayout(self)

        description = QLabel(
            "Informe o nome do projeto e a pasta onde ele será criado."
        )

        description.setWordWrap(True)

        layout.addWidget(description)

        form = QFormLayout()

        self.project_name = QLineEdit()

        form.addRow(
            "Nome do Projeto:",
            self.project_name,
        )

        folder_widget = QWidget()

        folder_layout = QHBoxLayout(folder_widget)
        folder_layout.setContentsMargins(0, 0, 0, 0)

        self.project_folder = QLineEdit()

        self.browse_button = QPushButton("Procurar...")

        folder_layout.addWidget(self.project_folder)
        folder_layout.addWidget(self.browse_button)

        form.addRow(
            "Pasta:",
            folder_widget,
        )

        layout.addLayout(form)

        layout.addStretch()

        buttons = QHBoxLayout()

        buttons.addStretch()

        self.cancel_button = QPushButton("Cancelar")

        self.create_button = QPushButton("Criar")

        self.create_button.setDefault(True)

        buttons.addWidget(self.cancel_button)
        buttons.addWidget(self.create_button)

        layout.addLayout(buttons)

    # ------------------------------------------------------------------

    def _connect_signals(self):

        self.project_name.textChanged.connect(
            self._validate
        )

        self.project_folder.textChanged.connect(
            self._validate
        )

        self.browse_button.clicked.connect(
            self._select_folder
        )

        self.cancel_button.clicked.connect(
            self.reject
        )

        self.create_button.clicked.connect(
            self.accept
        )

    # ------------------------------------------------------------------

    def _select_folder(self):

        folder = QFileDialog.getExistingDirectory(
            self,
            "Selecione a pasta",
        )

        if folder:
            self.project_folder.setText(folder)

    # ------------------------------------------------------------------

    def _validate(self):

        valid = (
            bool(self.project_name.text().strip())
            and bool(self.project_folder.text().strip())
        )

        self.create_button.setEnabled(valid)

    # ------------------------------------------------------------------

    def get_project_name(self) -> str:
        """
        Retorna o nome do projeto.
        """

        return self.project_name.text().strip()

    # ------------------------------------------------------------------

    def get_project_folder(self) -> Path:
        """
        Retorna a pasta onde o projeto será criado.
        """

        return Path(
            self.project_folder.text().strip()
        )
