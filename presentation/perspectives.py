"""Contrato declarativo das perspectivas da camada de apresentação."""

from collections.abc import Callable
from dataclasses import dataclass, field
import logging
from typing import Any

logger = logging.getLogger(__name__)

__all__ = [
    "DuplicatePerspective",
    "InvalidPerspectiveDefinition",
    "PerspectiveContractError",
    "PerspectiveDefinition",
    "PerspectiveId",
    "PerspectiveNotRegistered",
    "PerspectiveSnapshot",
    "PerspectiveStore",
]


class PerspectiveContractError(ValueError):
    """Valor incompatível com o contrato de perspectivas."""


class InvalidPerspectiveDefinition(PerspectiveContractError):
    """Uma definição não preserva as invariantes do contrato."""


class DuplicatePerspective(PerspectiveContractError):
    """O identificador ou o título já pertence a outra perspectiva."""


class PerspectiveNotRegistered(PerspectiveContractError):
    """A perspectiva consultada ou ativada não está registrada."""


@dataclass(frozen=True, slots=True)
class PerspectiveId:
    value: str

    def __post_init__(self) -> None:
        if not isinstance(self.value, str):
            raise PerspectiveContractError("value deve ser string.")
        normalized = self.value.strip()
        if not normalized:
            raise PerspectiveContractError("value não pode ser vazio.")
        object.__setattr__(self, "value", normalized)

    def to_dict(self) -> dict[str, str]:
        """Retorna uma representação composta apenas por dados simples."""
        return {"value": self.value}


PerspectiveFactory = Callable[[], Any]


@dataclass(frozen=True, slots=True)
class PerspectiveDefinition:
    id: PerspectiveId
    title: str
    order: int
    icon: str | None
    requires_project: bool
    factory: PerspectiveFactory = field(repr=False)

    def __post_init__(self) -> None:
        if not isinstance(self.id, PerspectiveId):
            raise InvalidPerspectiveDefinition(
                "id deve ser PerspectiveId."
            )
        if not isinstance(self.title, str) or not self.title.strip():
            raise InvalidPerspectiveDefinition(
                "title deve ser string não vazia."
            )
        if isinstance(self.order, bool) or not isinstance(self.order, int):
            raise InvalidPerspectiveDefinition("order deve ser inteiro.")
        if self.icon is not None and (
            not isinstance(self.icon, str) or not self.icon.strip()
        ):
            raise InvalidPerspectiveDefinition(
                "icon deve ser string não vazia ou None."
            )
        if not isinstance(self.requires_project, bool):
            raise InvalidPerspectiveDefinition(
                "requires_project deve ser booleano."
            )
        if not callable(self.factory):
            raise InvalidPerspectiveDefinition(
                "factory deve ser chamável."
            )
        object.__setattr__(self, "title", self.title.strip())
        if self.icon is not None:
            object.__setattr__(self, "icon", self.icon.strip())

    def to_dict(self) -> dict[str, object]:
        """Serializa os metadados declarativos, deliberadamente sem factory."""
        return {
            "id": self.id.to_dict(),
            "title": self.title,
            "order": self.order,
            "icon": self.icon,
            "requires_project": self.requires_project,
        }


@dataclass(frozen=True, slots=True)
class PerspectiveSnapshot:
    active: PerspectiveId | None = None
    available: tuple[PerspectiveDefinition, ...] = ()
    revision: int = 0

    def __post_init__(self) -> None:
        if self.active is not None and not isinstance(
            self.active, PerspectiveId
        ):
            raise PerspectiveContractError(
                "active deve ser PerspectiveId ou None."
            )
        if not isinstance(self.available, tuple) or any(
            not isinstance(item, PerspectiveDefinition)
            for item in self.available
        ):
            raise PerspectiveContractError(
                "available deve ser tuple de PerspectiveDefinition."
            )
        identifiers = tuple(item.id for item in self.available)
        if len(set(identifiers)) != len(identifiers):
            raise PerspectiveContractError(
                "available contém IDs duplicados."
            )
        titles = tuple(item.title.casefold() for item in self.available)
        if len(set(titles)) != len(titles):
            raise PerspectiveContractError(
                "available contém títulos conflitantes."
            )
        if self.active is not None and self.active not in identifiers:
            raise PerspectiveContractError(
                "active deve identificar uma perspectiva disponível."
            )
        if isinstance(self.revision, bool) or not isinstance(
            self.revision, int
        ):
            raise PerspectiveContractError("revision deve ser inteiro.")
        if self.revision < 0:
            raise PerspectiveContractError(
                "revision não pode ser negativa."
            )


