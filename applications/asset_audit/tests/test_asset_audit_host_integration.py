import os
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from core.application_lifecycle_host import ApplicationLifecycleHost
from core.project_manager import ProjectManager
from platform_sdk import (
    ApplicationCatalog,
    ApplicationLifecycleState,
    ApplicationRegistry,
    ContributionManager,
    ProjectSessionFactory,
)
from ui.platform_main_window import PlatformMainWindow

from ..descriptor import ACTION_ID, APPLICATION_ID, MAIN_VIEW_ID, MENU_ID


class AssetAuditHostIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.qt_app = QApplication.instance() or QApplication([])

    def test_creation_presentation_navigation_and_rsc_coexistence(self):
        catalog = ApplicationCatalog.discover()
        registry = ApplicationRegistry(catalog.applications)
        factory = ProjectSessionFactory(registry)
        lifecycle = ApplicationLifecycleHost()
        contributions = ContributionManager()
        contributions.register_many(catalog.contributions)
        window = PlatformMainWindow(contributions)
        self.addCleanup(window.deleteLater)
        self.addCleanup(window.close)

        with TemporaryDirectory() as temporary:
            manager = ProjectManager()
            asset_project = manager.create_project(
                "Asset Audit",
                Path(temporary),
                application_id=APPLICATION_ID,
            )
            rsc_project = manager.create_project(
                "RSC",
                Path(temporary),
                application_id="rsc",
            )

            asset_host_session = factory.create(asset_project)
            asset_runtime = (
                asset_host_session.platform_session.application_runtime
            )
            asset_session = asset_runtime.application_session
            lifecycle.activate_session(asset_host_session)
            window.home_view.refresh_dashboard_contributions(
                asset_host_session
            )

            self.assertEqual(
                asset_runtime.lifecycle_state,
                ApplicationLifecycleState.ACTIVE,
            )
            self.assertEqual(
                window.get_menu(MENU_ID).title(),
                "Asset Audit",
            )
            self.assertIn(ACTION_ID, vars(window))
            self.assertIn(MAIN_VIEW_ID, window.views)
            window.action_asset_audit_home.trigger()
            self.assertIs(
                window.view_manager.active_view(),
                window.asset_audit_home_view,
            )
            self.assertIn(
                window.action_asset_audit_home,
                window._toolbars_by_id["main"].actions(),
            )
            self.assertEqual(
                tuple(
                    card.value_label.text()
                    for card in (
                        window.home_view.asset_audit_cards.values()
                    )
                ),
                ("12", "4", "2", "7", "2"),
            )

            rsc_host_session = factory.create(rsc_project)
            rsc_runtime = (
                rsc_host_session.platform_session.application_runtime
            )
            lifecycle.activate_session(rsc_host_session)
            self.assertEqual(
                asset_runtime.lifecycle_state,
                ApplicationLifecycleState.ACTIVE,
            )
            lifecycle.dispose_session(asset_host_session)

            self.assertTrue(asset_session.is_disposed)
            self.assertEqual(
                asset_runtime.lifecycle_state,
                ApplicationLifecycleState.DISPOSED,
            )
            self.assertEqual(
                rsc_runtime.lifecycle_state,
                ApplicationLifecycleState.ACTIVE,
            )
            self.assertFalse(hasattr(asset_session, "rsc_session"))
            self.assertFalse(hasattr(
                rsc_runtime.application_session,
                "asset_service",
            ))

            lifecycle.dispose_session(rsc_host_session)
            self.assertEqual(
                rsc_runtime.lifecycle_state,
                ApplicationLifecycleState.DISPOSED,
            )


if __name__ == "__main__":
    unittest.main()
