"""
Controller responsável pelo gerenciamento de projetos.
"""

from PySide6.QtWidgets import (
    QDialog,
    QMessageBox,
)

from ui.dialogs import NewProjectDialog


class ProjectController:
    """
    Coordena as operações relacionadas aos projetos.
    """

    def __init__(
        self,
        window,
        manager,
        state,
    ):
        self.window = window
        self.manager = manager
        self.state = state

        self._connect_signals()

    # ------------------------------------------------------------------

    def _connect_signals(self):

        self.window.action_new_project.triggered.connect(
            self.new_project
        )

    # ------------------------------------------------------------------

    def new_project(self):
        """
        Cria um novo projeto.
        """

        dialog = NewProjectDialog(self.window)

        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        try:

            project = self.manager.create_project(
                dialog.get_project_name(),
                dialog.get_project_folder(),
            )

        except FileExistsError as exc:

            QMessageBox.warning(
                self.window,
                "Projeto já existe",
                str(exc),
            )

            return

        except Exception as exc:

            QMessageBox.critical(
                self.window,
                "Erro",
                f"Não foi possível criar o projeto.\n\n{exc}",
            )

            return

        self.state.open_project(project)

        self.window.set_project(project)