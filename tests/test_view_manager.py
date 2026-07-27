import os
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication, QStackedWidget, QWidget

from ui.view_manager import ViewManager
from ui.views import BaseView


class TrackingView(BaseView):
    def __init__(self):
        super().__init__(title="Teste")
        self.events = []

    def on_project_opened(self, project):
        self.events.append(("opened", project))

    def on_project_changed(self, project):
        self.events.append(("changed", project))

    def on_project_closed(self):
        self.events.append(("closed",))


class ViewManagerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.stack = QStackedWidget()
        self.manager = ViewManager(self.stack)

    def tearDown(self):
        self.stack.close()

    def test_registers_once_and_reuses_same_instance(self):
        view = QWidget()

        self.assertIs(self.manager.register("home", view), view)
        self.assertIs(self.manager.get("home"), view)
        self.assertEqual(self.stack.count(), 1)
        with self.assertRaises(ValueError):
            self.manager.register("home", QWidget())
        with self.assertRaises(ValueError):
            self.manager.register("other", view)

    def test_switches_and_reports_active_view(self):
        home = self.manager.register("home", QWidget())
        documents = self.manager.register("documents", QWidget())

        self.assertTrue(self.manager.show("documents"))
        self.assertIs(self.manager.active_view(), documents)
        self.assertEqual(self.manager.active_view_id(), "documents")
        self.assertFalse(self.manager.show("missing"))
        self.assertIs(self.manager.active_view(), documents)
        self.assertIsNot(self.manager.active_view(), home)

    def test_views_mapping_cannot_be_mutated_externally(self):
        self.manager.register("home", QWidget())

        with self.assertRaises(TypeError):
            self.manager.views["other"] = QWidget()

    def test_notifies_open_change_and_close(self):
        view = self.manager.register("home", TrackingView())
        first = object()
        second = object()

        self.manager.notify_project_opened(first)
        self.manager.notify_project_changed(second)
        self.manager.notify_project_closed()

        self.assertEqual(
            view.events,
            [
                ("opened", first),
                ("changed", second),
                ("closed",),
            ],
        )

    def test_close_notification_can_exclude_owned_view(self):
        included = self.manager.register("included", TrackingView())
        excluded = self.manager.register("excluded", TrackingView())

        self.manager.notify_project_closed(exclude=(excluded,))

        self.assertEqual(included.events, [("closed",)])
        self.assertEqual(excluded.events, [])

    def test_rejects_invalid_registration_contract(self):
        for identifier in ("", " "):
            with self.assertRaises(ValueError):
                self.manager.register(identifier, QWidget())
        with self.assertRaises(TypeError):
            self.manager.register(1, QWidget())
        with self.assertRaises(TypeError):
            self.manager.register("invalid", object())


if __name__ == "__main__":
    unittest.main()
