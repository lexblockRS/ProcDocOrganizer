"""Consulta passiva das interpretações funcionais."""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QAbstractItemView,
    QFormLayout, QHBoxLayout, QLabel, QListWidget, QListWidgetItem,
    QPushButton, QSplitter, QVBoxLayout, QWidget,
)


class FunctionalAssignmentsView(QWidget):
    assignment_selected = Signal(str)
    create_exercise_requested = Signal()
    create_activity_requested = Signal()
    open_source_requested = Signal()
    refresh_requested = Signal()
    new_requested = Signal()
    edit_requested = Signal()
    delete_requested = Signal()
    advance_requested = Signal()

    def __init__(self):
        super().__init__()
        self.items = ()
        title = QLabel("Interpretações funcionais")
        font = title.font()
        font.setBold(True)
        title.setFont(font)
        self.message_label = QLabel()
        self.message_label.setWordWrap(True)
        self.list_widget = QListWidget()
        self.list_widget.setSelectionMode(
            QAbstractItemView.SelectionMode.ExtendedSelection
        )
        self.list_widget.setAccessibleName("Interpretações funcionais")
        self.details = {}
        details_widget = QWidget()
        form = QFormLayout(details_widget)
        for key, label in (
            ("person", "Pessoa"),
            ("type", "Tipo"),
            ("role", "Função"),
            ("organization", "Organização"),
            ("period", "Período"),
            ("status", "Estado"),
            ("project", "Projeto"),
            ("source", "Evidence de origem"),
            ("document", "Documento"),
            ("page", "Página"),
            ("snippet", "Trecho"),
            ("created", "Criação da interpretação"),
        ):
            value = QLabel()
            value.setWordWrap(True)
            value.setTextInteractionFlags(
                Qt.TextInteractionFlag.TextSelectableByMouse
            )
            self.details[key] = value
            form.addRow(f"{label}:", value)
        self.open_source_button = QPushButton("Voltar para Evidence")
        self.open_source_button.setEnabled(False)
        self.open_source_button.clicked.connect(self.open_source_requested)
        self.refresh_button = QPushButton("Atualizar")
        self.refresh_button.clicked.connect(self.refresh_requested)
        self.new_button = QPushButton("Nova interpretação")
        self.new_button.clicked.connect(self.new_requested)
        self.edit_button = QPushButton("Editar")
        self.edit_button.clicked.connect(self.edit_requested)
        self.delete_button = QPushButton("Excluir")
        self.delete_button.clicked.connect(self.delete_requested)
        self.advance_button = QPushButton("Avançar estado")
        self.advance_button.clicked.connect(self.advance_requested)
        self.create_exercise_button = QPushButton(
            "Criar exercício funcional"
        )
        self.create_exercise_button.setEnabled(False)
        self.create_exercise_button.clicked.connect(
            self.create_exercise_requested
        )
        self.create_activity_button = QPushButton(
            "Nova atividade funcional"
        )
        self.create_activity_button.setEnabled(False)
        self.create_activity_button.clicked.connect(
            self.create_activity_requested
        )
        actions = QHBoxLayout()
        actions.addWidget(self.new_button)
        actions.addWidget(self.edit_button)
        actions.addWidget(self.delete_button)
        actions.addWidget(self.advance_button)
        actions.addWidget(self.create_exercise_button)
        actions.addWidget(self.create_activity_button)
        actions.addWidget(self.open_source_button)
        actions.addWidget(self.refresh_button)
        actions.addStretch(1)
        splitter = QSplitter()
        splitter.addWidget(self.list_widget)
        splitter.addWidget(details_widget)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)
        layout = QVBoxLayout(self)
        layout.addWidget(title)
        layout.addWidget(self.message_label)
        layout.addLayout(actions)
        layout.addWidget(splitter, 1)
        self.list_widget.currentItemChanged.connect(self._selected)
        self.list_widget.itemSelectionChanged.connect(
            self._selection_changed
        )
        self.clear()

    def set_items(self, items):
        self.items = tuple(items)
        self.list_widget.blockSignals(True)
        self.list_widget.clear()
        for item in self.items:
            start = item.start_date.isoformat() if item.start_date else "—"
            end = item.end_date.isoformat() if item.end_date else "—"
            row = QListWidgetItem(
                f"{item.person_id} · {item.role} — {item.organization}"
                f"{' / ' + item.unit if item.unit else ''}\n"
                f"{item.exercise_type_label} · {start} a {end} · "
                f"Evidence {item.source_evidence_reference}"
            )
            row.setData(Qt.ItemDataRole.UserRole, item.id)
            self.list_widget.addItem(row)
        self.list_widget.blockSignals(False)
        self.show_message(
            "" if self.items else "Nenhuma interpretação funcional."
        )
        self._selection_changed()

    def selected_assignment_ids(self):
        return tuple(
            item.data(Qt.ItemDataRole.UserRole)
            for item in self.list_widget.selectedItems()
        )

    def select_assignment(self, assignment_id):
        for index in range(self.list_widget.count()):
            item = self.list_widget.item(index)
            if item.data(Qt.ItemDataRole.UserRole) == assignment_id:
                self.list_widget.blockSignals(True)
                self.list_widget.setCurrentItem(item)
                self.list_widget.blockSignals(False)
                return True
        return False

    def set_details(self, assignment, evidence, project_name):
        if assignment is None:
            for label in self.details.values():
                label.clear()
            self.open_source_button.setEnabled(False)
            self.edit_button.setEnabled(False)
            self.delete_button.setEnabled(False)
            self.advance_button.setEnabled(False)
            self._selection_changed()
            return
        start = assignment.start_date.isoformat() if assignment.start_date else "—"
        end = assignment.end_date.isoformat() if assignment.end_date else "—"
        values = {
            "person": assignment.person_id,
            "type": (
                f"{assignment.exercise_type_label} "
                f"({assignment.exercise_type_code})"
            ),
            "role": assignment.role,
            "organization": " — ".join(filter(None, (
                assignment.organization, assignment.unit,
            ))),
            "period": f"{start} a {end}",
            "status": assignment.status,
            "project": project_name,
            "source": assignment.source_evidence_reference,
            "document": (
                evidence.document_identity if evidence else "Fonte indisponível"
            ),
            "page": (
                str(evidence.page_number or "não informada")
                if evidence else "não disponível"
            ),
            "snippet": (
                evidence.source_snippet or "não informado"
                if evidence else "não disponível"
            ),
            "created": (
                "Não registrada pelo modelo atual"
            ),
        }
        for key, value in values.items():
            self.details[key].setText(value)
        self.open_source_button.setEnabled(evidence is not None)
        self.edit_button.setEnabled(True)
        self.delete_button.setEnabled(True)
        self.advance_button.setEnabled(assignment.status != "linked")

    def show_message(self, message):
        self.message_label.setText(message)

    def show_error(self, message):
        self.show_message(message)

    def clear(self):
        self.items = ()
        self.list_widget.clear()
        self.set_details(None, None, None)
        self.show_message("Nenhum projeto RSC aberto.")
        self.create_exercise_button.setEnabled(False)
        self.create_activity_button.setEnabled(False)

    def _selected(self, current, _previous):
        if current is not None:
            self.assignment_selected.emit(
                current.data(Qt.ItemDataRole.UserRole)
            )

    def _selection_changed(self):
        self.create_exercise_button.setEnabled(
            bool(self.list_widget.selectedItems())
        )
        self.create_activity_button.setEnabled(
            bool(self.list_widget.selectedItems())
        )
