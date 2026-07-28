"""Dependências RSC com lifetime associado a um projeto aberto."""

from dataclasses import dataclass

from applications.rsc.assemblers import (
    FunctionalAssignmentEvidenceAssembler,
    ManualFunctionalExerciseAssembler,
)
from applications.rsc.ports import (
    ActivityRepository,
    FunctionalAssignmentEvidenceRepository,
    FunctionalExerciseRepository,
    ProjectRepository,
)
from applications.rsc.services import (
    CreateActivityService,
    CreateFunctionalAssignmentEvidenceService,
    CreateFunctionalExerciseService,
    CreateProjectService,
    FunctionalAssignmentNormalizer,
    ListFunctionalAssignmentEvidencesService,
    ListFunctionalExercisesService,
    RscActivityService,
    RscDocumentService,
    RscEvidenceService,
    RscProcessService,
    RscScoringService,
    RscValidationService,
)
from applications.rsc.catalogs import OfficialRscCatalog
from applications.rsc.use_cases import RscUseCaseRegistry

@dataclass(frozen=True)
class RscProjectSession:
    """Componentes RSC pertencentes a uma sessão de projeto."""

    activity_repository: ActivityRepository
    project_repository: ProjectRepository
    functional_exercise_repository: FunctionalExerciseRepository
    functional_assignment_evidence_repository: (
        FunctionalAssignmentEvidenceRepository
    )
    manual_functional_exercise_assembler: ManualFunctionalExerciseAssembler
    functional_assignment_evidence_assembler: (
        FunctionalAssignmentEvidenceAssembler
    )
    functional_assignment_normalizer: FunctionalAssignmentNormalizer
    create_activity_service: CreateActivityService
    create_project_service: CreateProjectService
    create_functional_exercise_service: CreateFunctionalExerciseService
    create_functional_assignment_evidence_service: (
        CreateFunctionalAssignmentEvidenceService
    )
    list_functional_assignment_evidences_service: (
        ListFunctionalAssignmentEvidencesService
    )
    list_functional_exercises_service: ListFunctionalExercisesService
    official_catalog: OfficialRscCatalog
    rsc_process_service: RscProcessService
    rsc_activity_service: RscActivityService
    rsc_document_service: RscDocumentService
    rsc_evidence_service: RscEvidenceService
    rsc_scoring_service: RscScoringService
    rsc_validation_service: RscValidationService
    use_cases: RscUseCaseRegistry

    def dispose(self) -> None:
        """Libera exclusivamente o estado transitório mantido em memória."""

        self.use_cases.dispose()
        self.rsc_process_service.clear()
        self.rsc_evidence_service.clear()
        self.rsc_document_service.clear()
