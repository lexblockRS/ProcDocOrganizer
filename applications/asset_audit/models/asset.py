from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import uuid4


@dataclass(frozen=True, slots=True)
class Asset:
    name: str
    asset_type: str
    owner: str
    status: str = "active"
    id: str = field(default_factory=lambda: str(uuid4()))
    created_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    def __post_init__(self):
        for name in ("id", "name", "asset_type", "owner", "status"):
            if not isinstance(getattr(self, name), str) or not getattr(
                self, name
            ).strip():
                raise ValueError(f"{name} deve ser um texto não vazio.")
        if self.created_at.tzinfo is None:
            raise ValueError("created_at deve possuir timezone.")
