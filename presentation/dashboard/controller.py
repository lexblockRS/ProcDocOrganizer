"""Coordenação do ciclo de apresentação do Dashboard."""

from .projections import DashboardProjection, DashboardState
from .service import DashboardService


class DashboardController:
    """Controla o estado visual sem expor a sessão à HomeView."""

    ERROR_MESSAGE = "Não foi possível carregar o resumo do projeto."

    def __init__(
        self,
        view,
        service_factory=DashboardService,
    ) -> None:
        self.view = view
        self._service_factory = service_factory
        self._service = None
        self.clear_session()

    def set_session(self, session) -> bool:
        self._session = session
        self._service = self._service_factory(session)
        return self.refresh()

    def clear_session(self) -> None:
        self._session = None
        self._service = None
        self._refresh_contributions(None)
        self.view.set_projection(DashboardProjection())

    def refresh(self) -> bool:
        if self._service is None:
            self.view.set_projection(DashboardProjection())
            return False
        project = self._service.project_summary()
        self.view.set_projection(DashboardProjection(
            state=DashboardState.LOADING,
            project=project,
        ))
        try:
            projection = self._service.build()
            self._refresh_contributions(self._session)
        except Exception:
            self.view.set_projection(DashboardProjection(
                state=DashboardState.ERROR,
                project=project,
                error_message=self.ERROR_MESSAGE,
            ))
            return False
        self.view.set_projection(projection)
        return True

    def _refresh_contributions(self, session) -> None:
        refresh = getattr(
            self.view,
            "refresh_dashboard_contributions",
            None,
        )
        if callable(refresh):
            refresh(session)
