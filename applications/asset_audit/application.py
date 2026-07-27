"""ApplicationModule da Asset Audit."""

from platform_sdk import (
    ApplicationLifecycleState,
    ApplicationLifecycleTransition,
    SessionContext,
)

from .descriptor import ASSET_AUDIT_DESCRIPTOR
from .session import create_demo_session


class AssetAuditApplication:
    descriptor = ASSET_AUDIT_DESCRIPTOR

    def __init__(self):
        self.hook_log = []
        self.transitions = []
        self.application_session = None
        self._disposed = False

    @property
    def is_active(self):
        return (
            self.application_session is not None
            and self.application_session.is_active
            and not self._disposed
        )

    def prepare(self, context):
        if not isinstance(context, SessionContext):
            raise TypeError("context deve ser um SessionContext.")
        self.hook_log.append("prepare")

    def create_session(self, context):
        if not isinstance(context, SessionContext):
            raise TypeError("context deve ser um SessionContext.")
        self.hook_log.append("create_session")
        self.application_session = create_demo_session(context)
        self._disposed = False
        return self.application_session

    def contributions(self, session):
        return ()

    def transition(self, transition):
        if not isinstance(transition, ApplicationLifecycleTransition):
            raise TypeError(
                "transition deve ser ApplicationLifecycleTransition."
            )
        self.transitions.append(transition)
        if (
            transition.target
            is ApplicationLifecycleState.ACTIVE
            and self.application_session is not None
        ):
            self.application_session.activate()

    def dispose(self):
        if self._disposed:
            return
        self.hook_log.append("dispose")
        if self.application_session is not None:
            self.application_session.dispose()
        self.application_session = None
        self._disposed = True
