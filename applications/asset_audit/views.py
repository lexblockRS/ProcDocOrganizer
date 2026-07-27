"""Views declarativas da Asset Audit."""

from platform_sdk import ApplicationView


def create_asset_audit_home_view():
    return ApplicationView(
        title="Asset Audit",
        content=(
            "Application de Referência",
            "Construída exclusivamente com o Platform SDK",
            "Domínio inicial: assets, audits, findings e evidências.",
            "Os dados atuais são mantidos exclusivamente em memória.",
        ),
    )
