"""Workspace visual, somente leitura, para navegação documental."""

from pathlib import Path

from PySide6.QtCore import QSettings, Qt, Signal
from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtWidgets import (
    QComboBox, QGroupBox, QHBoxLayout, QLabel, QLineEdit, QSplitter,
    QToolBar, QVBoxLayout, QWidget,
)

from ui.widgets.document_list_widget import DocumentListWidget
from ui.widgets.document_metadata_widget import DocumentMetadataWidget
from ui.widgets.document_page_list_widget import DocumentPageListWidget
from ui.widgets.document_text_widget import DocumentTextWidget


class DocumentsWorkspace(QWidget):
    document_selected = Signal(object)
    page_selected = Signal(object)
    create_evidence_requested = Signal()
    import_requested = Signal()
    open_requested = Signal()
    ocr_requested = Signal()
    remove_requested = Signal()
    refresh_requested = Signal()
    metadata_save_requested = Signal(str)
    metadata_cancel_requested = Signal()

    FILTERS = (
        ("Todos", "all"),
        ("PDF", "pdf"),
        ("OCR realizado", "ocr_done"),
        ("OCR pendente", "ocr_pending"),
        ("Processado", "processed"),
        ("Não processado", "not_processed"),
    )

    def __init__(self, parent=None):
        super().__init__(parent)
        self.state = "no_project"
        self.catalog = ()
        self.details = None
        self.pages = ()
        self.current_page = None
        self._settings_group = None
        self._settings_file = None
        self._restoring_state = False
        self._pending_selection = None
        self._unsaved_guard = None
        self._last_query = ""
        self._last_filter = "all"

        title = QLabel("Documentos")
        title.setStyleSheet("font-size: 18px; font-weight: bold;")
        self.status_label = QLabel()
        self.message_label = QLabel()
        self.message_label.setWordWrap(True)
        self.toolbar = QToolBar("Documentos", self)
        self.toolbar.setObjectName("documentsToolbar")
        self.import_action = self.toolbar.addAction(
            "Importar Documento..."
        )
        self.toolbar.addSeparator()
        self.open_action = self.toolbar.addAction("Abrir")
        self.ocr_action = self.toolbar.addAction("Executar OCR")
        self.remove_action = self.toolbar.addAction("Remover")
        self.import_button = self.toolbar.widgetForAction(self.import_action)
        self.open_button = self.toolbar.widgetForAction(self.open_action)
        self.ocr_button = self.toolbar.widgetForAction(self.ocr_action)
        self.remove_button = self.toolbar.widgetForAction(self.remove_action)
        self.import_button.setAccessibleName("Importar documento")
        self.import_button.setToolTip(
            "Copiar um documento para o acervo do projeto"
        )
        self.open_button.setAccessibleName("Abrir documento")
        self.open_button.setToolTip(
            "Abrir o documento selecionado no visualizador"
        )
        self.ocr_button.setAccessibleName("Executar OCR")
        self.ocr_button.setToolTip(
            "Processar o documento selecionado com o mecanismo existente"
        )
        self.remove_button.setAccessibleName("Remover documento")
        self.remove_button.setToolTip(
            "Remover o documento selecionado do acervo"
        )
        self._set_document_actions_enabled(False)
        self.import_action.triggered.connect(self.import_requested)
        self.open_action.triggered.connect(self.open_requested)
        self.ocr_action.triggered.connect(self.ocr_requested)
        self.remove_action.triggered.connect(self.remove_requested)
        self.import_action.setShortcut(QKeySequence.StandardKey.Open)
        self.open_action.setShortcuts(
            (QKeySequence("Return"), QKeySequence("Enter"))
        )
        self.remove_action.setShortcut(QKeySequence("Delete"))
        for action in (
            self.import_action,
            self.open_action,
            self.remove_action,
        ):
            action.setShortcutContext(
                Qt.ShortcutContext.WidgetWithChildrenShortcut
            )
        self.addActions(
            (self.import_action, self.open_action, self.remove_action)
        )

        self.document_list_widget = DocumentListWidget()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText(
            "Pesquisar por nome, tipo, caminho, hash ou data..."
        )
        self.search_input.setClearButtonEnabled(True)
        self.filter_combo = QComboBox()
        for label, filter_id in self.FILTERS:
            self.filter_combo.addItem(label, filter_id)
        filters = QHBoxLayout()
        filters.addWidget(QLabel("Pesquisar:"))
        filters.addWidget(self.search_input, 1)
        filters.addWidget(QLabel("Filtro:"))
        filters.addWidget(self.filter_combo)
        self.metadata_widget = DocumentMetadataWidget()
        self.metadata_widget.save_requested.connect(
            self.metadata_save_requested
        )
        self.metadata_widget.cancel_requested.connect(
            self.metadata_cancel_requested
        )
        self.metadata_widget.editing_changed.connect(
            self._metadata_editing_changed
        )
        self.page_list_widget = DocumentPageListWidget()
        self.text_widget = DocumentTextWidget()

        documents_group = self._group("Documentos", self.document_list_widget)
        metadata_group = self._group("Informações", self.metadata_widget)
        pages_group = self._group("Páginas", self.page_list_widget)
        text_group = self._group("Texto", self.text_widget)

        middle = QSplitter(Qt.Orientation.Vertical)
        middle.addWidget(metadata_group)
        middle.addWidget(pages_group)
        middle.setStretchFactor(0, 1)
        middle.setStretchFactor(1, 2)
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setChildrenCollapsible(False)
        splitter.addWidget(documents_group)
        splitter.addWidget(middle)
        splitter.addWidget(text_group)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 1)
        splitter.setStretchFactor(2, 2)
        splitter.setSizes([300, 360, 600])
        self.splitter = splitter

        layout = QVBoxLayout(self)
        layout.addWidget(title)
        layout.addWidget(self.status_label)
        layout.addWidget(self.message_label)
        layout.addWidget(self.toolbar)
        layout.addLayout(filters)
        layout.addWidget(splitter, 1)
        self.summary_status_label = QLabel()
        self.summary_status_label.setObjectName("documentsSummaryStatus")
        layout.addWidget(self.summary_status_label)

        self.document_list_widget.document_selected.connect(
            self._document_selection_changed
        )
        self.search_input.textChanged.connect(self._query_changed)
        self.filter_combo.currentIndexChanged.connect(self._filter_changed)
        header = self.document_list_widget.list_widget.horizontalHeader()
        header.sortIndicatorChanged.connect(self._view_state_changed)
        header.sectionResized.connect(self._view_state_changed)
        self.page_list_widget.page_selected.connect(self.page_selected)
        self.focus_search_action = QAction("Pesquisar documentos", self)
        self.focus_search_action.setShortcut(QKeySequence.StandardKey.Find)
        self.focus_search_action.setShortcutContext(
            Qt.ShortcutContext.WidgetWithChildrenShortcut
        )
        self.focus_search_action.triggered.connect(
            self.search_input.setFocus
        )
        self.refresh_action = QAction("Atualizar documentos", self)
        self.refresh_action.setShortcut(QKeySequence.StandardKey.Refresh)
        self.refresh_action.setShortcutContext(
            Qt.ShortcutContext.WidgetWithChildrenShortcut
        )
        self.refresh_action.triggered.connect(self.refresh_requested)
        self.addActions((self.focus_search_action, self.refresh_action))
        self.setTabOrder(
            self.document_list_widget.list_widget, self.metadata_widget
        )
        self.setTabOrder(
            self.metadata_widget, self.page_list_widget.list_widget
        )
        self.setTabOrder(
            self.page_list_widget.list_widget, self.text_widget.text_edit
        )
        self.clear()

    @staticmethod
    def _group(title, widget):
        group = QGroupBox(title)
        layout = QVBoxLayout(group)
        layout.addWidget(widget)
        return group

    def set_state(self, state: str) -> None:
        self.state = state
        messages = {
            "no_project": "Nenhum projeto aberto.",
            "loading": "Carregando documentos...",
            "empty": "Nenhum documento importado.",
            "error": "Não foi possível carregar os documentos do projeto.",
            "ready": "",
        }
        self.status_label.setText(messages.get(state, state))

    def set_catalog(self, catalog) -> None:
        self.catalog = tuple(catalog)
        self.document_list_widget.set_catalog(self.catalog)
        if self._pending_selection:
            if self.document_list_widget.select_identity(
                self._pending_selection
            ):
                self.document_selected.emit(self._pending_selection)
            self._pending_selection = None
        self._update_summary()

    def set_details(self, details) -> None:
        self.details = details
        self.metadata_widget.set_details(details)
        self._set_document_actions_enabled(details is not None)
        if details is not None and not details.summary.has_processing_result:
            self.metadata_widget.show_unprocessed()
        self._update_summary()

    @property
    def has_unsaved_metadata(self) -> bool:
        return self.metadata_widget.has_unsaved_changes

    def set_unsaved_guard(self, guard) -> None:
        self._unsaved_guard = guard

    def cancel_metadata_edit(self) -> None:
        self.metadata_widget.cancel_edit()

    def finish_metadata_edit(self) -> None:
        self.metadata_widget.finish_edit()

    def show_metadata_error(self, message: str) -> None:
        self.metadata_widget.show_validation_error(message)

    def set_pages(self, pages) -> None:
        self.pages = tuple(pages)
        self.page_list_widget.set_pages(self.pages)

    def set_page(self, page) -> None:
        self.current_page = page
        self.text_widget.set_page(page)

    def select_document(self, identity) -> bool:
        return self.document_list_widget.select_identity(identity)

    def select_page(self, page_number) -> bool:
        return self.page_list_widget.select_page(page_number)

    def clear_document(self) -> None:
        self.details = None
        self.pages = ()
        self.current_page = None
        self.metadata_widget.clear()
        self.page_list_widget.clear()
        self.text_widget.clear()
        self._set_document_actions_enabled(False)

    def show_message(self, message: str) -> None:
        self.message_label.setText(message)

    def clear(self) -> None:
        self.catalog = ()
        self.document_list_widget.clear()
        self.clear_document()
        self.message_label.clear()
        self.set_state("no_project")
        self._update_summary()

    def on_project_opened(self, project) -> None:
        self._configure_settings(project)
        self._restore_ui_state()
        self.set_state("loading")

    def on_project_closed(self) -> None:
        self._save_ui_state()
        self._settings_group = None
        self._settings_file = None
        self.clear()

    def _set_document_actions_enabled(self, enabled: bool) -> None:
        self.open_action.setEnabled(enabled)
        self.ocr_action.setEnabled(enabled)
        self.remove_action.setEnabled(enabled)

    def _document_selection_changed(self, identity) -> None:
        self.document_selected.emit(identity)
        self._save_ui_state()
        self._update_summary()

    def _query_changed(self, query: str) -> None:
        if not self._can_change_context():
            self.search_input.blockSignals(True)
            self.search_input.setText(self._last_query)
            self.search_input.blockSignals(False)
            return
        self.document_list_widget.set_query(query)
        self._last_query = query
        self._save_ui_state()
        self._update_summary()

    def _filter_changed(self, _index: int) -> None:
        filter_id = self.filter_combo.currentData() or "all"
        if not self._can_change_context():
            previous = self.filter_combo.findData(self._last_filter)
            self.filter_combo.blockSignals(True)
            self.filter_combo.setCurrentIndex(max(0, previous))
            self.filter_combo.blockSignals(False)
            return
        self.document_list_widget.set_filter_id(filter_id)
        self._last_filter = filter_id
        self._save_ui_state()
        self._update_summary()

    def _view_state_changed(self, *_args) -> None:
        self._save_ui_state()

    def _configure_settings(self, project) -> None:
        project_path = getattr(project, "project_path", None)
        if not isinstance(project_path, (str, Path)):
            self._settings_group = None
            self._settings_file = None
            return
        settings_folder = Path(project_path) / ".procdocorganizer"
        settings_folder.mkdir(parents=True, exist_ok=True)
        self._settings_file = settings_folder / "ui.ini"
        self._settings_group = "document-workspace"

    def _settings(self):
        return QSettings(
            str(self._settings_file),
            QSettings.Format.IniFormat,
        )

    def _save_ui_state(self) -> None:
        if self._settings_group is None or self._restoring_state:
            return
        settings = self._settings()
        settings.beginGroup(self._settings_group)
        header = self.document_list_widget.list_widget.horizontalHeader()
        settings.setValue("query", self.search_input.text())
        settings.setValue(
            "filter", self.filter_combo.currentData() or "all"
        )
        settings.setValue("sort_column", header.sortIndicatorSection())
        settings.setValue(
            "sort_order", int(header.sortIndicatorOrder().value)
        )
        settings.setValue(
            "column_widths",
            [
                self.document_list_widget.list_widget.columnWidth(column)
                for column in range(3)
            ],
        )
        settings.setValue(
            "selection",
            self.document_list_widget.current_identity() or "",
        )
        settings.endGroup()
        settings.sync()

    def _restore_ui_state(self) -> None:
        if self._settings_group is None:
            return
        settings = self._settings()
        settings.beginGroup(self._settings_group)
        self._restoring_state = True
        try:
            self.search_input.setText(str(settings.value("query", "")))
            filter_id = str(settings.value("filter", "all"))
            index = self.filter_combo.findData(filter_id)
            self.filter_combo.setCurrentIndex(max(0, index))
            self._last_query = self.search_input.text()
            self._last_filter = self.filter_combo.currentData() or "all"
            column = int(settings.value("sort_column", 0))
            order_value = int(settings.value("sort_order", 0))
            order = Qt.SortOrder(order_value)
            self.document_list_widget.list_widget.sortByColumn(column, order)
            widths = settings.value("column_widths", [])
            if isinstance(widths, (list, tuple)):
                for width_column, width in enumerate(widths[:3]):
                    self.document_list_widget.list_widget.setColumnWidth(
                        width_column, int(width)
                    )
            self._pending_selection = str(
                settings.value("selection", "")
            ) or None
        finally:
            self._restoring_state = False
            settings.endGroup()
        self._update_summary()

    def _update_summary(self) -> None:
        total = len(self.catalog)
        results = self.document_list_widget.proxy_model.rowCount()
        filter_name = self.filter_combo.currentText() or "Todos"
        selected = (
            self.details.summary.name
            if self.details is not None
            else "Nenhum"
        )
        self.summary_status_label.setText(
            f"{total} documento{'s' if total != 1 else ''} | "
            f"{results} resultado{'s' if results != 1 else ''} | "
            f"Filtro: {filter_name} | Selecionado: {selected}"
        )

    def _can_change_context(self) -> bool:
        return bool(
            not self.has_unsaved_metadata
            or self._unsaved_guard is None
            or self._unsaved_guard()
        )

    def _metadata_editing_changed(self, editing: bool) -> None:
        self._set_document_actions_enabled(
            not editing and self.details is not None
        )
