import ast
import os
from pathlib import Path
from types import SimpleNamespace
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from contracts import (
    ContributionCategory,
    ContributionRegistration,
    DashboardContribution,
    DashboardRefreshPolicy,
)
from core.contribution_manager import ContributionManager
from core.exceptions import ContributionError
from ui.views.home_view import HomeView
from ui.widgets.dashboard_widgets import SummaryCard


class AuditCard(SummaryCard):
    def __init__(self, title):
        super().__init__(title)
        self.sessions = []

    def refresh_dashboard(self, session):
        self.sessions.append(session)
        self.set_value(len(self.sessions))
        return session is not None


def contribution(application_id, title, priority):
    return DashboardContribution(
        application_id=application_id,
        section="summary",
        priority=priority,
        widget_factory=lambda: AuditCard(title),
        refresh_policy=DashboardRefreshPolicy.MANUAL,
    )


def manager_with(*contributions):
    manager = ContributionManager()
    manager.register_many(
        ContributionRegistration(
            category=ContributionCategory.DASHBOARD,
            application_id=item.application_id,
            priority=item.priority,
            contribution=item,
        )
        for item in contributions
    )
    return manager


class DashboardContributionContractTests(unittest.TestCase):
    def test_contract_is_immutable_and_qt_independent(self):
        item = contribution("asset-audit", "Assets", 10)

        self.assertEqual(item.application_id, "asset-audit")
        self.assertEqual(item.section, "summary")
        self.assertEqual(item.priority, 10)
        self.assertEqual(
            item.refresh_policy,
            DashboardRefreshPolicy.MANUAL,
        )

        source = (
            Path(__file__).parents[1]
            / "contracts"
            / "dashboard_contribution.py"
        ).read_text(encoding="utf-8")
        self.assertNotIn("PySide6", source)
        self.assertNotIn("QWidget", source)

    def test_declares_all_refresh_policies(self):
        self.assertEqual(
            set(DashboardRefreshPolicy),
            {
                DashboardRefreshPolicy.MANUAL,
                DashboardRefreshPolicy.ON_OPEN,
                DashboardRefreshPolicy.PERIODIC,
            },
        )

    def test_manager_rejects_non_dashboard_payload_in_category(self):
        manager = ContributionManager()
        manager.register(ContributionRegistration(
            ContributionCategory.DASHBOARD,
            "asset-audit",
            0,
            object(),
        ))

        with self.assertRaisesRegex(
            ContributionError,
            "DashboardContribution",
        ):
            manager.dashboard_contributions()

    def test_duplicate_dashboard_object_is_rejected(self):
        item = contribution("asset-audit", "Assets", 10)
        registration = ContributionRegistration(
            ContributionCategory.DASHBOARD,
            "asset-audit",
            10,
            item,
        )
        manager = ContributionManager()

        with self.assertRaisesRegex(
            ContributionError,
            "duplicada",
        ):
            manager.register_many((registration, registration))


class DashboardContributionViewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.views = []

    def tearDown(self):
        for view in self.views:
            view.close()
            view.deleteLater()
        self.app.processEvents()

    def test_two_applications_are_installed_by_priority(self):
        lower = contribution("rsc", "RSC", 10)
        higher = contribution("asset-audit", "Asset Audit", 20)
        view = HomeView(manager_with(lower, higher))
        self.views.append(view)

        cards = view.summary_grid._cards

        self.assertEqual(
            [card.title_label.text() for card in cards],
            ["Documentos", "Evidências", "Asset Audit", "RSC"],
        )

    def test_refresh_and_visibility_are_generic(self):
        item = contribution("asset-audit", "Asset Audit", 20)
        view = HomeView(manager_with(item))
        self.views.append(view)
        card = view.summary_grid._cards[-1]
        session = SimpleNamespace(marker="asset")

        view.refresh_dashboard_contributions(session)

        self.assertFalse(card.isHidden())
        self.assertEqual(card.value_label.text(), "1")
        self.assertIs(card.sessions[0], session)

    def test_historical_provider_preserves_layout(self):
        view = HomeView()
        self.views.append(view)

        self.assertEqual(
            [card.title_label.text() for card in view.summary_grid._cards],
            ["Documentos", "Evidências", "Atribuições", "Exercícios"],
        )
        self.assertEqual(view.rsc_section.title_label.text(), "RSC")
        self.assertLess(
            view.ready_layout.indexOf(view.rsc_section),
            view.ready_layout.indexOf(view.shortcuts_section),
        )

    def test_dashboard_sources_have_no_rsc_knowledge(self):
        root = Path(__file__).parents[1]
        paths = (
            root / "presentation" / "dashboard" / "controller.py",
            root / "presentation" / "dashboard" / "service.py",
            root / "presentation" / "dashboard" / "projections.py",
            root / "ui" / "views" / "home_view.py",
        )
        forbidden = (
            "applications.rsc",
            "rsc_session",
            "RscSummaryProjection",
            "RscApplication",
        )

        for path in paths:
            source = path.read_text(encoding="utf-8")
            ast.parse(source)
            for term in forbidden:
                with self.subTest(path=path.name, term=term):
                    self.assertNotIn(term, source)


if __name__ == "__main__":
    unittest.main()
