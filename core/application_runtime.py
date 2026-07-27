"""Estado neutro do runtime de uma Application."""

from dataclasses import dataclass
import logging

from contracts.application_descriptor import ApplicationDescriptor
from contracts.application_module import ApplicationModule
from contracts.lifecycle import (
    ApplicationLifecycleState,
    ApplicationLifecycleTransition,
)


logger = logging.getLogger(__name__)


@dataclass(slots=True)
class ApplicationRuntime:
    """Associa módulo, descriptor, lifecycle e futura sessão da Application."""

    descriptor: ApplicationDescriptor
    module: ApplicationModule | None
    lifecycle_state: ApplicationLifecycleState
    application_session: object | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.descriptor, ApplicationDescriptor):
            raise TypeError(
                "descriptor deve ser um ApplicationDescriptor."
            )
        if (
            self.module is not None
            and not isinstance(self.module, ApplicationModule)
        ):
            raise TypeError(
                "module deve implementar ApplicationModule ou ser None."
            )
        if (
            self.module is not None
            and self.module.descriptor != self.descriptor
        ):
            raise ValueError(
                "O descriptor do module deve coincidir com o runtime."
            )
        if not isinstance(
            self.lifecycle_state,
            ApplicationLifecycleState,
        ):
            raise TypeError(
                "lifecycle_state deve ser um ApplicationLifecycleState."
            )

    def prepare(self, context: object) -> None:
        """Prepara uma única vez o módulo associado ao projeto."""

        self._require_state(ApplicationLifecycleState.REGISTERED)
        if self.module is not None:
            self.module.prepare(context)
        try:
            self._transition_to(
                ApplicationLifecycleState.PROJECT_PREPARED
            )
        except Exception:
            self.dispose()
            raise

    def create_session(self, context: object) -> object | None:
        """Cria e publica atomicamente a sessão específica da Application."""

        self._require_state(
            ApplicationLifecycleState.PROJECT_PREPARED
        )
        try:
            application_session = (
                self.module.create_session(context)
                if self.module is not None
                else None
            )
            self.application_session = application_session
            self._transition_to(
                ApplicationLifecycleState.SESSION_CREATED
            )
        except Exception:
            self.dispose()
            raise
        return application_session

    def activate(self) -> None:
        """Registra a montagem da apresentação e ativa o módulo."""

        self._require_state(
            ApplicationLifecycleState.SESSION_CREATED
        )
        self._transition_to(
            ApplicationLifecycleState.PRESENTATION_MOUNTED
        )
        self._transition_to(ApplicationLifecycleState.ACTIVE)

    def dispose(self) -> None:
        """Descarta o módulo de forma idempotente e consistente."""

        if self.lifecycle_state is ApplicationLifecycleState.DISPOSED:
            return

        if self.lifecycle_state is ApplicationLifecycleState.ACTIVE:
            try:
                self._transition_to(
                    ApplicationLifecycleState.DEACTIVATING
                )
            except Exception:
                logger.exception(
                    "Falha na desativação da Application %s.",
                    self.descriptor.application_id,
                )

        try:
            if self.module is not None:
                self.module.dispose()
        except Exception:
            logger.exception(
                "Falha ao descartar a Application %s.",
                self.descriptor.application_id,
            )
        finally:
            self.application_session = None
            try:
                self._transition_to(
                    ApplicationLifecycleState.DISPOSED
                )
            except Exception:
                logger.exception(
                    "Falha ao notificar o descarte da Application %s.",
                    self.descriptor.application_id,
                )

    def _transition_to(
        self,
        target: ApplicationLifecycleState,
    ) -> None:
        transition = ApplicationLifecycleTransition(
            self.lifecycle_state,
            target,
        )
        self.lifecycle_state = target
        if self.module is not None:
            try:
                self.module.transition(transition)
            except Exception:
                logger.exception(
                    "Falha na transição %s -> %s da Application %s.",
                    transition.source.value,
                    transition.target.value,
                    self.descriptor.application_id,
                )

    def _require_state(
        self,
        expected: ApplicationLifecycleState,
    ) -> None:
        if self.lifecycle_state is not expected:
            raise RuntimeError(
                "Estado de lifecycle inválido: esperado "
                f"{expected.value}, atual {self.lifecycle_state.value}."
            )
