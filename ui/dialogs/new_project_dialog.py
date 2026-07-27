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
    QComboBox,
    QVBoxLayout,
    QWidget,
)

from contracts import ApplicationDescriptor
from ui.dialogs.base_dialog import BaseDialog


class NewProjectDialog(BaseDialog):
    """
    Diálogo para criação de um novo projeto.
    """

    def __init__(self, parent=None, descriptors=()):
        super().__init__(parent)
        self._descriptors = self._validated_descriptors(descriptors)

        self.setWindowTitle("Novo Projeto")
        self.resize(520, 300)

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

        self.application_selector = QComboBox()
        for descriptor in self._descriptors:
            self.application_selector.addItem(
                descriptor.display_name,
                descriptor.application_id,
            )
        form.addRow(
            "Tipo de Projeto:",
            self.application_selector,
        )

        self.application_description = QLabel()
        self.application_description.setWordWrap(True)
        form.addRow("Descrição:", self.application_description)

        self.application_version = QLabel()
        form.addRow("Versão:", self.application_version)

        self.application_compatibility = QLabel()
        self.application_compatibility.setWordWrap(True)
        form.addRow("Compatibilidade:", self.application_compatibility)

        self.application_schema = QLabel()
        form.addRow("Schema:", self.application_schema)

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

        self.application_selector.currentIndexChanged.connect(
            self._show_selected_descriptor
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

        self._show_selected_descriptor()

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
            and self.application_selector.currentIndex() >= 0
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

    def get_application_id(self) -> str:
        """Retorna a identidade da Application selecionada."""

        return self.application_selector.currentData()

    @staticmethod
    def _validated_descriptors(descriptors) -> tuple[ApplicationDescriptor, ...]:
        values = tuple(descriptors)
        if any(
            not isinstance(descriptor, ApplicationDescriptor)
            for descriptor in values
        ):
            raise TypeError(
                "descriptors deve conter apenas ApplicationDescriptor."
            )
        return tuple(
            sorted(values, key=lambda item: item.application_id)
        )

    def _show_selected_descriptor(self) -> None:
        index = self.application_selector.currentIndex()
        descriptor = (
            self._descriptors[index]
            if 0 <= index < len(self._descriptors)
            else None
        )
        if descriptor is None:
            self.application_description.clear()
            self.application_version.clear()
            self.application_compatibility.clear()
            self.application_schema.clear()
            return

        self.application_description.setText(
            descriptor.description or "Não informada"
        )
        self.application_version.setText(str(descriptor.version))
        self.application_compatibility.setText(
            f"Plataforma {descriptor.minimum_platform_version} ou superior"
        )
        schemas = descriptor.supported_project_schema_versions
        self.application_schema.setText(
            ", ".join(str(version) for version in schemas)
            if schemas
            else "Não especificado"
        )