PerspectiveObserver = Callable[[PerspectiveSnapshot], None]


class PerspectiveStore:
    """Único proprietário do catálogo e da perspectiva ativa."""

    def __init__(self) -> None:
        self._snapshot = PerspectiveSnapshot()
        self._observers: list[PerspectiveObserver] = []

    @property
    def snapshot(self) -> PerspectiveSnapshot:
        return self._snapshot

    def register(
        self, definition: PerspectiveDefinition
    ) -> PerspectiveSnapshot:
        if not isinstance(definition, PerspectiveDefinition):
            logger.warning("Registro de perspectiva recusado.")
            raise InvalidPerspectiveDefinition(
                "definition deve ser PerspectiveDefinition."
            )
        if self.contains(definition.id):
            raise DuplicatePerspective(
                f"ID já registrado: {definition.id.value}."
            )
        if any(
            item.title.casefold() == definition.title.casefold()
            for item in self._snapshot.available
        ):
            raise DuplicatePerspective(
                f"Título já registrado: {definition.title}."
            )
        available = tuple(
            sorted(
                (*self._snapshot.available, definition),
                key=lambda item: (
                    item.order,
                    item.title.casefold(),
                    item.id.value,
                ),
            )
        )
        return self._commit(
            PerspectiveSnapshot(
                active=self._snapshot.active,
                available=available,
                revision=self._snapshot.revision + 1,
            )
        )

    def get(self, perspective_id: PerspectiveId) -> PerspectiveDefinition:
        self._validate_id(perspective_id)
        for definition in self._snapshot.available:
            if definition.id == perspective_id:
                return definition
        raise PerspectiveNotRegistered(
            f"Perspectiva não registrada: {perspective_id.value}."
        )

    def list_all(self) -> tuple[PerspectiveDefinition, ...]:
        return self._snapshot.available

    def contains(self, perspective_id: PerspectiveId) -> bool:
        self._validate_id(perspective_id)
        return any(
            definition.id == perspective_id
            for definition in self._snapshot.available
        )

    def activate(self, perspective_id: PerspectiveId) -> PerspectiveSnapshot:
        self.get(perspective_id)
        if self._snapshot.active == perspective_id:
            return self._snapshot
        return self._commit(
            PerspectiveSnapshot(
                active=perspective_id,
                available=self._snapshot.available,
                revision=self._snapshot.revision + 1,
            )
        )

    def deactivate(self) -> PerspectiveSnapshot:
        if self._snapshot.active is None:
            return self._snapshot
        return self._commit(
            PerspectiveSnapshot(
                available=self._snapshot.available,
                revision=self._snapshot.revision + 1,
            )
        )

    def subscribe(
        self, observer: PerspectiveObserver
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

    @staticmethod
    def _validate_id(perspective_id: PerspectiveId) -> None:
        if not isinstance(perspective_id, PerspectiveId):
            raise PerspectiveContractError(
                "perspective_id deve ser PerspectiveId."
            )

    def _commit(
        self, candidate: PerspectiveSnapshot
    ) -> PerspectiveSnapshot:
        self._snapshot = candidate
        logger.info(
            "Perspectivas da UI alteradas; revisão %d.",
            candidate.revision,
        )
        for observer in tuple(self._observers):
            try:
                observer(candidate)
            except Exception:
                logger.exception("Observer de perspectivas da UI falhou.")
        return candidate
