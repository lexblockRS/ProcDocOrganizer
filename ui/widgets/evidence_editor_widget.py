"""Formulário visual desacoplado para editar EvidenceDraft."""

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QFormLayout, QLineEdit, QPlainTextEdit, QSpinBox, QWidget,
)

from models import EvidenceDraft


class EvidenceEditorWidget(QWidget):
    draft_changed = Signal(object)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._updating = False
        self._evidence_id = None
        self.title_edit = QLineEdit()
        self.sha_edit = QLineEdit()
        self.sha_edit.setMaxLength(64)
        self.sha_edit.setPlaceholderText("SHA-256 do documento")
        self.page_edit = QSpinBox()
        self.page_edit.setRange(0, 999999)
        self.page_edit.setSpecialValueText("Não informada")
        self.category_edit = QLineEdit()
        self.snippet_edit = QPlainTextEdit()
        self.notes_edit = QPlainTextEdit()
        self.start_date_edit = QLineEdit()
        self.end_date_edit = QLineEdit()
        self.start_date_edit.setPlaceholderText("AAAA-MM-DD")
        self.end_date_edit.setPlaceholderText("AAAA-MM-DD")
        self.snippet_edit.setTabChangesFocus(True)
        self.notes_edit.setTabChangesFocus(True)

        layout = QFormLayout(self)
        layout.addRow("Título:", self.title_edit)
        layout.addRow("Documento SHA-256:", self.sha_edit)
        layout.addRow("Página:", self.page_edit)
        layout.addRow("Categoria:", self.category_edit)
        layout.addRow("Trecho documental:", self.snippet_edit)
        layout.addRow("Observações:", self.notes_edit)
        layout.addRow("Data inicial:", self.start_date_edit)
        layout.addRow("Data final:", self.end_date_edit)

        for field in (
            self.title_edit, self.sha_edit, self.category_edit,
            self.start_date_edit, self.end_date_edit,
        ):
            field.textChanged.connect(self._emit_draft)
        self.page_edit.valueChanged.connect(self._emit_draft)
        self.snippet_edit.textChanged.connect(self._emit_draft)
        self.notes_edit.textChanged.connect(self._emit_draft)
        self.set_editable(False)

    def set_draft(self, draft: EvidenceDraft, creating: bool = False) -> None:
        self._updating = True
        try:
            self._evidence_id = draft.evidence_id
            self.title_edit.setText(draft.title)
            self.sha_edit.setText(draft.document_identity)
            self.page_edit.setValue(draft.page_number or 0)
            self.category_edit.setText(draft.category)
            self.snippet_edit.setPlainText(draft.source_snippet)
            self.notes_edit.setPlainText(draft.user_notes)
            self.start_date_edit.setText(draft.start_date)
            self.end_date_edit.setText(draft.end_date)
            self.sha_edit.setReadOnly(not creating)
        finally:
            self._updating = False

    def draft(self) -> EvidenceDraft:
        return EvidenceDraft(
            evidence_id=self._evidence_id,
            document_identity=self.sha_edit.text(),
            page_number=self.page_edit.value() or None,
            title=self.title_edit.text(),
            source_snippet=self.snippet_edit.toPlainText(),
            user_notes=self.notes_edit.toPlainText(),
            category=self.category_edit.text(),
            start_date=self.start_date_edit.text(),
            end_date=self.end_date_edit.text(),
        )

    def clear(self) -> None:
        self.set_draft(EvidenceDraft.empty(), creating=True)

    def set_editable(self, editable: bool, creating: bool = False) -> None:
        self.setEnabled(editable)
        self.sha_edit.setReadOnly(not creating)

    def focus_title(self) -> None:
        self.title_edit.setFocus()

    def _emit_draft(self, *_args) -> None:
        if not self._updating:
            self.draft_changed.emit(self.draft())
