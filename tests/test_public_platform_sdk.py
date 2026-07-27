import ast
import os
from pathlib import Path
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from applications.rsc.application import RscApplication
from contracts import ContributionRegistration
from platform_sdk import (
    ActionContribution,
    ApplicationView,
    ApplicationCatalog,
    ContributionCategory,
    DashboardCard,
    DashboardContribution,
    DashboardRefreshPolicy,
    MenuContribution,
    ToolbarContribution,
    ViewContribution,
)
from ui.platform_main_window import PlatformMainWindow
import platform_sdk

class ModuleDouble:
    descriptor = RscApplication.descriptor

    def prepare(self, context):
        pass

    def create_session(self, context):
        return object()

    def contributions(self, session):
        return ()

    def transition(self, transition):
        pass

    def dispose(self):
        pass


class ProviderDouble:
    def __init__(self, application, contributions=()):
        self._application = application
        self._contributions = tuple(contributions)

    def applications(self):
        return (self._application,)

    def contributions(self):
        return self._contributions


class ControllerDouble:
    def __init__(self):
        self.calls = []

    def execute(self, command_id, context=None):
        self.calls.append((command_id, context))


class PublicPlatformSdkTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_public_contracts_have_no_qt_dependency(self):
        root = Path(__file__).parents[1] / "platform_sdk"
        for path in root.glob("*.py"):
            with self.subTest(path=path.name):
                source = path.read_text(encoding="utf-8")
                self.assertNotIn("PySide6", source)
                self.assertNotIn("PyQt", source)

    def test_sdk_exports_the_stable_platform_surface(self):
        expected = {
            "ApplicationModule",
            "ApplicationDescriptor",
            "ApplicationRuntime",
            "PlatformSession",
            "ContributionManager",
            "DashboardContribution",
            "ProjectSessionFactory",
            "ApplicationRegistry",
            "ApplicationLifecycleState",
            "ApplicationLifecycleTransition",
            "MenuContribution",
            "ActionContribution",
            "ViewContribution",
            "ToolbarContribution",
            "ApplicationProvider",
            "ApplicationCatalog",
        }

        self.assertTrue(expected.issubset(set(platform_sdk.__all__)))

    def test_catalog_discovers_provider_deterministically(self):
        provider = ProviderDouble(ModuleDouble())
        catalog = ApplicationCatalog((provider,))

        self.assertEqual(catalog.applications, (provider._application,))
        self.assertEqual(catalog.contributions, ())

    def test_builtin_discovery_registers_rsc_automatically(self):
        catalog = ApplicationCatalog.discover()

        self.assertIn(
            "rsc",
            tuple(
                item.descriptor.application_id
                for item in catalog.applications
            ),
        )
        self.assertTrue(catalog.contributions)

    def test_materializes_menu_action_view_and_toolbar(self):
        application_id = "sdk.test"
        callback_calls = []
        controller = ControllerDouble()
        registrations = (
            ContributionRegistration(
                ContributionCategory.MENU,
                application_id,
                40,
                MenuContribution("sdk-menu", "SDK"),
            ),
            ContributionRegistration(
                ContributionCategory.ACTION,
                application_id,
                30,
                ActionContribution(
                    "action_sdk",
                    "Abrir SDK",
                    "sdk-menu",
                    callback=lambda: callback_calls.append("called"),
                    navigation_target="sdk",
                    controller=controller,
                    command_id="sdk.open",
                ),
            ),
            ContributionRegistration(
                ContributionCategory.VIEW,
                application_id,
                20,
                ViewContribution(
                    "sdk",
                    "sdk_view",
                    lambda: ApplicationView(
                        "SDK",
                        ("View declarativa",),
                    ),
                    "show_sdk",
                ),
            ),
            ContributionRegistration(
                ContributionCategory.TOOLBAR,
                application_id,
                10,
                ToolbarContribution("main", "action_sdk"),
            ),
        )
        catalog = ApplicationCatalog(
            (ProviderDouble(ModuleDouble(), registrations),)
        )
        from core.contribution_manager import ContributionManager

        manager = ContributionManager()
        manager.register_many(catalog.contributions)
        window = PlatformMainWindow(manager)
        self.addCleanup(window.deleteLater)
        self.addCleanup(window.close)

        self.assertEqual(window.get_menu("sdk-menu").title(), "SDK")
        self.assertIn(
            window.action_sdk,
            window.get_menu("sdk-menu").actions(),
        )
        self.assertIs(window.views["sdk"], window.sdk_view)
        window.action_sdk.trigger()
        self.assertIs(
            window.view_manager.active_view(),
            window.sdk_view,
        )
        self.assertEqual(callback_calls, ["called"])
        self.assertEqual(controller.calls, [("sdk.open", None)])
        toolbar = window._toolbars_by_id["main"]
        self.assertIn(window.action_sdk, toolbar.actions())

    def test_materializes_public_dashboard_component(self):
        dashboard = DashboardContribution(
            application_id="sdk.test",
            section="summary",
            priority=10,
            widget_factory=lambda: DashboardCard(
                "Items", 12, key="items"
            ),
            refresh_policy=DashboardRefreshPolicy.ON_OPEN,
            metadata={"summary_key": "items"},
        )
        registration = ContributionRegistration(
            ContributionCategory.DASHBOARD,
            "sdk.test",
            10,
            dashboard,
        )
        catalog = ApplicationCatalog((
            ProviderDouble(ModuleDouble(), (registration,)),
        ))
        from core.contribution_manager import ContributionManager

        manager = ContributionManager()
        manager.register_many(catalog.contributions)
        window = PlatformMainWindow(manager)
        self.addCleanup(window.deleteLater)
        self.addCleanup(window.close)

        self.assertIn("items", window.home_view.summary_cards)
        self.assertEqual(
            window.home_view.summary_cards["items"].value_label.text(),
            "12",
        )

    def test_rsc_uses_public_contribution_contracts(self):
        catalog = ApplicationCatalog.discover()
        rsc = tuple(
            item.contribution
            for item in catalog.contributions
            if item.application_id == "rsc"
        )

        self.assertTrue(rsc)
        self.assertTrue(all(isinstance(
            item,
            (
                ActionContribution,
                ViewContribution,
                ToolbarContribution,
                DashboardContribution,
            ),
        ) for item in rsc))

    def test_rsc_public_contributions_preserve_visual_contract(self):
        from core.contribution_manager import ContributionManager

        catalog = ApplicationCatalog.discover()
        manager = ContributionManager()
        manager.register_many(catalog.contributions)
        window = PlatformMainWindow(manager)
        self.addCleanup(window.deleteLater)
        self.addCleanup(window.close)

        for attribute in (
            "action_activities",
            "action_functional_assignments",
            "action_functional_exercises",
            "activities_view",
            "functional_assignments_view",
            "functional_exercises_view",
            "show_activities",
            "show_functional_assignments",
            "show_functional_exercises",
        ):
            with self.subTest(attribute=attribute):
                self.assertTrue(hasattr(window, attribute))

    def test_applications_do_not_import_private_window_specs(self):
        root = Path(__file__).parents[1] / "applications"
        forbidden = (
            "ui.main_window_contributions",
            "WindowActionSpec",
            "WindowViewSpec",
            "WindowToolbarSpec",
        )
        for path in root.rglob("*.py"):
            source = path.read_text(encoding="utf-8")
            tree = ast.parse(source)
            imports = {
                node.module or ""
                for node in ast.walk(tree)
                if isinstance(node, ast.ImportFrom)
            }
            imports.update(
                alias.name
                for node in ast.walk(tree)
                if isinstance(node, ast.Import)
                for alias in node.names
            )
            with self.subTest(path=path):
                self.assertTrue(all(
                    forbidden_name not in source
                    and forbidden_name not in imports
                    for forbidden_name in forbidden
                ))


if __name__ == "__main__":
    unittest.main()
