"""Provider descoberto automaticamente pelo Platform SDK."""

from .application import AssetAuditApplication
from .contributions import asset_audit_contributions
from .controller import AssetAuditController


class AssetAuditApplicationProvider:
    def __init__(self):
        self._application = None
        self._controller = None

    def applications(self):
        self._application = AssetAuditApplication()
        self._controller = AssetAuditController()
        return (self._application,)

    def contributions(self):
        if self._application is None:
            self.applications()
        return asset_audit_contributions(
            self._application,
            self._controller,
        )


APPLICATION_PROVIDER = AssetAuditApplicationProvider()
