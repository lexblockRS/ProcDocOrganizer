"""Visualização passiva das atividades profissionais."""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QSplitter,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from presentation.activities import ActivitiesProjection, ActivitiesViewState
from ui.widgets import ResponsiveCardGrid, SummaryCard


class ActivitiesView(QWidget):
    """Renderiza projeções sem consultar sessão, serviços ou repositories."""

    open_project_requested = Signal()
    refresh_requested = Signal()
    retry_requested = Signal()
    activity_selected = Signal(str)
    open_assignment_requested = Signal(str)
    open_exercise_requested = Signal(str)

    def __init__(self):
        super().__init__()
        self._build_ui()
        self.set_projection(ActivitiesProjection())

    def _build_ui(self):
        self.state_stack = QStackedWidget()
        self.no_project_page = self._state_page(
            "Atividades",
            "Nenhum projeto está aberto.",
        )
        self.open_project_button = QPushButton("Abrir projeto")
        self.open_project_button.setAccessibleName("Abrir projeto")
        self.open_project_button.setToolTip(
            "Abrir um projeto existente"
        )
        self.open_project_button.clicked.connect(
            self.open_project_requested
        )
        self.no_project_page.layout().addWidget(
            self.open_project_button,
            alignment=Qt.AlignmentFlag.AlignCenter,
        )

        self.loading_page = self._state_page(
            "Atividades", "Carregando atividades..."
        )
        self.loading_message_label = self.loading_page.layout().itemAt(
            1
        ).widget()
        self.loading_progress = QProgressBar()
        self.loading_progress.setRange(0, 0)
        self.loading_progress.setTextVisible(False)
        self.loading_progress.setAccessibleName("Carregando atividades")
        self.loading_page.layout().addWidget(self.loading_progress)

        self.empty_page = self._state_page(
            "Atividades",
            "Ainda não existem atividades neste projeto.\n"
            "Atividades acompanham lembranças profissionais até sua "
            "comprovação.",
        )
        self.empty_project_label = QLabel()
        self.empty_project_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty_page.layout().insertWidget(1, self.empty_project_label)
        self.new_activity_button = QPushButton("Nova atividade funcional")
        self.new_activity_button.setEnabled(False)
        self.new_activity_button.setToolTip(
            "Disponível na próxima etapa"
        )
        self.new_activity_button.setAccessibleName("Nova atividade")
        self.empty_page.layout().addWidget(
            self.new_activity_button,
            alignment=Qt.AlignmentFlag.AlignCenter,
        )

        self.ready_page = self._build_ready_page()
        self.error_page = self._state_page(
            "Atividades", "Não foi possível carregar as atividades."
        )
        self.error_title_label = self.error_page.layout().itemAt(0).widget()
        self.error_message_label = self.error_page.layout().itemAt(1).widget()
        self.retry_button = QPushButton("Tentar novamente")
        self.retry_button.setToolTip("Recarregar atividades")
        self.retry_button.setAccessibleName("Tentar novamente")
        self.retry_button.clicked.connect(self.retry_requested)
        self.error_page.layout().addWidget(
            self.retry_button,
            alignment=Qt.AlignmentFlag.AlignCenter,
        )

        for page in (
            self.no_project_page,
            self.loading_page,
            self.empty_page,
            self.ready_page,
            self.error_page,
        ):
            self.state_stack.addWidget(page)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.state_stack)

    @staticmethod
    def _state_page(title, message):
        page = QWidget()
        title_label = QLabel(title)
        font = title_label.font()
        font.setBold(True)
        title_label.setFont(font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        message_label = QLabel(message)
        message_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        message_label.setWordWrap(True)
        layout = QVBoxLayout(page)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        layout.addWidget(message_label)
        return page

    def _build_ready_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(24, 20, 24, 24)

        header = QHBoxLayout()
        titles = QVBoxLayout()
        title = QLabel("Atividades")
        font = title.font()
        font.setBold(True)
        title.setFont(font)
        self.project_name_label = QLabel()
        self.total_label = QLabel()
        titles.addWidget(title)
        titles.addWidget(self.project_name_label)
        titles.addWidget(self.total_label)
        self.refresh_button = QPushButton("Atualizar")
        self.refresh_button.setToolTip("Atualizar lista de atividades")
        self.refresh_button.setAccessibleName("Atualizar atividades")
        self.refresh_button.clicked.connect(self.refresh_requested)
        header.addLayout(titles)
        header.addStretch(1)
        header.addWidget(self.refresh_button)
        layout.addLayout(header)

        self.summary_cards = {
            "remembered": SummaryCard("Lembradas"),
            "investigating": SummaryCard("Em investigação"),
            "partial": SummaryCard("Parcialmente comprovadas"),
            "proven": SummaryCard("Comprovadas"),
        }
        summary = ResponsiveCardGrid()
        summary.set_cards(self.summary_cards.values())
        layout.addWidget(summary)

        self.activity_list = QListWidget()
        self.activity_list.setAccessibleName("Lista de atividades")
        self.activity_list.setToolTip(
            "Selecione uma atividade para visualizar os detalhes"
        )
        self.activity_list.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self.activity_list.currentItemChanged.connect(
            self._selection_changed
        )

        details = QWidget()
        details.setAccessibleName("Detalhes da atividade")
        details_layout = QVBoxLayout(details)
        details_title = QLabel("Detalhes da atividade")
        details_font = details_title.font()
        details_font.setBold(True)
        details_title.setFont(details_font)
        self.details_description_label = QLabel()
        self.details_description_label.setWordWrap(True)
        self.details_state_label = QLabel()
        self.details_counts_label = QLabel()
        self.details_id_label = QLabel()
        self.details_id_label.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )
        self.evidence_ids_label = QLabel()
        self.evidence_ids_label.setWordWrap(True)
        self.evidence_ids_label.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )
        self.exercise_ids_label = QLabel()
        self.exercise_ids_label.setWordWrap(True)
        self.exercise_ids_label.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )
        self.exercise_list = QListWidget()
        self.exercise_list.setAccessibleName(
            "Exercícios funcionais da atividade"
        )
        self.open_exercise_button = QPushButton(
            "Abrir exercício funcional"
        )
        self.open_exercise_button.setEnabled(False)
        self.open_exercise_button.clicked.connect(self._open_exercise)
        self.exercise_list.currentItemChanged.connect(
            lambda current, _previous:
            self.open_exercise_button.setEnabled(
                current is not None
                and bool(current.data(Qt.ItemDataRole.UserRole + 1))
            )
        )
        self.related_list = QListWidget()
        self.related_list.setAccessibleName(
            "Interpretações da atividade"
        )
        self.open_assignment_button = QPushButton("Abrir interpretação")
        self.open_assignment_button.setEnabled(False)
        self.open_assignment_button.clicked.connect(self._open_assignment)
        self.related_list.currentItemChanged.connect(
            lambda current, _previous:
            self.open_assignment_button.setEnabled(
                current is not None
                and bool(current.data(Qt.ItemDataRole.UserRole + 1))
            )
        )
        for widget in (
            details_title,
            self.details_description_label,
            self.details_state_label,
            self.details_counts_label,
            self.details_id_label,
            self.evidence_ids_label,
            self.exercise_ids_label,
            self.exercise_list,
            self.open_exercise_button,
            self.related_list,
            self.open_assignment_button,
        ):
            details_layout.addWidget(widget)
        details_layout.addStretch(1)
        details_scroll = QScrollArea()
        details_scroll.setWidgetResizable(True)
        details_scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        details_scroll.setWidget(details)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setChildrenCollapsible(False)
        splitter.addWidget(self.activity_list)
        splitter.addWidget(details_scroll)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)
        layout.addWidget(splitter, 1)
        self.setTabOrder(self.refresh_button, self.activity_list)
        return page

    def set_projection(self, projection):
        if projection.state is ActivitiesViewState.NO_PROJECT:
            self.state_stack.setCurrentWidget(self.no_project_page)
        elif projection.state is ActivitiesViewState.LOADING:
            self.loading_message_label.setText(
                f"Carregando atividades de "
                f"{projection.project_name or 'projeto'}..."
            )
            self.state_stack.setCurrentWidget(self.loading_page)
        elif projection.state is ActivitiesViewState.EMPTY:
            self.empty_project_label.setText(
                projection.project_name or ""
            )
            self.state_stack.setCurrentWidget(self.empty_page)
        elif projection.state is ActivitiesViewState.ERROR:
            self.error_title_label.setText(
                projection.project_name or "Atividades"
            )
            self.error_message_label.setText(
                projection.error_message
                or "Não foi possível carregar as atividades."
            )
            self.state_stack.setCurrentWidget(self.error_page)
        else:
            self._render_ready(projection)
            self.state_stack.setCurrentWidget(self.ready_page)

    def _render_ready(self, projection):
        self.project_name_label.setText(projection.project_name or "")
        self.total_label.setText(
            f"{projection.total} atividade(s)"
        )
        values = (
            ("remembered", projection.remembered_count),
            ("investigating", projection.investigating_count),
            ("partial", projection.partially_proven_count),
            ("proven", projection.proven_count),
        )
        for key, value in values:
            self.summary_cards[key].set_value(value)

        self.activity_list.blockSignals(True)
        self.activity_list.clear()
        selected_item = None
        for item in projection.items:
            widget_item = QListWidgetItem(
                f"{item.description}\n{item.state_label} · "
                f"{item.evidence_count} evidência(s) · "
                f"{item.exercise_count} exercício(s)"
            )
            widget_item.setData(
                Qt.ItemDataRole.UserRole, item.activity_id
            )
            widget_item.setToolTip(item.description)
            self.activity_list.addItem(widget_item)
            if item.is_selected:
                selected_item = widget_item
        self.activity_list.setCurrentItem(selected_item)
        self.activity_list.blockSignals(False)
        self._render_details(projection.selected_activity)

    def _render_details(self, details):
        if details is None:
            return
        self.details_description_label.setText(details.description)
        self.details_state_label.setText(
            f"Estado: {details.state_label}"
        )
        self.details_counts_label.setText(
            f"Evidências: {details.evidence_count} · "
            f"Exercícios: {details.exercise_count}"
        )
        self.details_id_label.setText(
            f"Identificador: {details.activity_id}"
        )
        self.evidence_ids_label.setText(
            "Interpretações funcionais relacionadas diretamente:\n"
            + ("\n".join(details.evidence_ids) or "Nenhuma")
        )
        self.exercise_ids_label.setText(
            "Exercícios relacionados:\n"
            + ("\n".join(details.exercise_ids) or "Nenhum")
        )
        self.exercise_list.clear()
        for item in details.related_exercises:
            if item.available:
                context = " — ".join(filter(None, (
                    item.organization, item.unit,
                )))
                text = (
                    f"{item.person_id} · {item.role}\n"
                    f"{context} · {item.period} · {item.status} · "
                    f"{item.assignment_count} interpretação(ões)\n"
                    f"ID: {item.exercise_id}"
                )
            else:
                text = (
                    "Exercício funcional indisponível\n"
                    f"ID histórico: {item.exercise_id}\n"
                    f"{item.unavailable_reason}"
                )
            row = QListWidgetItem(text)
            row.setData(Qt.ItemDataRole.UserRole, item.exercise_id)
            row.setData(
                Qt.ItemDataRole.UserRole + 1, item.available
            )
            self.exercise_list.addItem(row)
        self.related_list.clear()
        for item in details.related_interpretations:
            if item.assignment_available:
                source = (
                    f"{item.document_identity} · página "
                    f"{item.page_number or 'não informada'} · "
                    f"{item.snippet or 'trecho não informado'}"
                    if item.source_available
                    else item.unavailable_reason
                )
                text = (
                    f"{item.person_id} · {item.role}\n"
                    f"Evidence de origem {item.evidence_id} · {source}\n"
                    f"ID da interpretação: {item.assignment_id}"
                )
            else:
                text = (
                    "Interpretação funcional indisponível\n"
                    f"ID histórico: {item.assignment_id}\n"
                    f"{item.unavailable_reason}"
                )
            row = QListWidgetItem(text)
            row.setData(Qt.ItemDataRole.UserRole, item.assignment_id)
            row.setData(
                Qt.ItemDataRole.UserRole + 1,
                item.assignment_available,
            )
            self.related_list.addItem(row)

    def _selection_changed(self, current, _previous):
        if current is not None:
            self.activity_selected.emit(
                current.data(Qt.ItemDataRole.UserRole)
            )

    def _open_assignment(self):
        current = self.related_list.currentItem()
        if (
            current is not None
            and current.data(Qt.ItemDataRole.UserRole + 1)
        ):
            self.open_assignment_requested.emit(
                current.data(Qt.ItemDataRole.UserRole)
            )

    def _open_exercise(self):
        current = self.exercise_list.currentItem()
        if (
            current is not None
            and current.data(Qt.ItemDataRole.UserRole + 1)
        ):
            self.open_exercise_requested.emit(
                current.data(Qt.ItemDataRole.UserRole)
            )
