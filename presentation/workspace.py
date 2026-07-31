"""Contrato lógico do espaço central da camada de apresentação."""

from collections.abc import Callable, Mapping
from dataclasses import dataclass, field, replace
from enum import Enum
import logging

from .perspectives import PerspectiveId, PerspectiveStore
from .navigation_contracts import (
    NavigationIntent,
    NavigationIntentType,
    Scalar,
    WorkspaceFilter,
    _freeze_scalars,
)
from .selection import SelectionContext

logger = logging.getLogger(__name__)

__all__ = [
    "InvalidWorkspacePerspective",
    "WorkspaceContractError",
    "WorkspaceSnapshot",
    "WorkspaceState",
    "WorkspaceStore",
]


class WorkspaceState(str, Enum):
    EMPTY = "empty"
    READY = "ready"


class WorkspaceContractError(ValueError):
    """Valor incompatível com o contrato lógico do Workspace."""


class InvalidWorkspacePerspective(WorkspaceContractError):
    """A perspectiva não pode ser montada no Workspace."""


@dataclass(frozen=True, slots=True)
class WorkspaceSnapshot:
    state: WorkspaceState = WorkspaceState.EMPTY
    active_perspective: PerspectiveId | None = None
    revision: int = 0
    workspace_id: str = "default"
    project_id: str | None = None
    selection: SelectionContext = field(default_factory=SelectionContext.none)
    active_filters: tuple[WorkspaceFilter, ...] = ()
    current_document: str | None = None
    current_evidence: str | None = None
    current_execution_fact: str | None = None
    current_requirement: str | None = None
    current_criterion: str | None = None
    current_evaluation: str | None = None
    metadata: Mapping[str, Scalar] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not isinstance(self.state, WorkspaceState):
            raise WorkspaceContractError(
                "state deve ser WorkspaceState."
            )
        if self.active_perspective is not None and not isinstance(
            self.active_perspective, PerspectiveId
        ):
            raise WorkspaceContractError(
                "active_perspective deve ser PerspectiveId ou None."
            )
        if self.state is WorkspaceState.EMPTY:
            if self.active_perspective is not None:
                raise WorkspaceContractError(
                    "Workspace EMPTY não pode possuir perspectiva."
                )
        elif self.active_perspective is None:
            raise WorkspaceContractError(
                "Workspace READY exige perspectiva ativa."
            )
        if isinstance(self.revision, bool) or not isinstance(
            self.revision, int
        ):
            raise WorkspaceContractError("revision deve ser inteiro.")
        if self.revision < 0:
            raise WorkspaceContractError(
                "revision não pode ser negativa."
            )
        if not isinstance(self.workspace_id, str) or not self.workspace_id.strip():
            raise WorkspaceContractError(
                "workspace_id deve ser string não vazia."
            )
        object.__setattr__(self, "workspace_id", self.workspace_id.strip())
        for name in (
            "project_id",
            "current_document",
            "current_evidence",
            "current_execution_fact",
            "current_requirement",
            "current_criterion",
            "current_evaluation",
        ):
            value = getattr(self, name)
            if value is not None and (
                not isinstance(value, str) or not value.strip()
            ):
                raise WorkspaceContractError(
                    f"{name} deve ser string não vazia ou None."
                )
            if isinstance(value, str):
                object.__setattr__(self, name, value.strip())
        if not isinstance(self.selection, SelectionContext):
            raise WorkspaceContractError(
                "selection deve ser SelectionContext."
            )
        if not isinstance(self.active_filters, tuple) or any(
            not isinstance(item, WorkspaceFilter)
            for item in self.active_filters
        ):
            raise WorkspaceContractError(
                "active_filters deve ser tuple de WorkspaceFilter."
            )
        if len({item.filter_id for item in self.active_filters}) != len(
            self.active_filters
        ):
            raise WorkspaceContractError(
                "active_filters contém IDs duplicados."
            )
        try:
            frozen_metadata = _freeze_scalars(self.metadata, "metadata")
        except ValueError as exc:
            raise WorkspaceContractError(str(exc)) from exc
        object.__setattr__(self, "metadata", frozen_metadata)

    @property
    def perspective(self) -> PerspectiveId | None:
        return self.active_perspective


WorkspaceObserver = Callable[[WorkspaceSnapshot], None]


