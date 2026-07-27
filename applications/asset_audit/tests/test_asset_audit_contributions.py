import unittest

from platform_sdk import (
    ActionContribution,
    ApplicationCatalog,
    ApplicationView,
    ContributionCategory,
    DashboardCard,
    DashboardContribution,
    DashboardPanel,
    MenuContribution,
    ToolbarContribution,
    ViewContribution,
)

from ..descriptor import (
    ACTION_ID,
    APPLICATION_ID,
    MAIN_VIEW_ID,
    OPEN_HOME_COMMAND,
)


class AssetAuditContributionTests(unittest.TestCase):
    def setUp(self):
        self.catalog = ApplicationCatalog.discover()
        self.application = next(
            item
            for item in self.catalog.applications
            if item.descriptor.application_id == APPLICATION_ID
        )
        self.registrations = tuple(
            item
            for item in self.catalog.contributions
            if item.application_id == APPLICATION_ID
        )

    def contribution(self, category):
        return tuple(
            item.contribution
            for item in self.registrations
            if item.category is category
        )

    def test_registers_every_required_public_contribution(self):
        expected = {
            ContributionCategory.MENU,
            ContributionCategory.ACTION,
            ContributionCategory.VIEW,
            ContributionCategory.TOOLBAR,
            ContributionCategory.DASHBOARD,
        }

        self.assertEqual(
            {item.category for item in self.registrations},
            expected,
        )
        self.assertIsInstance(
            self.contribution(ContributionCategory.MENU)[0],
            MenuContribution,
        )
        self.assertIsInstance(
            self.contribution(ContributionCategory.TOOLBAR)[0],
            ToolbarContribution,
        )
        self.assertIsInstance(
            self.contribution(ContributionCategory.DASHBOARD)[0],
            DashboardContribution,
        )

    def test_action_is_operational_and_targets_public_view(self):
        action = self.contribution(ContributionCategory.ACTION)[0]

        self.assertIsInstance(action, ActionContribution)
        self.assertEqual(action.attribute_name, ACTION_ID)
        self.assertEqual(action.navigation_target, MAIN_VIEW_ID)
        self.assertEqual(action.command_id, OPEN_HOME_COMMAND)
        self.assertEqual(
            action.controller.execute(action.command_id),
            MAIN_VIEW_ID,
        )

    def test_view_is_declarative_and_contains_reference_content(self):
        contribution = self.contribution(ContributionCategory.VIEW)[0]
        view = contribution.factory()

        self.assertIsInstance(contribution, ViewContribution)
        self.assertIsInstance(view, ApplicationView)
        self.assertEqual(view.title, "Asset Audit")
        self.assertTrue(any(
            "Application de Referência" in line
            for line in view.content
        ))
        self.assertTrue(any("Platform SDK" in line for line in view.content))

    def test_dashboard_reads_values_from_application_session(self):
        dashboard = self.contribution(
            ContributionCategory.DASHBOARD
        )[0]
        panel = dashboard.widget_factory()

        self.assertIsInstance(panel, DashboardPanel)
        self.assertTrue(all(
            isinstance(card, DashboardCard) for card in panel.cards
        ))
        self.assertEqual(
            tuple(card.value(None) for card in panel.cards),
            (0, 0, 0, 0, 0),
        )


if __name__ == "__main__":
    unittest.main()
