"""Resultado estruturado da validação RSC."""

from dataclasses import dataclass
from enum import Enum


class ValidationSeverity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


@dataclass(frozen=True, slots=True)
class ValidationIssue:
    code: str
    severity: ValidationSeverity
    message: str
    entity_type: str
    entity_id: str
    field: str | None = None


@dataclass(frozen=True, slots=True)
class RscValidationResult:
    issues: tuple[ValidationIssue, ...]

    @property
    def error_count(self) -> int:
        return sum(
            issue.severity is ValidationSeverity.ERROR
            for issue in self.issues
        )

    @property
    def warning_count(self) -> int:
        return sum(
            issue.severity is ValidationSeverity.WARNING
            for issue in self.issues
        )

    @property
    def is_valid(self) -> bool:
        return self.error_count == 0
