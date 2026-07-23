"""Composição visual do gerenciamento de evidências."""

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QGroupBox, QHBoxLayout, QLabel, QPushButton, QSplitter, QVBoxLayout, QWidget,
)

from models import EvidenceDraft
from ui.widgets.evidence_editor_widget import EvidenceEditorWidget
from ui.widgets.evidence_list_widget import EvidenceListWidget
from ui.widgets.evidence_source_status_widget import EvidenceSourceStatusWidget


class EvidenceWorkspace(QWidget):
    new_requested = Signal()
    save_requested = Signal()
    cancel_requested = Signal()
    delete_requested = Signal()
    refresh_requested = Signal()
    evidence_selected = Signal(object)
    draft_changed = Signal(object)
    open_document_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.new_button = QPushButton("Nova evidência")
        self.save_button = QPushButton("Salvar")
        self.cancel_button = QPushButton("Cancelar")
        self.delete_button = QPushButton("Excluir")
        self.refresh_button = QPushButton("Atualizar lista")
        self.count_label = QLabel("0 evidências")
        self.dirty_label = QLabel("")
        self.message_label = QLabel("")
        self.message_label.setWordWrap(True)

        actions = QHBoxLayout()
        for widget in (
            self.new_button, self.save_button, self.cancel_button,
            self.delete_button, self.refresh_button,
        ):
            actions.addWidget(widget)
        actions.addStretch(1)
        actions.addWidget(self.dirty_label)
        actions.addWidget(self.count_label)

        self.list_widget = EvidenceListWidget()
        self.editor_widget = EvidenceEditorWidget()
        self.source_status_widget = EvidenceSourceStatusWidget()
        editor_group = QGroupBox("Editor")
        editor_layout = QVBoxLayout(editor_group)
        editor_layout.addWidget(self.editor_widget, 1)
        editor_layout.addWidget(self.source_status_widget)
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(self.list_widget)
        splitter.addWidget(editor_group)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)

        layout = QVBoxLayout(self)
        layout.addLayout(actions)
        layout.addWidget(self.message_label)
        layout.addWidget(splitter, 1)

        self.new_button.clicked.connect(self.new_requested)
        self.save_button.clicked.connect(self.save_requested)
        self.cancel_button.clicked.connect(self.cancel_requested)
        self.delete_button.clicked.connect(self.delete_requested)
        self.refresh_button.clicked.connect(self.refresh_requested)
        self.list_widget.evidence_selected.connect(self.evidence_selected)
        self.editor_widget.draft_changed.connect(self.draft_changed)
        QShortcut(QKeySequence.StandardKey.Save, self).activated.connect(self.save_requested)
        QShortcut(QKeySequence(Qt.Key.Key_Escape), self).activated.connect(self.cancel_requested)
        self.clear()

    def set_evidences(self, evidences, statuses=None) -> None:
        self.list_widget.set_evidences(evidences, statuses)
        count = len(tuple(evidences))
        self.count_label.setText(f"{count} evidência{'s' if count != 1 else ''}")

    def set_draft(
        self, draft: EvidenceDraft, creating=False, source_locked=False
    ) -> None:
        self.editor_widget.set_draft(draft, creating and not source_locked)

    def set_source_status(self, status) -> None:
        self.source_status_widget.set_status(status)

    def select_evidence(self, evidence_id) -> None:
        self.list_widget.select_evidence(evidence_id)

    def set_editor_state(self, mode, dirty: bool, minimally_valid: bool) -> None:
        mode_value = getattr(mode, "value", mode)
        creating = mode_value == "creating"
        active = mode_value in ("creating", "viewing", "editing")
        selected = mode_value in ("viewing", "editing")
        self.editor_widget.set_editable(active, creating)
        self.save_button.setEnabled(dirty and minimally_valid)
        self.cancel_button.setEnabled(dirty or creating)
        self.delete_button.setEnabled(selected)
        self.new_button.setEnabled(True)
        self.dirty_label.setText("Alterações não salvas" if dirty else "")

    def _apply_editor_projection(
        self,
        mode,
        dirty,
        minimally_valid,
        *,
        draft,
        source_status,
        source_locked,
        editor_enabled,
        identity_editable,
        save_enabled,
        cancel_enabled,
        delete_enabled,
    ) -> None:
        self.editor_widget.set_draft(draft, identity_editable)
        self.source_status_widget.set_status(source_status)
        self.editor_widget.set_editable(
            editor_enabled, identity_editable
        )
        self.save_button.setEnabled(save_enabled)
        self.cancel_button.setEnabled(cancel_enabled)
        self.delete_button.setEnabled(delete_enabled)
        self.new_button.setEnabled(True)
        self.dirty_label.setText("Alterações não salvas" if dirty else "")

    def show_message(self, message: str) -> None:
        self.message_label.setText(message)

    def focus_title(self) -> None:
        self.editor_widget.focus_title()

    def clear(self) -> None:
        self.list_widget.clear()
        self.editor_widget.clear()
        self.editor_widget.set_editable(False)
        self.set_source_status(None)
        self.count_label.setText("0 evidências")
        self.dirty_label.clear()
        self.message_label.clear()
        self.set_editor_state("empty", False, False)

    def on_project_opened(self, _project) -> None:
        pass

    def on_project_closed(self) -> None:
        self.clear()
