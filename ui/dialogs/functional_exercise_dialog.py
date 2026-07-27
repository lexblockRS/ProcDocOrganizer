"""Formulário de apresentação para criação de exercício funcional."""

from datetime import date

from PySide6.QtWidgets import (
    QDialogButtonBox,
    QFormLayout,
    QLabel,
    QLineEdit,
    QVBoxLayout,
)

from .base_dialog import BaseDialog


class FunctionalExerciseDialog(BaseDialog):
    def __init__(self, assignments, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Criar exercício funcional")
        self.resize(640, 430)
        layout = QVBoxLayout(self)
        selected = QLabel(
            f"{len(assignments)} interpretação(ões) selecionada(s)."
        )
        selected.setWordWrap(True)
        layout.addWidget(selected)
        self.error_label = QLabel()
        self.error_label.setWordWrap(True)
        layout.addWidget(self.error_label)
        form = QFormLayout()
        first = assignments[0] if assignments else None
        defaults = {
            "person_id": getattr(first, "person_id", ""),
            "exercise_type_code": getattr(
                first, "exercise_type_code", ""
            ),
            "exercise_type_label": getattr(
                first, "exercise_type_label", ""
            ),
            "role": getattr(first, "role", ""),
            "context_organization": getattr(
                first, "organization", ""
            ),
            "context_unit": getattr(first, "unit", "") or "",
            "context_reference": getattr(
                first, "administrative_reference", ""
            ) or "",
            "start_date": (
                first.start_date.isoformat()
                if first and first.start_date else ""
            ),
            "end_date": (
                first.end_date.isoformat()
                if first and first.end_date else ""
            ),
        }
        labels = {
            "person_id": "Pessoa:",
            "exercise_type_code": "Código do tipo:",
            "exercise_type_label": "Tipo de exercício:",
            "role": "Função:",
            "context_organization": "Organização:",
            "context_unit": "Unidade:",
            "context_reference": "Referência administrativa:",
            "start_date": "Data inicial (AAAA-MM-DD):",
            "end_date": "Data final (AAAA-MM-DD, opcional):",
        }
        self.fields = {}
        for name, value in defaults.items():
            field = QLineEdit(value)
            field.textChanged.connect(self._validate)
            self.fields[name] = field
            form.addRow(labels[name], field)
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
            "person_id",
            "exercise_type_code",
            "exercise_type_label",
            "role",
            "context_organization",
            "start_date",
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
        values["start_date"] = date.fromisoformat(values["start_date"])
        values["end_date"] = (
            date.fromisoformat(values["end_date"])
            if values["end_date"] else None
        )
        for optional in ("context_unit", "context_reference"):
            values[optional] = values[optional] or None
        return values
