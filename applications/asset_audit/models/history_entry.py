from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import uuid4


@dataclass(frozen=True, slots=True)
class HistoryEntry:
    entity_type: str
    entity_id: str
    event: str
    id: str = field(default_factory=lambda: str(uuid4()))
    occurred_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    def __post_init__(self):
        for name in ("id", "entity_type", "entity_id", "event"):
            if not isinstance(getattr(self, name), str) or not getattr(
                self, name
            ).strip():
                raise ValueError(f"{name} deve ser um texto não vazio.")
        if self.occurred_at.tzinfo is None:
            raise ValueError("occurred_at deve possuir timezone.")
