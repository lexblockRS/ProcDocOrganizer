"""Objetos de transferência da camada Application do ProcDoc RSC."""

from .activity import ActivityDTO
from .functional_assignment_evidence import (
    FunctionalAssignmentEvidenceDTO,
)
from .functional_exercise import FunctionalExerciseDTO
from .project import ProjectDTO

__all__ = [
    "ActivityDTO",
    "FunctionalAssignmentEvidenceDTO",
    "FunctionalExerciseDTO",
    "ProjectDTO",
]
