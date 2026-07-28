"""Execução síncrona e coordenada de operações da apresentação."""

from collections.abc import Callable
from dataclasses import dataclass
import logging
from threading import Event
from typing import Protocol, TypeVar

from .application_state import ApplicationStateStore

logger = logging.getLogger(__name__)

T_co = TypeVar("T_co", covariant=True)

__all__ = [
    "CancellationToken",
    "OperationCancelled",
    "OperationContext",
    "OperationExecutor",
    "OperationId",
    "OperationWork",
]


@dataclass(frozen=True, slots=True)
class OperationId:
    value: str

    def __post_init__(self) -> None:
        if not isinstance(self.value, str):
            raise TypeError("value deve ser string.")
        normalized = self.value.strip()
        if not normalized:
            raise ValueError("value não pode ser vazio.")
        object.__setattr__(self, "value", normalized)

    def to_dict(self) -> dict[str, str]:
        return {"value": self.value}


class OperationCancelled(RuntimeError):
    """A unidade de trabalho reconheceu um cancelamento cooperativo."""


class CancellationToken:
    """Sinalização cooperativa, idempotente e segura entre threads."""

    __slots__ = ("_event",)

    def __init__(self) -> None:
        self._event = Event()

    @property
    def is_cancellation_requested(self) -> bool:
        return self._event.is_set()

    def request_cancellation(self) -> None:
        self._event.set()

    def throw_if_cancellation_requested(self) -> None:
        if self.is_cancellation_requested:
            raise OperationCancelled("Operação cancelada.")


@dataclass(frozen=True, slots=True)
class OperationContext:
    operation_id: OperationId
    cancellation_token: CancellationToken

    def __post_init__(self) -> None:
        if not isinstance(self.operation_id, OperationId):
            raise TypeError("operation_id deve ser OperationId.")
        if not isinstance(self.cancellation_token, CancellationToken):
            raise TypeError(
                "cancellation_token deve ser CancellationToken."
            )


class OperationWork(Protocol[T_co]):
    def __call__(self, context: OperationContext, /) -> T_co:
        ...


class OperationExecutor:
    """Coordena uma operação sem possuir estado operacional autoritativo."""

    __slots__ = ("_application_state_store",)

    def __init__(
        self, application_state_store: ApplicationStateStore
    ) -> None:
        if not isinstance(application_state_store, ApplicationStateStore):
            raise TypeError(
                "application_state_store deve ser ApplicationStateStore."
            )
        self._application_state_store = application_state_store

    def execute(
        self,
        operation_id: OperationId,
        work: Callable[[OperationContext], T_co],
        cancellation_token: CancellationToken | None = None,
    ) -> T_co:
        if not isinstance(operation_id, OperationId):
            raise TypeError("operation_id deve ser OperationId.")
        if not callable(work):
            raise TypeError("work deve ser chamável.")
        if cancellation_token is None:
            cancellation_token = CancellationToken()
        elif not isinstance(cancellation_token, CancellationToken):
            raise TypeError(
                "cancellation_token deve ser CancellationToken ou None."
            )

        context = OperationContext(operation_id, cancellation_token)
        self._application_state_store.begin_operation(operation_id.value)

        try:
            cancellation_token.throw_if_cancellation_requested()
            result = work(context)
            cancellation_token.throw_if_cancellation_requested()
        except OperationCancelled:
            self._cancel_preserving_exception(operation_id)
            raise
        except Exception as error:
            logger.exception(
                "Falha inesperada durante unidade de trabalho: %s.",
                operation_id.value,
            )
            self._fail_preserving_exception(operation_id, error)
            raise

        self._application_state_store.complete_operation(
            operation_id.value
        )
        return result

    def _cancel_preserving_exception(
        self, operation_id: OperationId
    ) -> None:
        try:
            self._application_state_store.cancel_operation(
                operation_id.value
            )
        except Exception:
            logger.exception(
                "Falha secundária ao registrar cancelamento: %s.",
                operation_id.value,
            )

    def _fail_preserving_exception(
        self, operation_id: OperationId, error: Exception
    ) -> None:
        description = str(error).strip() or type(error).__name__
        try:
            self._application_state_store.fail_operation(
                operation_id.value,
                description,
            )
        except Exception:
            logger.exception(
                "Falha secundária ao registrar erro operacional: %s.",
                operation_id.value,
            )
