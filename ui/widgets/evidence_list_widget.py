"""Lista e filtro local de evidências."""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QVBoxLayout,
    QWidget,
)


class EvidenceListWidget(QWidget):
    evidence_selected = Signal(object)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._evidences = ()
        self._statuses = {}
        self.filter_edit = QLineEdit()
        self.filter_edit.setPlaceholderText("Filtrar evidências")
        self.sort_combo = QComboBox()
        self.sort_combo.addItem("Mais antigas", "oldest")
        self.sort_combo.addItem("Mais recentes", "newest")
        self.sort_combo.addItem("Título A–Z", "title_asc")
        self.sort_combo.addItem("Título Z–A", "title_desc")
        self.list_widget = QListWidget()
        self.empty_label = QLabel("Nenhuma evidência cadastrada.")
        self.empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout = QVBoxLayout(self)
        layout.addWidget(self.filter_edit)
        layout.addWidget(self.sort_combo)
        layout.addWidget(self.list_widget, 1)
        layout.addWidget(self.empty_label)
        self.filter_edit.textChanged.connect(self._rebuild)
        self.sort_combo.currentIndexChanged.connect(self._rebuild)
        self.list_widget.currentItemChanged.connect(self._selection_changed)
        self._rebuild()

    def set_evidences(self, evidences, statuses=None) -> None:
        self._evidences = tuple(evidences)
        self._statuses = dict(statuses or {})
        self._rebuild()

    def select_evidence(self, evidence_id: str | None) -> None:
        self.list_widget.blockSignals(True)
        try:
            self.list_widget.setCurrentItem(None)
            if evidence_id is not None:
                for index in range(self.list_widget.count()):
                    item = self.list_widget.item(index)
                    if item.data(Qt.ItemDataRole.UserRole).id == evidence_id:
                        self.list_widget.setCurrentItem(item)
                        break
        finally:
            self.list_widget.blockSignals(False)

    def clear(self) -> None:
        self.filter_edit.clear()
        self.set_evidences(())

    def visible_count(self) -> int:
        return self.list_widget.count()

    def _rebuild(self, *_args) -> None:
        selected = self.current_evidence_id()
        query = self.filter_edit.text().strip().casefold()
        self.list_widget.blockSignals(True)
        try:
            self.list_widget.clear()
            for evidence in self._sorted_evidences():
                haystack = " ".join((
                    evidence.title, evidence.category or "", evidence.user_notes or "",
                )).casefold()
                if query and query not in haystack:
                    continue
                status = getattr(self._statuses.get(evidence.id), "value", self._statuses.get(evidence.id))
                available = "Disponível" if status == "available" else "Indisponível"
                page = f"p. {evidence.page_number}" if evidence.page_number else "sem página"
                period = evidence.start_date or "sem data"
                if evidence.end_date:
                    period += f" a {evidence.end_date}"
                item = QListWidgetItem(
                    f"{evidence.title}\n{evidence.category or 'Sem categoria'} • {page} • {period} • {available}"
                )
                item.setData(Qt.ItemDataRole.UserRole, evidence)
                self.list_widget.addItem(item)
        finally:
            self.list_widget.blockSignals(False)
        self.select_evidence(selected)
        self.empty_label.setVisible(self.list_widget.count() == 0)

    def _sorted_evidences(self):
        mode = self.sort_combo.currentData()
        if mode == "newest":
            return sorted(
                self._evidences,
                key=lambda item: item.created_at,
                reverse=True,
            )
        if mode == "title_asc":
            return sorted(
                self._evidences,
                key=lambda item: item.title.casefold(),
            )
        if mode == "title_desc":
            return sorted(
                self._evidences,
                key=lambda item: item.title.casefold(),
                reverse=True,
            )
        return sorted(
            self._evidences,
            key=lambda item: item.created_at,
        )

    def current_evidence_id(self):
        item = self.list_widget.currentItem()
        return item.data(Qt.ItemDataRole.UserRole).id if item else None

    def _selection_changed(self, current, _previous) -> None:
        evidence = current.data(Qt.ItemDataRole.UserRole) if current else None
        self.evidence_selected.emit(evidence.id if evidence else None)
