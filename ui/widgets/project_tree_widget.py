"""
Árvore do projeto.

Responsável por exibir a estrutura lógica do projeto aberto.
"""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QTreeWidget,
    QTreeWidgetItem,
)

from models import Document, Project


class ProjectTreeWidget(QTreeWidget):
    """
    Árvore do projeto.
    """

    document_selected = Signal(object)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setHeaderHidden(True)
        self.itemSelectionChanged.connect(self._emit_selected_document)

        self.clear_project()

    # ------------------------------------------------------------------

    def clear_project(self):
        """
        Remove todas as informações da árvore.
        """

        self.clear()

        root = QTreeWidgetItem(self)

        root.setText(0, "Nenhum projeto aberto")

        root.setExpanded(True)

    # ------------------------------------------------------------------

    def load_project(
        self,
        project: Project,
        documents: list[Document] | None = None,
    ):
        """
        Carrega a estrutura lógica do projeto.
        """

        if documents is None:
            documents = []

        self.clear()

        root = QTreeWidgetItem(self)
        root.setText(0, project.project_name)

        # ---------------- Arquivos ----------------

        files_item = QTreeWidgetItem(root)
        files_item.setText(0, "Arquivos")

        for document in documents:
            item = QTreeWidgetItem(files_item)
            item.setText(
                0,
                f"{document.name} ({document.pages} páginas, {document.status})",
            )
            item.setData(
                0,
                Qt.ItemDataRole.UserRole,
                document,
            )

        # ---------------- Evidências ----------------

        QTreeWidgetItem(root, ["Evidências"])

        # ---------------- Linha do Tempo ----------------

        QTreeWidgetItem(root, ["Linha do Tempo"])

        # ---------------- Classificações ----------------

        QTreeWidgetItem(root, ["Classificações"])

        root.setExpanded(True)
        files_item.setExpanded(True)

    # ------------------------------------------------------------------

    def _emit_selected_document(self):
        item = self.currentItem()

        if item is None:
            self.document_selected.emit(None)
            return

        self.document_selected.emit(
            item.data(0, Qt.ItemDataRole.UserRole)
        )

    # ------------------------------------------------------------------
