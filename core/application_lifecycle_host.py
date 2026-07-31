"""Autoridade neutra sobre o lifecycle da sessão ativa."""

from __future__ import annotations

from collections.abc import Callable


class ApplicationLifecycleHost:
    """Mantém zero ou uma sessão oficial, sem localizar dependências."""

    def __init__(self) -> None:
        self._current_session: object | None = None

    @property
    def current_session(self) -> object | None:
        return self._current_session

    def activate_session(
        self,
        session: object,
        *,
        after_publish: Callable[[object, object | None], None] | None = None,
        rollback: Callable[[object | None, object], None] | None = None,
    ) -> object | None:
        if session is None:
            raise ValueError("session não pode ser None.")
        if session is self._current_session:
            return session
        previous = self._current_session
        runtime = self._runtime(session)
        try:
            if runtime is not None:
                runtime.activate()
        except Exception:
            if runtime is not None:
                self._dispose_runtime(runtime)
            raise

        self._current_session = session
        try:
            if after_publish is not None:
                after_publish(session, previous)
        except Exception:
            self._current_session = previous
            try:
                if rollback is not None:
                    rollback(previous, session)
            finally:
                if runtime is not None:
                    self._dispose_runtime(runtime)
            raise

        if previous is not None:
            self._dispose_session_resources(previous)
        return previous

    def close_session(
        self,
        *,
        after_publish: Callable[[object], None] | None = None,
        rollback: Callable[[object], None] | None = None,
    ) -> object | None:
        previous = self._current_session
        if previous is None:
            return None
        self._current_session = None
        try:
            if after_publish is not None:
                after_publish(previous)
        except Exception:
            self._current_session = previous
            if rollback is not None:
                rollback(previous)
            raise
        self._dispose_session_resources(previous)
        return previous

    def dispose_session(self, session: object) -> None:
        if session is None:
            return
        if session is self._current_session:
            self._current_session = None
        self._dispose_session_resources(session)

    def _dispose_session_resources(self, session: object) -> None:
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
