"""Apresenta metadados documentais de interesse do usuário."""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from models import DocumentType


class DocumentMetadataWidget(QWidget):
    save_requested = Signal(str)
    cancel_requested = Signal()
    editing_changed = Signal(bool)
    _STATUS_LABELS = {
        "processed": "Processado",
        "not_processed": "Não processado",
        "processing": "Em processamento",
        "pending": "Pendente",
        "failed": "Falha no processamento",
        "cancelled": "Cancelado",
        "ocr_required": "OCR necessário",
    }

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.values = {}
        self._details = None
        self._editing = False
        layout = QVBoxLayout(self)
        form = QFormLayout()
        fields = (
            ("name", "Nome"), ("type", "Tipo"),
            ("path", "Caminho"), ("hash", "Hash"),
            ("imported", "Data de inclusão"), ("date", "Data documental"),
            ("status", "Situação"), ("pages", "Quantidade de páginas"),
            ("ocr", "Situação do OCR"), ("source", "Origem do texto"),
            ("processed", "Data de processamento"),
        )
        for key, label in fields:
            value = QLabel("Não informado")
            value.setWordWrap(True)
            value.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            form.addRow(f"{label}:", value)
            self.values[key] = value
        layout.addLayout(form)
        self.type_editor = QComboBox()
        for document_type in DocumentType:
            self.type_editor.addItem(
                document_type.value.replace("_", " ").title(),
                document_type.value,
            )
        self.type_editor.hide()
        form.addRow("Editar tipo:", self.type_editor)
        self.unsaved_label = QLabel("Alterações não salvas")
        self.unsaved_label.setStyleSheet("color: #9a6700; font-weight: bold;")
        self.unsaved_label.hide()
        layout.addWidget(self.unsaved_label)
        actions = QHBoxLayout()
        self.edit_button = QPushButton("Editar metadados")
        self.save_button = QPushButton("Salvar")
        self.cancel_button = QPushButton("Cancelar")
        self.save_button.hide()
        self.cancel_button.hide()
        actions.addWidget(self.edit_button)
        actions.addWidget(self.save_button)
        actions.addWidget(self.cancel_button)
        actions.addStretch(1)
        layout.addLayout(actions)
        self.edit_button.clicked.connect(self.begin_edit)
        self.save_button.clicked.connect(self._request_save)
        self.cancel_button.clicked.connect(self.cancel_requested)
        self.type_editor.currentIndexChanged.connect(self._draft_changed)

    def set_details(self, details) -> None:
        if details is None:
            self.clear()
            return
        self._details = details
        summary = details.summary
        values = {
            "name": summary.name,
            "type": summary.document_type,
            "path": summary.relative_path,
            "hash": summary.sha256,
            "imported": details.imported_at,
            "date": summary.document_date,
            "status": self._STATUS_LABELS.get(
                summary.processing_status, summary.processing_status
            ),
            "pages": str(details.page_count),
            "ocr": "Sim" if details.ocr_used else "Não",
            "source": details.text_source,
            "processed": details.processed_at,
        }
        for key, value in values.items():
            self.values[key].setText(str(value) if value not in (None, "") else "Não informado")
        if not self._editing:
            self._set_editor_value(summary.document_type)
        self.edit_button.setEnabled(True)

    def show_unprocessed(self) -> None:
        self.values["status"].setText("Este documento ainda não foi processado.")

    def clear(self) -> None:
        self._details = None
        for value in self.values.values():
            value.setText("Não informado")
        self.finish_edit()
        self.edit_button.setEnabled(False)

    @property
    def is_editing(self) -> bool:
        return self._editing

    @property
    def has_unsaved_changes(self) -> bool:
        return bool(
            self._editing
            and self._details is not None
            and self.type_editor.currentData()
            != self._details.summary.document_type
        )

    def begin_edit(self) -> bool:
        if self._details is None or self._editing:
            return False
        self._editing = True
        self._set_editor_value(self._details.summary.document_type)
        self.type_editor.show()
        self.edit_button.hide()
        self.save_button.show()
        self.cancel_button.show()
        self.unsaved_label.hide()
        self.type_editor.setFocus()
        self.editing_changed.emit(True)
        return True

    def cancel_edit(self) -> None:
        if self._details is not None:
            self._set_editor_value(
                self._details.summary.document_type
            )
        self.finish_edit()

    def finish_edit(self) -> None:
        was_editing = self._editing
        self._editing = False
        self.type_editor.hide()
        self.save_button.hide()
        self.cancel_button.hide()
        self.unsaved_label.hide()
        self.edit_button.setVisible(self._details is not None)
        if was_editing:
            self.editing_changed.emit(False)

    def show_validation_error(self, message: str) -> None:
        self.unsaved_label.setText(message)
        self.unsaved_label.show()

    def _set_editor_value(self, document_type: str) -> None:
        index = self.type_editor.findData(document_type)
        self.type_editor.blockSignals(True)
        self.type_editor.setCurrentIndex(max(0, index))
        self.type_editor.blockSignals(False)

    def _draft_changed(self, _index: int) -> None:
        if not self._editing:
            return
        self.unsaved_label.setText("Alterações não salvas")
        self.unsaved_label.setVisible(self.has_unsaved_changes)

    def _request_save(self) -> None:
        document_type = self.type_editor.currentData()
        if not isinstance(document_type, str):
            self.show_validation_error(
                "Selecione um tipo documental válido."
            )
            return
        self.save_requested.emit(document_type)
