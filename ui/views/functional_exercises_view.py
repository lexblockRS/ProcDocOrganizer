"""Consulta passiva de exercícios funcionais e sua rastreabilidade."""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QAbstractItemView,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QSplitter,
    QVBoxLayout,
    QWidget,
)


class FunctionalExercisesView(QWidget):
    exercise_selected = Signal(str)
    open_assignment_requested = Signal(str)
    refresh_requested = Signal()
    create_activity_requested = Signal()
    new_requested = Signal()
    edit_requested = Signal()
    delete_requested = Signal()

    def __init__(self):
        super().__init__()
        self.items = ()
        title = QLabel("Exercícios funcionais")
        font = title.font()
        font.setBold(True)
        title.setFont(font)
        self.message_label = QLabel()
        self.message_label.setWordWrap(True)
        self.list_widget = QListWidget()
        self.list_widget.setSelectionMode(
            QAbstractItemView.SelectionMode.ExtendedSelection
        )
        self.list_widget.setAccessibleName("Exercícios funcionais")
        details_widget = QWidget()
        form = QFormLayout(details_widget)
        self.details = {}
        for key, label in (
            ("person", "Pessoa"),
            ("type", "Tipo"),
            ("role", "Função"),
            ("context", "Contexto"),
            ("period", "Período"),
            ("status", "Estado"),
            ("reference", "Referência administrativa"),
        ):
            value = QLabel()
            value.setWordWrap(True)
            value.setTextInteractionFlags(
                Qt.TextInteractionFlag.TextSelectableByMouse
            )
            self.details[key] = value
            form.addRow(f"{label}:", value)
        self.related_list = QListWidget()
        self.related_list.setAccessibleName(
            "Interpretações relacionadas"
        )
        form.addRow("Interpretações:", self.related_list)
        self.open_assignment_button = QPushButton(
            "Abrir interpretação relacionada"
        )
        self.open_assignment_button.setEnabled(False)
        self.open_assignment_button.clicked.connect(
            self._open_assignment
        )
        self.refresh_button = QPushButton("Atualizar")
        self.refresh_button.clicked.connect(self.refresh_requested)
        actions = QHBoxLayout()
        self.new_button = QPushButton("Novo exercício")
        self.edit_button = QPushButton("Editar")
        self.delete_button = QPushButton("Excluir")
        self.new_button.clicked.connect(self.new_requested)
        self.edit_button.clicked.connect(self.edit_requested)
        self.delete_button.clicked.connect(self.delete_requested)
        self.edit_button.setEnabled(False)
        self.delete_button.setEnabled(False)
        self.create_activity_button = QPushButton(
            "Nova atividade funcional"
        )
        self.create_activity_button.setEnabled(False)
        self.create_activity_button.clicked.connect(
            self.create_activity_requested
        )
        actions.addWidget(self.new_button)
        actions.addWidget(self.edit_button)
        actions.addWidget(self.delete_button)
        actions.addWidget(self.create_activity_button)
        actions.addWidget(self.open_assignment_button)
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
        self.related_list.currentItemChanged.connect(
            lambda current, _previous: self.open_assignment_button.setEnabled(
                current is not None
            )
        )
        self.clear()

    def set_items(self, items):
        self.items = tuple(items)
        self.new_button.setEnabled(True)
        self.list_widget.blockSignals(True)
        self.list_widget.clear()
        for item in self.items:
            end = item.end_date.isoformat() if item.end_date else "aberto"
            row = QListWidgetItem(
                f"{item.person_id} · {item.role}\n"
                f"{item.exercise_type_label} · "
                f"{item.start_date.isoformat()} a {end}"
            )
            row.setData(Qt.ItemDataRole.UserRole, item.id)
            self.list_widget.addItem(row)
        self.list_widget.blockSignals(False)
        self.show_message(
            "" if self.items else "Nenhum exercício funcional."
        )
        self._selection_changed()

    def selected_exercise_ids(self):
        return tuple(
            item.data(Qt.ItemDataRole.UserRole)
            for item in self.list_widget.selectedItems()
        )

    def select_exercise(self, exercise_id):
        for index in range(self.list_widget.count()):
            row = self.list_widget.item(index)
            if row.data(Qt.ItemDataRole.UserRole) == exercise_id:
                self.list_widget.blockSignals(True)
                self.list_widget.setCurrentItem(row)
                self.list_widget.blockSignals(False)
                return True
        return False

    def set_details(self, exercise, related):
        self.related_list.clear()
        if exercise is None:
            for label in self.details.values():
                label.clear()
            self.open_assignment_button.setEnabled(False)
            self.edit_button.setEnabled(False)
            self.delete_button.setEnabled(False)
            return
        self.edit_button.setEnabled(True)
        self.delete_button.setEnabled(True)
        end = exercise.end_date.isoformat() if exercise.end_date else "aberto"
        values = {
            "person": exercise.person_id,
            "type": (
                f"{exercise.exercise_type_label} "
                f"({exercise.exercise_type_code})"
            ),
            "role": exercise.role,
            "context": " — ".join(filter(None, (
                exercise.context_organization,
                exercise.context_unit,
            ))),
            "period": f"{exercise.start_date.isoformat()} a {end}",
            "status": exercise.status,
            "reference": exercise.context_reference or "não informada",
        }
        for key, value in values.items():
            self.details[key].setText(value)
        for assignment, evidence in related:
            if evidence is None:
                source = "Evidence/fonte indisponível"
            else:
                source = (
                    f"Evidence {evidence.id} · "
                    f"documento {evidence.document_identity} · "
                    f"página {evidence.page_number or 'não informada'} · "
                    f"trecho: {evidence.source_snippet or 'não informado'}"
                )
            row = QListWidgetItem(
                f"{assignment.person_id} · {assignment.role} · {source}"
            )
            row.setData(Qt.ItemDataRole.UserRole, assignment.id)
            self.related_list.addItem(row)

    def show_loading(self):
        self.show_message("Carregando exercícios funcionais...")

    def show_message(self, message):
        self.message_label.setText(message)

    def show_error(self, message):
        self.show_message(message)

    def clear(self):
        self.items = ()
        self.list_widget.clear()
        self.set_details(None, ())
        self.show_message("Nenhum projeto RSC aberto.")
        self.create_activity_button.setEnabled(False)
        self.new_button.setEnabled(False)
        self.edit_button.setEnabled(False)
        self.delete_button.setEnabled(False)

    def _selected(self, current, _previous):
        if current is not None:
            self.exercise_selected.emit(
                current.data(Qt.ItemDataRole.UserRole)
            )

    def _open_assignment(self):
        current = self.related_list.currentItem()
        if current is not None:
            self.open_assignment_requested.emit(
                current.data(Qt.ItemDataRole.UserRole)
            )

    def _selection_changed(self):
        has_selection = bool(self.list_widget.selectedItems())
        self.create_activity_button.setEnabled(has_selection)
        self.edit_button.setEnabled(has_selection)
        self.delete_button.setEnabled(has_selection)
