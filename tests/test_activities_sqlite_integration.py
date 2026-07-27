import os
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from applications.rsc.composition import create_sqlite_rsc_repositories
from applications.rsc.models import Activity
from presentation.activities import ActivitiesController, ActivitiesViewState
from ui.main_window import MainWindow


def host_session(project_name, database_path):
    repositories = create_sqlite_rsc_repositories(database_path)
    return SimpleNamespace(
        project=SimpleNamespace(project_name=project_name),
        rsc_session=SimpleNamespace(
            activity_repository=repositories.activity
        ),
    )


class ActivitiesSQLiteIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.temporary_directory = TemporaryDirectory()
        self.addCleanup(self.temporary_directory.cleanup)
        self.window = MainWindow()
        self.addCleanup(self.window.close)
        self.controller = ActivitiesController(
            self.window.activities_view
        )

    def test_navigation_selection_close_and_reopening(self):
        database_path = (
            Path(self.temporary_directory.name) / "first.db"
        )
        first = host_session("Primeiro", database_path)
        first.rsc_session.activity_repository.save(
            Activity("activity-1", "Fiscalização")
        )
        first.rsc_session.activity_repository.save(
            Activity("activity-2", "Coordenação")
        )

        self.controller.set_session(first)
        self.window.show_activities()
        self.window.activities_view.activity_list.setCurrentRow(1)
        QApplication.processEvents()

        self.assertIs(
            self.window.stack.currentWidget(),
            self.window.activities_view,
        )
        self.assertEqual(
            self.window.activities_view.activity_list.count(), 2
        )
        self.assertEqual(
            self.window.activities_view.details_description_label.text(),
            "Coordenação",
        )

        self.controller.clear_session()
        self.assertEqual(
            self.window.activities_view.state_stack.currentWidget(),
            self.window.activities_view.no_project_page,
        )

        reopened = host_session("Primeiro", database_path)
        self.controller.set_session(reopened)
        self.assertEqual(
            self.window.activities_view.activity_list.count(), 2
        )

    def test_two_projects_remain_isolated(self):
        first_path = Path(self.temporary_directory.name) / "first.db"
        second_path = Path(self.temporary_directory.name) / "second.db"
        first = host_session("Primeiro", first_path)
        second = host_session("Segundo", second_path)
        first.rsc_session.activity_repository.save(
            Activity("activity-1", "Somente no primeiro")
        )

        self.controller.set_session(first)
        self.assertEqual(
            self.window.activities_view.activity_list.count(), 1
        )
        self.controller.set_session(second)

        self.assertEqual(
            self.window.activities_view.state_stack.currentWidget(),
            self.window.activities_view.empty_page,
        )
        self.assertEqual(
            self.controller.view.state_stack.currentWidget(),
            self.window.activities_view.empty_page,
        )


if __name__ == "__main__":
    unittest.main()
