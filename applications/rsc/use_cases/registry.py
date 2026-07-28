"""Registro local dos casos de uso disponíveis em uma sessão RSC."""

from collections.abc import Iterator
from typing import TypeVar

from .errors import DuplicateEntityError, SessionDisposedError

T = TypeVar("T")


class RscUseCaseRegistry:
    """Armazena uma instância por tipo concreto e possui descarte explícito."""

    def __init__(self) -> None:
        self._instances: dict[type[object], object] = {}
        self._disposed = False

    @property
    def is_disposed(self) -> bool:
        return self._disposed

    def register(self, use_case: object) -> None:
        self._ensure_active()
        if use_case is None:
            raise TypeError("use_case não pode ser None.")
        use_case_type = type(use_case)
        if use_case_type in self._instances:
            raise DuplicateEntityError(
                f"caso de uso já registrado: {use_case_type.__name__}"
            )
        self._instances[use_case_type] = use_case

    def get(self, use_case_type: type[T]) -> T:
        self._ensure_active()
        if not isinstance(use_case_type, type):
            raise TypeError("use_case_type deve ser um tipo.")
        try:
            return self._instances[use_case_type]  # type: ignore[return-value]
        except KeyError as exc:
            raise KeyError(
                f"caso de uso não registrado: {use_case_type.__name__}"
            ) from exc

    def __iter__(self) -> Iterator[object]:
        self._ensure_active()
        return iter(tuple(self._instances.values()))

    def __len__(self) -> int:
        return len(self._instances)

    def dispose(self) -> None:
        self._instances.clear()
        self._disposed = True

    def _ensure_active(self) -> None:
        if self._disposed:
            raise SessionDisposedError(
                "o registro de casos de uso pertence a uma sessão descartada."
            )
