"""Dashboard visual do projeto."""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QScrollArea,
    QStackedWidget,
    QStyle,
    QVBoxLayout,
    QWidget,
)

from core.contribution_manager import ContributionManager
from presentation.dashboard import DashboardProjection, DashboardState
from ui.platform_sdk_materializer import (
    materialize_dashboard_component,
)
from ui.widgets import (
    DashboardHeader,
    DashboardSection,
    ResponsiveCardGrid,
    ShortcutButton,
    SummaryCard,
)

PAGE_MARGIN = 24
SECTION_GAP = 18
STATE_GAP = 12


def _title_font(widget, scale=1.4):
    font = widget.font()
    point_size = font.pointSizeF()
    if point_size > 0:
        font.setPointSizeF(point_size * scale)
    font.setBold(True)
    return font


class HomeView(QWidget):
    """Apresenta exclusivamente o estado projetado do Dashboard."""

    new_project_requested = Signal()
    open_project_requested = Signal()
    documents_requested = Signal()
    search_requested = Signal()
    evidences_requested = Signal()
    import_documents_requested = Signal()
    process_documents_requested = Signal()
    retry_requested = Signal()

    def __init__(
        self,
        contribution_manager: ContributionManager | None = None,
    ):
        super().__init__()
        self.contribution_manager = (
            contribution_manager
            if contribution_manager is not None
            else self._compatibility_contribution_manager()
        )
        self._build_ui()
        self._install_dashboard_contributions()
        self.set_projection(DashboardProjection())

    def _build_ui(self) -> None:
        self.state_stack = QStackedWidget()
        self.no_project_page = self._build_no_project_page()
        self.loading_page = self._build_loading_page()
        self.ready_page = self._build_ready_page()
        self.error_page = self._build_error_page()
        for page in (
            self.no_project_page,
            self.loading_page,
            self.ready_page,
            self.error_page,
        ):
            self.state_stack.addWidget(page)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.state_stack)

    def _build_no_project_page(self) -> QWidget:
        page = QWidget()
        icon = QLabel()
        icon.setPixmap(
            self.style().standardIcon(
                QStyle.StandardPixmap.SP_DirHomeIcon
            ).pixmap(48, 48)
        )
        icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon.setAccessibleName("Projeto")
        self.no_project_title_label = QLabel("Nenhum projeto aberto")
        self.no_project_title_label.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )
        self.no_project_title_label.setFont(
            _title_font(self.no_project_title_label)
        )
        self.no_project_message_label = QLabel(
            "Crie um projeto ou abra um existente para começar."
        )
        self.no_project_message_label.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )
        self.no_project_message_label.setWordWrap(True)

        self.new_project_button = ShortcutButton(
            "Novo Projeto", "Criar um novo projeto"
        )
        self.new_project_button.setDefault(True)
        self.open_project_button = ShortcutButton(
            "Abrir Projeto", "Abrir um projeto existente"
        )
        self.new_project_button.requested.connect(
            self.new_project_requested
        )
        self.open_project_button.requested.connect(
            self.open_project_requested
        )

        actions = QHBoxLayout()
        actions.addStretch(1)
        actions.addWidget(self.new_project_button)
        actions.addWidget(self.open_project_button)
        actions.addStretch(1)
        self.setTabOrder(
            self.new_project_button, self.open_project_button
        )

        layout = QVBoxLayout(page)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setContentsMargins(
            PAGE_MARGIN, PAGE_MARGIN, PAGE_MARGIN, PAGE_MARGIN
        )
        layout.setSpacing(STATE_GAP)
        layout.addWidget(icon)
        layout.addWidget(self.no_project_title_label)
        layout.addWidget(self.no_project_message_label)
        layout.addLayout(actions)
        return page

    def _build_loading_page(self) -> QWidget:
        page = QWidget()
        self.loading_label = QLabel("Carregando resumo do projeto...")
        self.loading_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.loading_progress = QProgressBar()
        self.loading_progress.setRange(0, 0)
        self.loading_progress.setTextVisible(False)
        self.loading_progress.setAccessibleName("Carregando Dashboard")
        self.loading_progress.setAccessibleDescription(
            "O resumo do projeto está sendo preparado"
        )
        self.loading_progress.setMaximumWidth(320)

        layout = QVBoxLayout(page)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setContentsMargins(
            PAGE_MARGIN, PAGE_MARGIN, PAGE_MARGIN, PAGE_MARGIN
        )
        layout.setSpacing(STATE_GAP)
        layout.addWidget(self.loading_label)
        layout.addWidget(
            self.loading_progress,
            alignment=Qt.AlignmentFlag.AlignCenter,
        )
        return page

    def _build_ready_page(self) -> QWidget:
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(
            PAGE_MARGIN, 20, PAGE_MARGIN, PAGE_MARGIN
        )
        layout.setSpacing(SECTION_GAP)

        self.dashboard_header = DashboardHeader()
        layout.addWidget(self.dashboard_header)

        self.summary_cards = {
            "documents": SummaryCard("Documentos"),
            "evidences": SummaryCard("Evidências"),
        }
        self.summary_grid = ResponsiveCardGrid()
        self.summary_grid.set_cards(self.summary_cards.values())
        self.summary_section = DashboardSection(
            "Resumo", self.summary_grid
        )
        layout.addWidget(self.summary_section)

        document_content = ResponsiveCardGrid()
        self.document_cards = {
            "total": SummaryCard("Total"),
            "processed": SummaryCard("Processados"),
            "pending": SummaryCard("Pendentes"),
            "ocr": SummaryCard("OCR necessário"),
            "failed": SummaryCard("Falhas"),
            "pages": SummaryCard("Páginas processadas"),
        }
        document_content.set_cards(self.document_cards.values())
        self.documents_section = DashboardSection(
            "Documentos", document_content
        )
        layout.addWidget(self.documents_section)

        self.evidence_total_card = SummaryCard("Total de evidências")
        self.evidences_section = DashboardSection(
            "Evidências", self.evidence_total_card
        )
        layout.addWidget(self.evidences_section)

        shortcuts_content = ResponsiveCardGrid()
        self.shortcut_buttons = {
            "documents": ShortcutButton(
                "Documentos", "Abrir o catálogo de documentos"
            ),
            "search": ShortcutButton(
                "Pesquisa", "Pesquisar nos documentos processados"
            ),
            "evidences": ShortcutButton(
                "Evidências", "Abrir o gerenciamento de evidências"
            ),
            "import": ShortcutButton(
                "Importar documentos", "Importar documentos para o projeto"
            ),
            "process": ShortcutButton(
                "Processar documentos",
                "Processar documentos pendentes",
            ),
        }
        shortcuts_content.set_cards(self.shortcut_buttons.values())
        self.shortcuts_section = DashboardSection(
            "Atalhos rápidos", shortcuts_content
        )
        layout.addWidget(self.shortcuts_section)
        layout.addStretch(1)

        signals = (
            ("documents", self.documents_requested),
            ("search", self.search_requested),
            ("evidences", self.evidences_requested),
            ("import", self.import_documents_requested),
            ("process", self.process_documents_requested),
        )
        for key, signal in signals:
            self.shortcut_buttons[key].requested.connect(signal)

        focus_order = list(self.shortcut_buttons.values())
        for current, following in zip(
            focus_order, focus_order[1:]
        ):
            self.setTabOrder(current, following)

        self.ready_scroll = QScrollArea()
        self.ready_scroll.setWidgetResizable(True)
        self.ready_scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self.ready_scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        self.ready_scroll.setWidget(content)

        page = QWidget()
        page_layout = QVBoxLayout(page)
        page_layout.setContentsMargins(0, 0, 0, 0)
        page_layout.addWidget(self.ready_scroll)
        self.ready_layout = layout
        return page

    def _install_dashboard_contributions(self) -> None:
        self._dashboard_widgets = []
        self._summary_contribution_widgets = []
        for contribution in (
            self.contribution_manager.dashboard_contributions()
        ):
            widget = materialize_dashboard_component(
                contribution.widget_factory()
            )
            if contribution.section == "summary":
                self._summary_contribution_widgets.append(widget)
                self.summary_grid.set_cards((
                    self.summary_cards["documents"],
                    self.summary_cards["evidences"],
                    *self._summary_contribution_widgets,
                ))
                key = contribution.metadata.get("summary_key")
                if isinstance(key, str):
                    self.summary_cards[key] = widget
            elif contribution.section == "content":
                index = self.ready_layout.indexOf(
                    self.shortcuts_section
                )
                self.ready_layout.insertWidget(index, widget)
            else:
                raise ValueError(
                    "Seção de Dashboard desconhecida: "
                    f"{contribution.section}."
                )
            attribute_name = contribution.metadata.get(
                "attribute_name"
            )
            if isinstance(attribute_name, str):
                setattr(self, attribute_name, widget)
            cards_attribute = contribution.metadata.get(
                "cards_attribute"
            )
            if isinstance(cards_attribute, str) and hasattr(widget, "cards"):
                setattr(self, cards_attribute, widget.cards)
            self._dashboard_widgets.append((contribution, widget))

    @staticmethod
    def _compatibility_contribution_manager():
        from ui.main_window_contributions import (
            create_compatibility_contribution_manager,
        )

        return create_compatibility_contribution_manager()

    def refresh_dashboard_contributions(self, session) -> None:
        for contribution, widget in self._dashboard_widgets:
            visibility = contribution.visibility
            visible = (
                visibility(session)
                if callable(visibility)
                else visibility
            )
            refresh = getattr(widget, "refresh_dashboard", None)
            if callable(refresh):
                refreshed = refresh(session)
                if refreshed is not None:
                    visible = visible and bool(refreshed)
            if contribution.section == "summary":
                self.summary_grid.set_card_visible(widget, visible)
            else:
                widget.setVisible(visible)

    def _build_error_page(self) -> QWidget:
        page = QWidget()
        error_icon = QLabel()
        error_icon.setPixmap(
            self.style().standardIcon(
                QStyle.StandardPixmap.SP_MessageBoxCritical
            ).pixmap(40, 40)
        )
        error_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        error_icon.setAccessibleName("Erro")
        self.error_title_label = QLabel("Não foi possível carregar o projeto")
        self.error_title_label.setFont(
            _title_font(self.error_title_label)
        )
        self.error_title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.error_message_label = QLabel()
        self.error_message_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.error_message_label.setWordWrap(True)
        self.retry_button = ShortcutButton(
            "Tentar novamente", "Recarregar o resumo do projeto"
        )
        self.retry_button.requested.connect(self.retry_requested)

        layout = QVBoxLayout(page)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setContentsMargins(
            PAGE_MARGIN, PAGE_MARGIN, PAGE_MARGIN, PAGE_MARGIN
        )
        layout.setSpacing(STATE_GAP)
        layout.addWidget(error_icon)
        layout.addWidget(self.error_title_label)
        layout.addWidget(self.error_message_label)
        layout.addWidget(
            self.retry_button,
            alignment=Qt.AlignmentFlag.AlignCenter,
        )
        return page

    def set_projection(self, projection: DashboardProjection) -> None:
        if projection.state == DashboardState.NO_PROJECT:
            self.state_stack.setCurrentWidget(self.no_project_page)
            return

        project = projection.project
        if projection.state == DashboardState.LOADING:
            project_name = project.project_name if project else "projeto"
            self.loading_label.setText(
                f"Carregando resumo de {project_name}..."
            )
            self.state_stack.setCurrentWidget(self.loading_page)
            return

        if projection.state == DashboardState.ERROR:
            project_name = project.project_name if project else "Projeto"
            self.error_title_label.setText(project_name)
            self.error_message_label.setText(
                projection.error_message
                or "Não foi possível carregar o resumo do projeto."
            )
            self.state_stack.setCurrentWidget(self.error_page)
            return

        self._render_ready(projection)
        self.state_stack.setCurrentWidget(self.ready_page)

    def _render_ready(self, projection: DashboardProjection) -> None:
        project = projection.project
        documents = projection.documents
        self.dashboard_header.set_values(
            project_name=project.project_name,
            application_name=project.application_name,
            project_path=project.project_path,
            created_at=project.created_at,
            last_opened_at=project.last_opened_at,
        )
        summary_values = {
            "documents": documents.total_documents,
            "evidences": projection.evidences.total_evidences,
        }
        for key, value in summary_values.items():
            self.summary_cards[key].set_value(value)

        document_values = {
            "total": documents.total_documents,
            "processed": documents.processed_documents,
            "pending": documents.pending_documents,
            "ocr": documents.ocr_required_documents,
            "failed": documents.failed_documents,
            "pages": documents.processed_pages,
        }
        for key, value in document_values.items():
            self.document_cards[key].set_value(value)

        self.evidence_total_card.set_value(
            projection.evidences.total_evidences
        )
