from dataclasses import dataclass, field
from uuid import uuid4


@dataclass(frozen=True, slots=True)
class Finding:
    audit_id: str
    title: str
    severity: str
    description: str = ""
    status: str = "pending"
    id: str = field(default_factory=lambda: str(uuid4()))

    def __post_init__(self):
        for name in ("id", "audit_id", "title", "severity", "status"):
            if not isinstance(getattr(self, name), str) or not getattr(
                self, name
            ).strip():
                raise ValueError(f"{name} deve ser um texto não vazio.")
        if not isinstance(self.description, str):
            raise TypeError("description deve ser uma string.")
