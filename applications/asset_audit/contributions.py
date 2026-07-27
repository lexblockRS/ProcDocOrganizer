"""Contribuições públicas da Asset Audit."""

from platform_sdk import (
    ActionContribution,
    ContributionCategory,
    ContributionRegistration,
    MenuContribution,
    ToolbarContribution,
    ViewContribution,
)

from .dashboard import dashboard_registrations
from .descriptor import (
    ACTION_ID,
    APPLICATION_ID,
    MAIN_VIEW_ID,
    MENU_ID,
    OPEN_HOME_COMMAND,
    TOOLBAR_ID,
)
from .views import create_asset_audit_home_view


def asset_audit_contributions(application, controller):
    contributions = (
        ContributionRegistration(
            ContributionCategory.MENU,
            APPLICATION_ID,
            50,
            MenuContribution(MENU_ID, "Asset Audit"),
        ),
        ContributionRegistration(
            ContributionCategory.ACTION,
            APPLICATION_ID,
            40,
            ActionContribution(
                ACTION_ID,
                "Abrir Asset Audit",
                MENU_ID,
                navigation_target=MAIN_VIEW_ID,
                controller=controller,
                command_id=OPEN_HOME_COMMAND,
                object_name="actionAssetAuditHome",
                disable_on_project_close=True,
            ),
        ),
        ContributionRegistration(
            ContributionCategory.VIEW,
            APPLICATION_ID,
            30,
            ViewContribution(
                MAIN_VIEW_ID,
                "asset_audit_home_view",
                create_asset_audit_home_view,
                "show_asset_audit_home",
            ),
        ),
        ContributionRegistration(
            ContributionCategory.TOOLBAR,
            APPLICATION_ID,
            20,
            ToolbarContribution(TOOLBAR_ID, ACTION_ID),
        ),
    )
    return (*contributions, *dashboard_registrations(application))
