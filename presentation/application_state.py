"""Estado operacional, global e estritamente pertencente à apresentação."""

from collections.abc import Callable
from dataclasses import dataclass, replace
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class ApplicationState(str, Enum):
    NO_PROJECT = "no_project"
    PROJECT_OPEN = "project_open"
    PROJECT_MODIFIED = "project_modified"
    BUSY = "busy"
    ERROR = "error"
    CLOSING = "closing"


class InvalidApplicationStateTransition(RuntimeError):
    """A transição solicitada viola o contrato do estado da UI."""


@dataclass(frozen=True, slots=True)
class ApplicationStateSnapshot:
    state: ApplicationState = ApplicationState.NO_PROJECT
    previous_state: ApplicationState | None = None
    active_operation_id: str | None = None
    project_id: str | None = None
    has_project: bool = False
    is_modified: bool = False
    error: str | None = None
    revision: int = 0

    def __post_init__(self) -> None:
        if not isinstance(self.state, ApplicationState):
            raise TypeError("state deve ser ApplicationState.")
        if self.previous_state is not None and not isinstance(
            self.previous_state, ApplicationState
        ):
            raise TypeError("previous_state deve ser ApplicationState.")
        if isinstance(self.revision, bool) or not isinstance(self.revision, int):
            raise TypeError("revision deve ser inteiro.")
        if self.revision < 0:
            raise ValueError("revision não pode ser negativa.")
        self._validate_invariants()

    def _validate_invariants(self) -> None:
        if self.state is ApplicationState.NO_PROJECT:
            if self.has_project or self.project_id is not None or self.is_modified:
                raise ValueError("NO_PROJECT não pode possuir projeto.")
        elif self.state is ApplicationState.PROJECT_OPEN:
            if not self.has_project or self.project_id is None or self.is_modified:
                raise ValueError("PROJECT_OPEN exige projeto não modificado.")
        elif self.state is ApplicationState.PROJECT_MODIFIED:
            if not self.has_project or self.project_id is None or not self.is_modified:
                raise ValueError("PROJECT_MODIFIED exige projeto modificado.")
        elif self.state is ApplicationState.BUSY:
            if self.previous_state is None or not self.active_operation_id:
                raise ValueError("BUSY exige estado anterior e operação ativa.")
            if self.previous_state in (
                ApplicationState.BUSY,
                ApplicationState.CLOSING,
            ):
                raise ValueError("BUSY possui estado anterior inválido.")
        elif self.state is ApplicationState.ERROR and not self.error:
            raise ValueError("ERROR exige descrição do erro.")

        if (
            self.state is not ApplicationState.BUSY
            and self.active_operation_id is not None
        ):
            raise ValueError("somente BUSY pode possuir operação ativa.")
        if (
            self.state not in (ApplicationState.BUSY, ApplicationState.ERROR)
            and self.previous_state is not None
        ):
            raise ValueError(
                "estado anterior só é preservado em BUSY ou ERROR."
            )
        if self.state is not ApplicationState.ERROR and self.error is not None:
            raise ValueError("somente ERROR pode possuir descrição de erro.")
        if self.has_project != (self.project_id is not None):
            raise ValueError("has_project deve corresponder a project_id.")


StateObserver = Callable[[ApplicationStateSnapshot], None]

_DIRECT_TRANSITIONS = {
    ApplicationState.NO_PROJECT: frozenset(
        (
            ApplicationState.PROJECT_OPEN,
            ApplicationState.ERROR,
            ApplicationState.CLOSING,
        )
    ),
    ApplicationState.PROJECT_OPEN: frozenset(
        (
            ApplicationState.NO_PROJECT,
            ApplicationState.PROJECT_MODIFIED,
            ApplicationState.ERROR,
            ApplicationState.CLOSING,
        )
    ),
    ApplicationState.PROJECT_MODIFIED: frozenset(
        (
            ApplicationState.NO_PROJECT,
            ApplicationState.PROJECT_OPEN,
            ApplicationState.ERROR,
            ApplicationState.CLOSING,
        )
    ),
    ApplicationState.ERROR: frozenset(
        (
            ApplicationState.NO_PROJECT,
            ApplicationState.PROJECT_OPEN,
            ApplicationState.PROJECT_MODIFIED,
            ApplicationState.CLOSING,
        )
    ),
    ApplicationState.BUSY: frozenset(),
    ApplicationState.CLOSING: frozenset(),
}

_OPERATION_SOURCE_STATES = frozenset(
    (
        ApplicationState.NO_PROJECT,
        ApplicationState.PROJECT_OPEN,
        ApplicationState.PROJECT_MODIFIED,
    )
)


