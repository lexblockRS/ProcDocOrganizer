"""Formulário de apresentação para interpretação funcional."""

from datetime import date

from PySide6.QtWidgets import (
    QDialogButtonBox, QFormLayout, QLabel, QLineEdit, QVBoxLayout,
)

from .base_dialog import BaseDialog


class FunctionalAssignmentDialog(BaseDialog):
    def __init__(self, evidence, parent=None, initial=None):
        super().__init__(parent)
        self.setWindowTitle("Interpretar funcionalmente")
        self.resize(620, 440)
        layout = QVBoxLayout(self)
        source = QLabel(
            f"Evidence: {evidence.title}\n"
            f"Documento: {evidence.document_identity}\n"
            f"Página: {evidence.page_number or 'não informada'}"
        )
        source.setWordWrap(True)
        layout.addWidget(source)
        self.error_label = QLabel()
        self.error_label.setWordWrap(True)
        layout.addWidget(self.error_label)
        form = QFormLayout()
        self.fields = {
            "person_id": QLineEdit(),
            "exercise_type_code": QLineEdit(),
            "exercise_type_label": QLineEdit(),
            "role": QLineEdit(),
            "organization": QLineEdit(),
            "unit": QLineEdit(),
            "administrative_reference": QLineEdit(),
            "start_date": QLineEdit(),
            "end_date": QLineEdit(),
        }
        labels = {
            "person_id": "Pessoa:",
            "exercise_type_code": "Código do tipo:",
            "exercise_type_label": "Tipo de exercício:",
            "role": "Função:",
            "organization": "Organização:",
            "unit": "Unidade:",
            "administrative_reference": "Referência administrativa:",
            "start_date": "Data inicial (AAAA-MM-DD):",
            "end_date": "Data final (AAAA-MM-DD):",
        }
        for name, field in self.fields.items():
            form.addRow(labels[name], field)
            field.textChanged.connect(self._validate)
        if initial is not None:
            for name, field in self.fields.items():
                value = getattr(initial, name, None)
                if isinstance(value, date):
                    value = value.isoformat()
                field.setText(str(value) if value is not None else "")
        layout.addLayout(form)
        self.buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok
            | QDialogButtonBox.StandardButton.Cancel
        )
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        layout.addWidget(self.buttons)
        self._validate()

    def _validate(self):
        required = (
            "person_id", "exercise_type_code", "exercise_type_label",
            "role", "organization",
        )
        valid = all(
            self.fields[name].text().strip() for name in required
        )
        try:
            for name in ("start_date", "end_date"):
                value = self.fields[name].text().strip()
                if value:
                    date.fromisoformat(value)
            self.error_label.clear()
        except ValueError:
            valid = False
            self.error_label.setText(
                "Datas devem usar o formato AAAA-MM-DD."
            )
        self.buttons.button(
            QDialogButtonBox.StandardButton.Ok
        ).setEnabled(valid)

    def values(self):
        values = {
            name: field.text().strip()
            for name, field in self.fields.items()
        }
        for optional in ("unit", "administrative_reference"):
            values[optional] = values[optional] or None
        return values

    def show_error(self, message):
        self.error_label.setText(message)
