"""Estados persistíveis do domínio normativo RSC."""

from enum import Enum


class RscProcessStatus(str, Enum):
    DRAFT = "draft"
    IN_PREPARATION = "in_preparation"
    READY_FOR_REVIEW = "ready_for_review"
    SUBMITTED = "submitted"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    ARCHIVED = "archived"


class ActivityStatus(str, Enum):
    DRAFT = "draft"
    COMPLETE = "complete"
    INCOMPLETE = "incomplete"
    EXCLUDED = "excluded"


class DocumentStatus(str, Enum):
    AVAILABLE = "available"
    MISSING = "missing"
    INVALID = "invalid"
    ARCHIVED = "archived"


class EvidenceStatus(str, Enum):
    PROPOSED = "proposed"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    NEEDS_REVIEW = "needs_review"


class MeasurementUnit(str, Enum):
    DESIGNATION = "designation"
    PROJECT = "project"
    PRODUCT = "product"
    EVENT = "event"
    COURSE = "course"
    PUBLICATION = "publication"
    AWARD = "award"
    PATENT = "patent"
    MANDATE = "mandate"
    SYSTEM = "system"
    RESEARCH_GROUP = "research_group"
    MONTH = "month"
    YEAR_OR_FRACTION_OVER_SIX_MONTHS = (
        "year_or_fraction_over_six_months"
    )
    TRAINING = "training"
    OTHER = "other"
