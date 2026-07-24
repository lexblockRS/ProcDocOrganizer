"""
Gerenciamento de projetos do ProcDocOrganizer.
"""

from pathlib import Path
import shutil

from database import initialize_database
from models.project import LEGACY_APPLICATION_ID, Project


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
        application_id: str = LEGACY_APPLICATION_ID,
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
                application_id=application_id,
            )

            initialize_database(project_path / project.database)
            project.save()

            return project

        except Exception as exc:

            try:
                self._cleanup_project(project_path)

            except OSError as cleanup_exc:
                raise RuntimeError(
                    "Não foi possível criar o projeto e limpar os arquivos "
                    f"parciais. Erro original: {exc}"
                ) from cleanup_exc

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
        project.last_opened_at = project.now()
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
            "documents",
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
            shutil.rmtree(project_path)
