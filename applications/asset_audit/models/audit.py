from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import uuid4


@dataclass(frozen=True, slots=True)
class Audit:
    title: str
    status: str = "open"
    started_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    completed_at: datetime | None = None
    asset_ids: tuple[str, ...] = ()
    id: str = field(default_factory=lambda: str(uuid4()))

    def __post_init__(self):
        for name in ("id", "title", "status"):
            if not isinstance(getattr(self, name), str) or not getattr(
                self, name
            ).strip():
                raise ValueError(f"{name} deve ser um texto não vazio.")
        if self.started_at.tzinfo is None:
            raise ValueError("started_at deve possuir timezone.")
        if (
            self.completed_at is not None
            and self.completed_at.tzinfo is None
        ):
            raise ValueError("completed_at deve possuir timezone.")
        object.__setattr__(self, "asset_ids", tuple(self.asset_ids))
