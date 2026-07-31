import os
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from core.application import Application
from core.version import (
    APPLICATION_DISPLAY_NAME,
    PUBLIC_VERSION,
    TECHNICAL_VERSION,
)


class ReleaseVersionTests(unittest.TestCase):
    def test_beta_1_1_has_one_coherent_version_source(self):
        self.assertEqual(PUBLIC_VERSION, "Beta 1.1")
        self.assertEqual(TECHNICAL_VERSION, "1.1.0-beta.1")
        self.assertEqual(
            APPLICATION_DISPLAY_NAME, "ProcDocOrganizer Beta 1.1"
        )

    def test_active_qt_metadata_and_labels_use_beta_1_1(self):
        application = Application()
        try:
            self.assertEqual(
                application.app.applicationVersion(), TECHNICAL_VERSION
            )
            self.assertEqual(
                application.app.applicationDisplayName(),
                APPLICATION_DISPLAY_NAME,
            )
            self.assertEqual(
                application.main_window.windowTitle(),
                APPLICATION_DISPLAY_NAME,
            )
            self.assertEqual(
                application.main_window.version_label.text(), PUBLIC_VERSION
            )
            self.assertNotIn("v1.0", application.main_window.windowTitle())
            self.assertNotIn("v1.0", application.main_window.version_label.text())
        finally:
            application.main_window.close()
            application.app.processEvents()


if __name__ == "__main__":
    unittest.main()
