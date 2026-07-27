"""Provider público da Application RSC."""

from .application import RscApplication
from .contributions import rsc_contributions
from .dashboard import rsc_dashboard_contributions


class RscApplicationProvider:
    def applications(self):
        return (RscApplication(),)

    def contributions(self):
        return (
            *rsc_contributions(),
            *rsc_dashboard_contributions(),
        )


APPLICATION_PROVIDER = RscApplicationProvider()
