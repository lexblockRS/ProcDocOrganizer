"""
Árvore do projeto.

Responsável por exibir a estrutura lógica do projeto aberto.
"""

from PySide6.QtWidgets import (
    QTreeWidget,
    QTreeWidgetItem,
)

from models.project import Project


class ProjectTreeWidget(QTreeWidget):
    """
    Árvore do projeto.
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setHeaderHidden(True)

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

    def load_project(self, project: Project):
        """
        Carrega a estrutura lógica do projeto.
        """

        self.clear()

        root = QTreeWidgetItem(self)

        root.setText(0, project.project_name)

        QTreeWidgetItem(root, ["Arquivos"])

        QTreeWidgetItem(root, ["Evidências"])

        QTreeWidgetItem(root, ["Linha do Tempo"])

        QTreeWidgetItem(root, ["Classificações"])

        root.setExpanded(True)