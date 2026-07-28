"""Critério oficial e suas variantes explícitas de pontuação."""

from collections.abc import Mapping
from dataclasses import dataclass, field
from decimal import Decimal
from types import MappingProxyType

from .enums import MeasurementUnit
from .identifiers import optional_text, positive_decimal, required_text


@dataclass(frozen=True, slots=True)
class CriterionScoreVariant:
    id: str
    label: str
    points_per_unit: Decimal
    qualifiers: Mapping[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "id", required_text(self.id, "id"))
        object.__setattr__(self, "label", required_text(self.label, "label"))
        object.__setattr__(
            self,
            "points_per_unit",
            positive_decimal(self.points_per_unit, "points_per_unit"),
        )
        normalized = {
            required_text(key, "qualifier key"): required_text(
                value, "qualifier value"
            )
            for key, value in dict(self.qualifiers).items()
        }
        object.__setattr__(
            self, "qualifiers", MappingProxyType(normalized)
        )


@dataclass(frozen=True, slots=True)
class RscCriterion:
    id: str
    requirement_id: str
    item_number: int
    description: str
    measurement_unit: MeasurementUnit
    display_order: int
    points_per_unit: Decimal | None = None
    score_variants: tuple[CriterionScoreVariant, ...] = ()
    notes: str | None = None
    active: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "id", required_text(self.id, "id"))
        object.__setattr__(
            self,
            "requirement_id",
            required_text(self.requirement_id, "requirement_id"),
        )
        if isinstance(self.item_number, bool) or self.item_number < 1:
            raise ValueError("item_number deve ser positivo.")
        if self.display_order != self.item_number:
            raise ValueError("display_order deve corresponder ao item.")
        object.__setattr__(
            self,
            "description",
            required_text(self.description, "description"),
        )
        if not isinstance(self.measurement_unit, MeasurementUnit):
            raise TypeError("measurement_unit deve ser MeasurementUnit.")
        variants = tuple(self.score_variants)
        object.__setattr__(self, "score_variants", variants)
        if (self.points_per_unit is None) == (not variants):
            raise ValueError(
                "critério deve usar pontos comuns ou variantes, exclusivamente."
            )
        if self.points_per_unit is not None:
            object.__setattr__(
                self,
                "points_per_unit",
                positive_decimal(self.points_per_unit, "points_per_unit"),
            )
        if len({variant.id for variant in variants}) != len(variants):
            raise ValueError("IDs de variantes não podem duplicar.")
        object.__setattr__(self, "notes", optional_text(self.notes, "notes"))
        if not isinstance(self.active, bool):
            raise TypeError("active deve ser bool.")

    def get_variant(self, variant_id: str) -> CriterionScoreVariant:
        for variant in self.score_variants:
            if variant.id == variant_id:
                return variant
        raise KeyError(f"variante inexistente: {variant_id}")
