"""Identidade canônica da Application Asset Audit."""

from platform_sdk import ApplicationDescriptor, Version


APPLICATION_ID = "asset_audit"
APPLICATION_NAME = "Asset Audit"
APPLICATION_VERSION = "0.1.0"

MAIN_VIEW_ID = "asset_audit.home"
MENU_ID = "asset_audit.menu"
ACTION_ID = "action_asset_audit_home"
TOOLBAR_ID = "main"
OPEN_HOME_COMMAND = "asset_audit.open_home"
DASHBOARD_SECTION_ID = "asset_audit.summary"

ASSET_AUDIT_DESCRIPTOR = ApplicationDescriptor(
    application_id=APPLICATION_ID,
    display_name=APPLICATION_NAME,
    version=Version.parse(APPLICATION_VERSION),
    minimum_platform_version=Version(1, 0, 0),
    supported_project_schema_versions=(1,),
    description=(
        "Application de referência para auditoria de ativos usando "
        "exclusivamente o Platform SDK."
    ),
)
