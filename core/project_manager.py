"""
Gerenciamento de projetos do ProcDocOrganizer.
"""

from pathlib import Path
import shutil

from models.project import Project


class ProjectManager:
    """
    Responsável pela criação e abertura de projetos.

    Esta classe não conhece a interface gráfica nem o estado da aplicação.
    """

    # ------------------------------------------------------------------

    def create_project(
        self,
        project_name: str,
        parent_folder: Path,
    ) -> Project:
        """
        Cria um novo projeto.
        """

        project_path = parent_folder / f"{project_name}.pdop"

        if project_path.exists():
            raise FileExistsError(
                f"O projeto '{project_name}' já existe."
            )

        try:

            self._create_project_structure(project_path)

            project = Project.create(
                project_name=project_name,
                project_path=project_path,
            )

            project.save()

            return project

        except Exception:

            self._cleanup_project(project_path)

            raise

    # ------------------------------------------------------------------

    def open_project(
        self,
        project_folder: Path,
    ) -> Project:
        """
        Abre um projeto existente.
        """

        project_file = project_folder / "project.json"

        if not project_file.exists():
            raise FileNotFoundError(
                "Arquivo 'project.json' não encontrado."
            )

        project = Project.load(project_file)

        # Atualiza a data de abertura
        project.save()

        return project

    # ------------------------------------------------------------------

    @staticmethod
    def _create_project_structure(
        project_path: Path,
    ) -> None:
        """
        Cria a estrutura de diretórios do projeto.
        """

        project_path.mkdir(parents=True)

        for folder in (
            "cache",
            "exports",
            "logs",
            "temp",
        ):
            (project_path / folder).mkdir()

    # ------------------------------------------------------------------

    @staticmethod
    def _cleanup_project(
        project_path: Path,
    ) -> None:
        """
        Remove completamente um projeto criado parcialmente.
        """

        if project_path.exists():
            shutil.rmtree(project_path, ignore_errors=True)