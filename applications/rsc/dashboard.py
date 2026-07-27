"""Dashboard RSC declarado exclusivamente pelo Platform SDK."""

from platform_sdk import (
    ContributionCategory,
    ContributionRegistration,
    DashboardCard,
    DashboardContribution,
    DashboardPanel,
    DashboardRefreshPolicy,
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


def rsc_dashboard_contributions():
    application_id = "rsc"
    contributions = (
        DashboardContribution(
            application_id=application_id,
            section="summary",
            priority=30,
            widget_factory=lambda: DashboardCard(
                "Atribuições",
                _assignment_count,
                key="assignments",
            ),
            refresh_policy=DashboardRefreshPolicy.MANUAL,
            metadata={"summary_key": "assignments"},
        ),
        DashboardContribution(
            application_id=application_id,
            section="summary",
            priority=20,
            widget_factory=lambda: DashboardCard(
                "Exercícios",
                _exercise_count,
                key="exercises",
            ),
            refresh_policy=DashboardRefreshPolicy.MANUAL,
            metadata={"summary_key": "exercises"},
        ),
        DashboardContribution(
            application_id=application_id,
            section="content",
            priority=10,
            widget_factory=lambda: DashboardPanel(
                "RSC",
                (
                    DashboardCard(
                        "Atribuições funcionais",
                        _assignment_count,
                        key="assignments",
                    ),
                    DashboardCard(
                        "Exercícios funcionais",
                        _exercise_count,
                        key="exercises",
                    ),
                ),
            ),
            refresh_policy=DashboardRefreshPolicy.MANUAL,
            metadata={
                "attribute_name": "rsc_section",
                "cards_attribute": "rsc_cards",
            },
        ),
    )
    return tuple(
        ContributionRegistration(
            category=ContributionCategory.DASHBOARD,
            application_id=application_id,
            priority=contribution.priority,
            contribution=contribution,
        )
        for contribution in contributions
    )
