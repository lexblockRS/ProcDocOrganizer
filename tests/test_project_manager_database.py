from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from core.project_manager import ProjectManager
from database import ProjectDatabase, SUPPORTED_SCHEMA_VERSION, get_schema_version


class ProjectManagerDatabaseTests(unittest.TestCase):
    def test_new_project_creates_initialized_database(self):
        with TemporaryDirectory() as temporary_directory:
            project = ProjectManager().create_project(
                "Projeto", Path(temporary_directory)
            )
            database_path = project.project_path / project.database

            self.assertTrue(database_path.is_file())
            with ProjectDatabase(database_path) as database:
                self.assertEqual(
                    get_schema_version(database.connection),
                    SUPPORTED_SCHEMA_VERSION,
                )


if __name__ == "__main__":
    unittest.main()