class ApplicationStateStore:
    """Único proprietário do snapshot operacional da apresentação."""

    def __init__(self) -> None:
        self._snapshot = ApplicationStateSnapshot()
        self._observers: list[StateObserver] = []

    @property
    def snapshot(self) -> ApplicationStateSnapshot:
        return self._snapshot

    def subscribe(self, observer: StateObserver) -> Callable[[], None]:
        if not callable(observer):
            raise TypeError("observer deve ser chamável.")
        if observer not in self._observers:
            self._observers.append(observer)

        def unsubscribe() -> None:
            try:
                self._observers.remove(observer)
            except ValueError:
                pass

        return unsubscribe

    def transition_to(
        self,
        state: ApplicationState,
        *,
        project_id: str | None = None,
        error: str | None = None,
    ) -> ApplicationStateSnapshot:
        if not isinstance(state, ApplicationState):
            raise TypeError("state deve ser ApplicationState.")
        source = self._snapshot.state
        if state not in _DIRECT_TRANSITIONS[source]:
            self._reject(source, state)
        try:
            candidate = self._snapshot_for_state(
                state, project_id=project_id, error=error
            )
        except (TypeError, ValueError) as exc:
            self._reject(source, state, str(exc))
        return self._commit(candidate, "mudança de estado")

    def begin_operation(self, operation_id: str) -> ApplicationStateSnapshot:
        normalized = self._required_text(operation_id, "operation_id")
        source = self._snapshot.state
        if source not in _OPERATION_SOURCE_STATES:
            self._reject(source, ApplicationState.BUSY)
        candidate = replace(
            self._snapshot,
            state=ApplicationState.BUSY,
            previous_state=source,
            active_operation_id=normalized,
            error=None,
            revision=self._snapshot.revision + 1,
        )
        logger.info("Início de operação da UI: %s.", normalized)
        return self._commit(candidate, "início de operação")

    def complete_operation(
        self,
        operation_id: str,
        *,
        resulting_state: ApplicationState | None = None,
        project_id: str | None = None,
    ) -> ApplicationStateSnapshot:
        self._require_active_operation(operation_id)
        target = resulting_state or self._snapshot.previous_state
        if target not in (
            ApplicationState.NO_PROJECT,
            ApplicationState.PROJECT_OPEN,
            ApplicationState.PROJECT_MODIFIED,
        ):
            self._reject(ApplicationState.BUSY, target)
        try:
            candidate = self._snapshot_for_state(
                target, project_id=project_id
            )
        except (TypeError, ValueError) as exc:
            self._reject(ApplicationState.BUSY, target, str(exc))
        logger.info("Fim de operação da UI: %s.", operation_id)
        return self._commit(candidate, "fim de operação")

    def fail_operation(
        self, operation_id: str, error: str
    ) -> ApplicationStateSnapshot:
        self._require_active_operation(operation_id)
        normalized_error = self._required_text(error, "error")
        candidate = ApplicationStateSnapshot(
            state=ApplicationState.ERROR,
            previous_state=self._snapshot.previous_state,
            project_id=self._snapshot.project_id,
            has_project=self._snapshot.has_project,
            is_modified=self._snapshot.is_modified,
            error=normalized_error,
            revision=self._snapshot.revision + 1,
        )
        logger.error("Operação da UI terminou com erro: %s.", operation_id)
        return self._commit(candidate, "falha de operação")

    def cancel_operation(
        self, operation_id: str
    ) -> ApplicationStateSnapshot:
        self._require_active_operation(operation_id)
        candidate = ApplicationStateSnapshot(
            state=self._snapshot.previous_state,
            project_id=self._snapshot.project_id,
            has_project=self._snapshot.has_project,
            is_modified=self._snapshot.is_modified,
            revision=self._snapshot.revision + 1,
        )
        logger.info("Cancelamento de operação da UI: %s.", operation_id)
        return self._commit(candidate, "cancelamento de operação")

    def _snapshot_for_state(
        self,
        state: ApplicationState,
        *,
        project_id: str | None = None,
        error: str | None = None,
    ) -> ApplicationStateSnapshot:
        revision = self._snapshot.revision + 1
        if state is ApplicationState.NO_PROJECT:
            return ApplicationStateSnapshot(revision=revision)
        if state in (
            ApplicationState.PROJECT_OPEN,
            ApplicationState.PROJECT_MODIFIED,
        ):
            selected_project = (
                project_id
                if project_id is not None
                else self._snapshot.project_id
            )
            selected_project = self._required_text(
                selected_project, "project_id"
            )
            return ApplicationStateSnapshot(
                state=state,
                project_id=selected_project,
                has_project=True,
                is_modified=state is ApplicationState.PROJECT_MODIFIED,
                revision=revision,
            )
        if state is ApplicationState.ERROR:
            return ApplicationStateSnapshot(
                state=state,
                previous_state=self._snapshot.state,
                project_id=self._snapshot.project_id,
                has_project=self._snapshot.has_project,
                is_modified=self._snapshot.is_modified,
                error=self._required_text(error, "error"),
                revision=revision,
            )
        if state is ApplicationState.CLOSING:
            return ApplicationStateSnapshot(
                state=state,
                project_id=self._snapshot.project_id,
                has_project=self._snapshot.has_project,
                is_modified=self._snapshot.is_modified,
                revision=revision,
            )
        self._reject(self._snapshot.state, state)

    def _require_active_operation(self, operation_id: str) -> None:
        normalized = self._required_text(operation_id, "operation_id")
        if (
            self._snapshot.state is not ApplicationState.BUSY
            or self._snapshot.active_operation_id != normalized
        ):
            self._reject(
                self._snapshot.state,
                self._snapshot.previous_state or self._snapshot.state,
                "operação ativa não corresponde ao identificador informado",
            )

    def _commit(
        self, candidate: ApplicationStateSnapshot, reason: str
    ) -> ApplicationStateSnapshot:
        previous = self._snapshot
        self._snapshot = candidate
        logger.info(
            "Estado da UI alterado (%s): %s -> %s; revisão %d.",
            reason,
            previous.state.value,
            candidate.state.value,
            candidate.revision,
        )
        for observer in tuple(self._observers):
            try:
                observer(candidate)
            except Exception:
                logger.exception("Observer do estado da UI falhou.")
        return candidate

    @staticmethod
    def _required_text(value: object, field: str) -> str:
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{field} é obrigatório.")
        return value.strip()

    def _reject(
        self,
        source: ApplicationState,
        target: ApplicationState,
        detail: str | None = None,
    ) -> None:
        message = f"transição inválida: {source.value} -> {target.value}"
        if detail:
            message = f"{message}: {detail}"
        logger.warning(message)
        raise InvalidApplicationStateTransition(message)
