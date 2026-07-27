from PySide6.QtWidgets import (
    QDialogButtonBox,
    QFormLayout,
    QLabel,
    QLineEdit,
    QVBoxLayout,
)

from .base_dialog import BaseDialog


class ActivityDialog(BaseDialog):
    def __init__(self, exercise_count=0, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Nova atividade funcional")
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel(
            f"{exercise_count} exercício(s) selecionado(s)."
        ))
        form = QFormLayout()
        self.description = QLineEdit()
        form.addRow("Descrição:", self.description)
        layout.addLayout(form)
        self.buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok
            | QDialogButtonBox.StandardButton.Cancel
        )
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        self.description.textChanged.connect(self._validate)
        layout.addWidget(self.buttons)
        self._validate()

    def _validate(self):
        self.buttons.button(
            QDialogButtonBox.StandardButton.Ok
        ).setEnabled(bool(self.description.text().strip()))

    def values(self):
        return {"description": self.description.text().strip()}
