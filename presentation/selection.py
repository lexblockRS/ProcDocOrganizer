"""Contrato imutável da seleção global da camada de apresentação."""

from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from enum import Enum
import logging
from types import MappingProxyType
from typing import TypeAlias

logger = logging.getLogger(__name__)

__all__ = [
    "InvalidSelectionContext",
    "InvalidSelectionIdentity",
    "SelectionContext",
    "SelectionContractError",
    "SelectionIdentity",
    "SelectionKind",
    "SelectionSnapshot",
    "SelectionStore",
]


class SelectionKind(str, Enum):
    NONE = "none"
    PROCESS = "process"
    DOCUMENT = "document"
    ACTIVITY = "activity"
    EVIDENCE = "evidence"
    EXECUTION_FACT = "execution_fact"
    FUNCTIONAL_ASSIGNMENT = "functional_assignment"
    FUNCTIONAL_EXERCISE = "functional_exercise"
    REQUIREMENT = "requirement"
    CRITERION = "criterion"
    EVALUATION = "evaluation"
    REPORT = "report"


class SelectionContractError(ValueError):
    """Valor incompatível com o contrato de seleção."""


class InvalidSelectionIdentity(SelectionContractError):
    """Kind e identifier não formam uma identidade válida."""


class InvalidSelectionContext(SelectionContractError):
    """Contexto ou metadata não são valores de apresentação válidos."""


@dataclass(frozen=True, slots=True)
class SelectionIdentity:
    kind: SelectionKind
    identifier: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.kind, SelectionKind):
            raise InvalidSelectionIdentity(
                "kind deve ser SelectionKind."
            )
        if self.kind is SelectionKind.NONE:
            if self.identifier not in (None, ""):
                raise InvalidSelectionIdentity(
                    "NONE não aceita identificador."
                )
            object.__setattr__(self, "identifier", None)
            return
        if not isinstance(self.identifier, str):
            raise InvalidSelectionIdentity(
                "identifier deve ser string."
            )
        normalized = self.identifier.strip()
        if not normalized:
            raise InvalidSelectionIdentity(
                "identifier é obrigatório para seleção real."
            )
        object.__setattr__(self, "identifier", normalized)

    @classmethod
    def none(cls) -> "SelectionIdentity":
        return cls(SelectionKind.NONE)


MetadataScalar: TypeAlias = str | int | float | bool | None
MetadataValue: TypeAlias = (
    MetadataScalar
    | tuple["MetadataValue", ...]
    | frozenset["MetadataValue"]
    | Mapping[str, "MetadataValue"]
)


def _freeze_metadata_value(value: object, path: str) -> MetadataValue:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, tuple):
        return tuple(
            _freeze_metadata_value(item, f"{path}[]") for item in value
        )
    if isinstance(value, frozenset):
        try:
            return frozenset(
                _freeze_metadata_value(item, f"{path}[]")
                for item in value
            )
        except TypeError as exc:
            raise InvalidSelectionContext(
                f"{path} contém valor não hashable."
            ) from exc
    if isinstance(value, Mapping):
        frozen: dict[str, MetadataValue] = {}
        for key, item in value.items():
            if not isinstance(key, str) or not key.strip():
                raise InvalidSelectionContext(
                    f"{path} exige chaves textuais não vazias."
                )
            normalized_key = key.strip()
            if normalized_key in frozen:
                raise InvalidSelectionContext(
                    f"{path} contém chave duplicada após normalização."
                )
            frozen[normalized_key] = _freeze_metadata_value(
                item, f"{path}.{normalized_key}"
            )
        return MappingProxyType(frozen)
    raise InvalidSelectionContext(
        f"{path} contém tipo incompatível: {type(value).__name__}."
    )


def _freeze_metadata(
    metadata: Mapping[str, object],
) -> Mapping[str, MetadataValue]:
    if not isinstance(metadata, Mapping):
        raise InvalidSelectionContext("metadata deve ser um mapping.")
    frozen = _freeze_metadata_value(metadata, "metadata")
    if not isinstance(frozen, Mapping):
        raise InvalidSelectionContext("metadata deve ser um mapping.")
    return frozen


@dataclass(frozen=True, slots=True)
class SelectionContext:
    identity: SelectionIdentity
    display_name: str = ""
    metadata: Mapping[str, MetadataValue] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not isinstance(self.identity, SelectionIdentity):
            raise InvalidSelectionContext(
                "identity deve ser SelectionIdentity."
            )
        if not isinstance(self.display_name, str):
            raise InvalidSelectionContext(
                "display_name deve ser string."
            )
        normalized_name = self.display_name.strip()
        frozen_metadata = _freeze_metadata(self.metadata)
        if self.identity.kind is SelectionKind.NONE and (
            normalized_name or frozen_metadata
        ):
            raise InvalidSelectionContext(
                "contexto NONE deve usar representação canônica vazia."
            )
        object.__setattr__(self, "display_name", normalized_name)
        object.__setattr__(self, "metadata", frozen_metadata)

    @classmethod
    def none(cls) -> "SelectionContext":
        return cls(SelectionIdentity.none())


@dataclass(frozen=True, slots=True)
class SelectionSnapshot:
    selection: SelectionContext = field(
        default_factory=SelectionContext.none
    )
    revision: int = 0

    def __post_init__(self) -> None:
        if not isinstance(self.selection, SelectionContext):
            raise InvalidSelectionContext(
                "selection deve ser SelectionContext."
            )
        if isinstance(self.revision, bool) or not isinstance(
            self.revision, int
        ):
            raise InvalidSelectionContext("revision deve ser inteiro.")
        if self.revision < 0:
            raise InvalidSelectionContext(
                "revision não pode ser negativa."
            )


SelectionObserver = Callable[[SelectionSnapshot], None]


class SelectionStore:
    """Único proprietário da seleção global em uma composição."""

    def __init__(self) -> None:
        self._snapshot = SelectionSnapshot()
        self._observers: list[SelectionObserver] = []

    @property
    def snapshot(self) -> SelectionSnapshot:
        return self._snapshot

    def select(self, selection: SelectionContext) -> SelectionSnapshot:
        if not isinstance(selection, SelectionContext):
            logger.warning("Seleção recusada: contexto inválido.")
            raise InvalidSelectionContext(
                "selection deve ser SelectionContext."
            )
        if selection == self._snapshot.selection:
            return self._snapshot
        candidate = SelectionSnapshot(
            selection=selection,
            revision=self._snapshot.revision + 1,
        )
        return self._commit(candidate)

    def clear(self) -> SelectionSnapshot:
        return self.select(SelectionContext.none())

    def restore(self, selection: SelectionContext) -> SelectionSnapshot:
        """Restaura uma seleção histórica com revisão monotônica."""
        return self.select(selection)

    def subscribe(
        self, observer: SelectionObserver
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

    def _commit(self, candidate: SelectionSnapshot) -> SelectionSnapshot:
        previous = self._snapshot
        self._snapshot = candidate
        logger.info(
            "Seleção da UI alterada: %s -> %s; revisão %d.",
            previous.selection.identity.kind.value,
            candidate.selection.identity.kind.value,
            candidate.revision,
        )
        for observer in tuple(self._observers):
            try:
                observer(candidate)
            except Exception:
                logger.exception("Observer da seleção da UI falhou.")
        return candidate
