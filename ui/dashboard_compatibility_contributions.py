"""Provider temporário dos widgets históricos do Dashboard."""

from contracts import (
    ContributionCategory,
    ContributionRegistration,
    DashboardContribution,
    DashboardRefreshPolicy,
)
from core.contribution_manager import ContributionManager
from ui.widgets.dashboard_widgets import (
    DashboardSection,
    ResponsiveCardGrid,
    SummaryCard,
)


def _application_session(session):
    return getattr(session, "rsc_session", None)


def _assignment_count(session) -> int:
    application_session = _application_session(session)
    if application_session is None:
        return 0
    return len(tuple(
        application_session
        .list_functional_assignment_evidences_service.execute()
    ))


def _exercise_count(session) -> int:
    application_session = _application_session(session)
    if application_session is None:
        return 0
    return len(tuple(
        application_session.list_functional_exercises_service.execute()
    ))


class _MetricCard(SummaryCard):
    def __init__(self, title, value_factory):
        super().__init__(title)
        self._value_factory = value_factory

    def refresh_dashboard(self, session) -> bool:
        self.set_value(self._value_factory(session))
        return _application_session(session) is not None


class _HistoricalSection(DashboardSection):
    def __init__(self):
        content = ResponsiveCardGrid()
        self.cards = {
            "assignments": SummaryCard("Atribuições funcionais"),
            "exercises": SummaryCard("Exercícios funcionais"),
        }
        content.set_cards(self.cards.values())
        super().__init__("RSC", content)

    def refresh_dashboard(self, session) -> bool:
        self.cards["assignments"].set_value(_assignment_count(session))
        self.cards["exercises"].set_value(_exercise_count(session))
        return _application_session(session) is not None


def create_compatibility_dashboard_manager() -> ContributionManager:
    manager = ContributionManager()
    application_id = "rsc"
    contributions = (
        DashboardContribution(
            application_id=application_id,
            section="summary",
            priority=30,
            widget_factory=lambda: _MetricCard(
                "Atribuições",
                _assignment_count,
            ),
            refresh_policy=DashboardRefreshPolicy.MANUAL,
            metadata={"summary_key": "assignments"},
        ),
        DashboardContribution(
            application_id=application_id,
            section="summary",
            priority=20,
            widget_factory=lambda: _MetricCard(
                "Exercícios",
                _exercise_count,
            ),
            refresh_policy=DashboardRefreshPolicy.MANUAL,
            metadata={"summary_key": "exercises"},
        ),
        DashboardContribution(
            application_id=application_id,
            section="content",
            priority=10,
            widget_factory=_HistoricalSection,
            refresh_policy=DashboardRefreshPolicy.MANUAL,
            metadata={
                "attribute_name": "rsc_section",
                "cards_attribute": "rsc_cards",
            },
        ),
    )
    manager.register_many(
        ContributionRegistration(
            category=ContributionCategory.DASHBOARD,
            application_id=application_id,
            priority=contribution.priority,
            contribution=contribution,
        )
        for contribution in contributions
    )
    return manager
