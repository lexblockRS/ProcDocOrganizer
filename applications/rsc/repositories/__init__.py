"""Repositórios disponíveis para a camada Application do ProcDoc RSC."""

from .in_memory_activity_repository import InMemoryActivityRepository
from .in_memory_functional_assignment_evidence_repository import (
    DuplicateFunctionalAssignmentEvidenceError,
    InMemoryFunctionalAssignmentEvidenceRepository,
)
from .in_memory_functional_exercise_repository import (
    InMemoryFunctionalExerciseRepository,
)
from .in_memory_project_repository import InMemoryProjectRepository
from .sqlite_functional_assignment_evidence_repository import (
    SQLiteFunctionalAssignmentEvidenceRepository,
)
from .sqlite_activity_repository import SQLiteActivityRepository
from .sqlite_functional_exercise_repository import (
    SQLiteFunctionalExerciseRepository,
)

__all__ = [
    "InMemoryActivityRepository",
    "DuplicateFunctionalAssignmentEvidenceError",
    "InMemoryFunctionalAssignmentEvidenceRepository",
    "InMemoryFunctionalExerciseRepository",
    "InMemoryProjectRepository",
    "SQLiteFunctionalAssignmentEvidenceRepository",
    "SQLiteActivityRepository",
    "SQLiteFunctionalExerciseRepository",
]