class WorkspaceStore:
    """Proprietário da perspectiva logicamente montada no Workspace."""

    def __init__(self, perspective_store: PerspectiveStore) -> None:
        if not isinstance(perspective_store, PerspectiveStore):
            raise TypeError(
                "perspective_store deve ser PerspectiveStore."
            )
        self._perspective_store = perspective_store
        self._snapshot = WorkspaceSnapshot()
        self._observers: list[WorkspaceObserver] = []

    @property
    def snapshot(self) -> WorkspaceSnapshot:
        return self._snapshot

    def mount(self, perspective: PerspectiveId) -> WorkspaceSnapshot:
        if not isinstance(perspective, PerspectiveId):
            logger.warning("Montagem lógica recusada: ID inválido.")
            raise InvalidWorkspacePerspective(
                "perspective deve ser PerspectiveId."
            )
        if not self._perspective_store.contains(perspective):
            logger.warning(
                "Montagem lógica recusada: perspectiva não registrada."
            )
            raise InvalidWorkspacePerspective(
                f"Perspectiva não registrada: {perspective.value}."
            )
        if self._snapshot.active_perspective == perspective:
            return self._snapshot
        return self._commit(
            replace(
                self._snapshot,
                state=WorkspaceState.READY,
                active_perspective=perspective,
                revision=self._snapshot.revision + 1,
            )
        )

    def clear(self) -> WorkspaceSnapshot:
        if self._snapshot.state is WorkspaceState.EMPTY:
            return self._snapshot
        return self._commit(
            WorkspaceSnapshot(
                revision=self._snapshot.revision + 1,
                workspace_id=self._snapshot.workspace_id,
            )
        )

    def apply(
        self,
        intent: NavigationIntent,
        *,
        selection: SelectionContext | None = None,
    ) -> WorkspaceSnapshot:
        """Aplica o contexto produzido por uma intenção validada."""
        if not isinstance(intent, NavigationIntent):
            raise TypeError("intent deve ser NavigationIntent.")
        if selection is not None and not isinstance(selection, SelectionContext):
            raise TypeError("selection deve ser SelectionContext ou None.")
        field_by_intent = {
            NavigationIntentType.OPEN_DOCUMENT: "current_document",
            NavigationIntentType.OPEN_EVIDENCE: "current_evidence",
            NavigationIntentType.OPEN_EXECUTION_FACT: "current_execution_fact",
            NavigationIntentType.OPEN_REQUIREMENT: "current_requirement",
            NavigationIntentType.OPEN_CRITERION: "current_criterion",
            NavigationIntentType.OPEN_EVALUATION: "current_evaluation",
        }
        changes: dict[str, object] = {
            "project_id": intent.project_id or self._snapshot.project_id,
            "active_filters": intent.filters,
            "metadata": intent.metadata,
        }
        if selection is not None:
            changes["selection"] = selection
        target_field = field_by_intent.get(intent.intent_type)
        if target_field is not None:
            changes[target_field] = intent.target_id
        if all(
            getattr(self._snapshot, name) == value
            for name, value in changes.items()
        ):
            return self._snapshot
        return self._commit(replace(
            self._snapshot,
            **changes,
            revision=self._snapshot.revision + 1,
        ))

    def restore(self, snapshot: WorkspaceSnapshot) -> WorkspaceSnapshot:
        """Restaura o conteúdo de um snapshot com nova revisão do Store."""
        if not isinstance(snapshot, WorkspaceSnapshot):
            raise TypeError("snapshot deve ser WorkspaceSnapshot.")
        if (
            snapshot.active_perspective is not None
            and not self._perspective_store.contains(
                snapshot.active_perspective
            )
        ):
            raise InvalidWorkspacePerspective(
                "Perspectiva do snapshot não está registrada: "
                f"{snapshot.active_perspective.value}."
            )
        candidate = replace(
            snapshot, revision=self._snapshot.revision + 1
        )
        if replace(candidate, revision=self._snapshot.revision) == self._snapshot:
            return self._snapshot
        return self._commit(candidate)

    def subscribe(
        self, observer: WorkspaceObserver
    ) -> Callable[[], None]:
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

    def _commit(self, candidate: WorkspaceSnapshot) -> WorkspaceSnapshot:
        self._snapshot = candidate
        logger.info(
            "Workspace lógico alterado: %s; revisão %d.",
            candidate.state.value,
            candidate.revision,
        )
        for observer in tuple(self._observers):
            try:
                observer(candidate)
            except Exception:
                logger.exception("Observer do Workspace lógico falhou.")
        return candidate
