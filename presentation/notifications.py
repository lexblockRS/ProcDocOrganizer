"""Distribuição transitória de notificações da apresentação."""

from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)

__all__ = [
    "Notification",
    "NotificationCenter",
    "NotificationLevel",
]


class NotificationLevel(str, Enum):
    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"


@dataclass(frozen=True, slots=True)
class Notification:
    level: NotificationLevel
    title: str
    message: str
    timeout: float | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.level, NotificationLevel):
            raise TypeError("level deve ser NotificationLevel.")
        if not isinstance(self.title, str) or not self.title.strip():
            raise ValueError("title deve ser string não vazia.")
        if not isinstance(self.message, str) or not self.message.strip():
            raise ValueError("message deve ser string não vazia.")
        if self.timeout is not None:
            if isinstance(self.timeout, bool) or not isinstance(
                self.timeout, (int, float)
            ):
                raise TypeError(
                    "timeout deve ser número não negativo ou None."
                )
            if self.timeout < 0:
                raise ValueError("timeout não pode ser negativo.")
            object.__setattr__(self, "timeout", float(self.timeout))
        object.__setattr__(self, "title", self.title.strip())
        object.__setattr__(self, "message", self.message.strip())

    def to_dict(self) -> dict[str, object]:
        return {
            "level": self.level.value,
            "title": self.title,
            "message": self.message,
            "timeout": self.timeout,
        }


NotificationObserver = Callable[[Notification], None]


class NotificationCenter:
    """Distribui notificações sem reter os eventos publicados."""

    __slots__ = ("_observers",)

    def __init__(self) -> None:
        self._observers: list[NotificationObserver] = []

    def subscribe(
        self, observer: NotificationObserver
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

    def publish(self, notification: Notification) -> None:
        if not isinstance(notification, Notification):
            raise TypeError("notification deve ser Notification.")
        for observer in tuple(self._observers):
            try:
                observer(notification)
            except Exception:
                logger.exception("Observer de notificação falhou.")
