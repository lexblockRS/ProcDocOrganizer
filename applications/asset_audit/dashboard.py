"""Dashboard declarativo da Asset Audit."""

from platform_sdk import (
    ContributionCategory,
    ContributionRegistration,
    DashboardCard,
    DashboardContribution,
    DashboardPanel,
    DashboardRefreshPolicy,
)

from .descriptor import APPLICATION_ID, DASHBOARD_SECTION_ID


def dashboard_registrations(application):
    metrics = (
        ("assets", "Assets", lambda session: session.asset_service.count_assets()),
        ("audits", "Audits", lambda session: session.audit_service.count_audits()),
        (
            "open_audits",
            "Open Audits",
            lambda session: session.audit_service.count_open_audits(),
        ),
        (
            "findings",
            "Findings",
            lambda session: session.finding_service.count_findings(),
        ),
        (
            "pending_findings",
            "Pending Findings",
            lambda session: (
                session.finding_service.count_pending_findings()
            ),
        ),
    )

    def value(metric):
        def provide(_host_session):
            session = application.application_session
            return metric(session) if session is not None else 0

        return provide

    contribution = DashboardContribution(
        application_id=APPLICATION_ID,
        section="content",
        priority=10,
        widget_factory=lambda: DashboardPanel(
            "Asset Audit",
            tuple(
                DashboardCard(title, value(metric), key=key)
                for key, title, metric in metrics
            ),
        ),
        refresh_policy=DashboardRefreshPolicy.ON_OPEN,
        visibility=lambda _session: application.is_active,
        metadata={
            "attribute_name": DASHBOARD_SECTION_ID.replace(".", "_"),
            "cards_attribute": "asset_audit_cards",
        },
    )
    return (
        ContributionRegistration(
            ContributionCategory.DASHBOARD,
            APPLICATION_ID,
            contribution.priority,
            contribution,
        ),
    )
