"""Requisito oficial do RSC."""

from dataclasses import dataclass

from .identifiers import required_text, requirement_id


@dataclass(frozen=True, slots=True)
class RscRequirement:
    id: str
    number: int
    title: str
    description: str
    display_order: int

    def __post_init__(self) -> None:
        if isinstance(self.number, bool) or self.number not in range(1, 7):
            raise ValueError("number deve estar entre 1 e 6.")
        if self.id != requirement_id(self.number):
            raise ValueError("id não corresponde ao número do requisito.")
        object.__setattr__(self, "title", required_text(self.title, "title"))
        object.__setattr__(
            self,
            "description",
            required_text(self.description, "description"),
        )
        if self.display_order != self.number:
            raise ValueError("display_order deve corresponder ao número.")
