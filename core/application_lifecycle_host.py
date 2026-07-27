"""Coordenação neutra do lifecycle de uma sessão da plataforma."""

class ApplicationLifecycleHost:
    """Ativa e descarta runtimes sem expor hooks aos controllers."""

    def activate_session(self, session: object) -> None:
        runtime = self._runtime(session)
        if runtime is None:
            return
        try:
            runtime.activate()
        except Exception:
            self._dispose_runtime(runtime)
            raise

    def dispose_session(self, session: object) -> None:
        runtime = self._runtime(session)
        if runtime is not None:
            self._dispose_runtime(runtime)

    @staticmethod
    def _dispose_runtime(runtime: object) -> None:
        runtime.dispose()

    @staticmethod
    def _runtime(session: object):
        if session is None:
            return None
        platform_session = getattr(session, "platform_session", None)
        return getattr(platform_session, "application_runtime", None)
