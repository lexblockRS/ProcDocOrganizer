"""Fronteira local de composição da sessão RSC."""

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from database import initialize_database

from applications.rsc.assemblers import (
    FunctionalAssignmentEvidenceAssembler,
    ManualFunctionalExerciseAssembler,
)
from applications.rsc.ports import (
    ActivityRepository,
    FunctionalAssignmentEvidenceRepository,
    FunctionalExerciseRepository,
    ProjectRepository,
    SourceEvidenceLookup,
)
from applications.rsc.repositories import (
    InMemoryActivityRepository,
    InMemoryFunctionalAssignmentEvidenceRepository,
    InMemoryFunctionalExerciseRepository,
    InMemoryProjectRepository,
    SQLiteFunctionalAssignmentEvidenceRepository,
    SQLiteActivityRepository,
    SQLiteFunctionalExerciseRepository,
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
from applications.rsc.infrastructure import (
    DocumentHashService,
    ProjectRepository as PdopProjectRepository,
)
from applications.rsc.services import DocumentHealthService
from applications.rsc.use_cases import (
    CalculateScoreUseCase,
    CreateActivityUseCase,
    CreateEvidenceUseCase,
    CreateProcessUseCase,
    GenerateSummaryUseCase,
    GetActivityUseCase,
    GetDocumentUseCase,
    GetEvidenceUseCase,
    GetProcessUseCase,
    ListActivitiesByCriterionUseCase,
    ListActivitiesByRequirementUseCase,
    ListActivitiesUseCase,
    ListDocumentsUseCase,
    ListEvidenceByActivityUseCase,
    ListEvidenceUseCase,
    ListProcessesUseCase,
    LoadProjectUseCase,
    RegisterDocumentUseCase,
    RemoveDocumentUseCase,
    RscUseCaseRegistry,
    SaveProjectUseCase,
    ValidateProcessUseCase,
    UpdateDocumentReferenceUseCase,
    VerifyDocumentsUseCase,
)

from .project_session import RscProjectSession


@dataclass(frozen=True)
class RscRepositories:
    """Repositories pertencentes a uma sessão de projeto RSC."""

    activity: ActivityRepository
    project: ProjectRepository
    functional_assignment_evidence: (
        FunctionalAssignmentEvidenceRepository
    )
    functional_exercise: FunctionalExerciseRepository


RscRepositoryFactory = Callable[[], RscRepositories]


def create_in_memory_rsc_repositories() -> RscRepositories:
    """Cria repositories em memória isolados para uma nova sessão."""

    return RscRepositories(
        activity=InMemoryActivityRepository(),
        project=InMemoryProjectRepository(),
        functional_assignment_evidence=(
            InMemoryFunctionalAssignmentEvidenceRepository()
        ),
        functional_exercise=InMemoryFunctionalExerciseRepository(),
    )


def create_sqlite_rsc_repositories(
    database_path: str | Path,
) -> RscRepositories:
    """Usa SQLite para atividades, atribuições e exercícios funcionais."""

    initialize_database(database_path)
    return RscRepositories(
        activity=SQLiteActivityRepository(database_path),
        project=InMemoryProjectRepository(),
        functional_assignment_evidence=(
            SQLiteFunctionalAssignmentEvidenceRepository(database_path)
        ),
        functional_exercise=SQLiteFunctionalExerciseRepository(
            database_path
        ),
    )


def create_rsc_project_session(
    source_evidence_lookup: SourceEvidenceLookup,
    repositories: RscRepositories | None = None,
) -> RscProjectSession:
    """Compõe serviços e sessão sobre repositories já escolhidos."""

    selected = (
        repositories
        if repositories is not None
        else create_in_memory_rsc_repositories()
    )
    manual_assembler = ManualFunctionalExerciseAssembler()
    assignment_assembler = FunctionalAssignmentEvidenceAssembler()
    normalizer = FunctionalAssignmentNormalizer()
    official_catalog = OfficialRscCatalog()
    process_service = RscProcessService()
    activity_service = RscActivityService(official_catalog)
    evidence_service = RscEvidenceService()
    validation_service = RscValidationService(official_catalog)
    scoring_service = RscScoringService(official_catalog)
    document_service = RscDocumentService()
    document_hash_service = DocumentHashService()
    document_health_service = DocumentHealthService(document_hash_service)
    use_cases = RscUseCaseRegistry()
    use_cases.register(CreateProcessUseCase(process_service))
    use_cases.register(RegisterDocumentUseCase(process_service, document_service))
    use_cases.register(GetProcessUseCase(process_service))
    use_cases.register(ListProcessesUseCase(process_service))
    use_cases.register(GetDocumentUseCase(process_service, document_service))
    use_cases.register(
        ListDocumentsUseCase(process_service, document_service)
    )
    use_cases.register(RemoveDocumentUseCase(process_service, document_service))
    use_cases.register(CreateActivityUseCase(process_service, activity_service))
    use_cases.register(GetActivityUseCase(process_service, activity_service))
    use_cases.register(
        ListActivitiesUseCase(process_service, activity_service)
    )
    use_cases.register(
        ListActivitiesByCriterionUseCase(
            process_service, activity_service
        )
    )
    use_cases.register(
        ListActivitiesByRequirementUseCase(
            process_service, activity_service
        )
    )
    use_cases.register(
        CreateEvidenceUseCase(
            process_service,
            activity_service,
            document_service,
            evidence_service,
        )
    )
    use_cases.register(
        GetEvidenceUseCase(
            process_service,
            activity_service,
            document_service,
            evidence_service,
        )
    )
    use_cases.register(
        ListEvidenceUseCase(
            process_service,
            activity_service,
            document_service,
            evidence_service,
        )
    )
    use_cases.register(
        ListEvidenceByActivityUseCase(
            process_service,
            activity_service,
            document_service,
            evidence_service,
        )
    )
    use_cases.register(
        ValidateProcessUseCase(
            process_service,
            document_service,
            evidence_service,
            validation_service,
        )
    )
    use_cases.register(
        CalculateScoreUseCase(
            process_service,
            scoring_service,
        )
    )
    use_cases.register(GenerateSummaryUseCase(use_cases))
    use_cases.register(
        VerifyDocumentsUseCase(document_service, document_health_service)
    )
    use_cases.register(
        UpdateDocumentReferenceUseCase(
            document_service, document_hash_service
        )
    )
    persistence_repository = PdopProjectRepository()
    use_cases.register(
        SaveProjectUseCase(
            process_service,
            document_service,
            evidence_service,
            official_catalog,
            persistence_repository,
        )
    )
    use_cases.register(
        LoadProjectUseCase(
            process_service,
            document_service,
            evidence_service,
            official_catalog,
            persistence_repository,
        )
    )

    return RscProjectSession(
        activity_repository=selected.activity,
        project_repository=selected.project,
        functional_exercise_repository=selected.functional_exercise,
        functional_assignment_evidence_repository=(
            selected.functional_assignment_evidence
        ),
        manual_functional_exercise_assembler=manual_assembler,
        functional_assignment_evidence_assembler=assignment_assembler,
        functional_assignment_normalizer=normalizer,
        create_activity_service=CreateActivityService(
            selected.activity,
            selected.functional_assignment_evidence,
            selected.functional_exercise,
        ),
        create_project_service=CreateProjectService(selected.project),
        create_functional_exercise_service=CreateFunctionalExerciseService(
            selected.functional_exercise,
            manual_assembler,
            selected.functional_assignment_evidence,
        ),
        create_functional_assignment_evidence_service=(
            CreateFunctionalAssignmentEvidenceService(
                source_evidence_lookup,
                selected.functional_assignment_evidence,
                assignment_assembler,
                normalizer,
            )
        ),
        list_functional_assignment_evidences_service=(
            ListFunctionalAssignmentEvidencesService(
                selected.functional_assignment_evidence
            )
        ),
        list_functional_exercises_service=ListFunctionalExercisesService(
            selected.functional_exercise
        ),
        official_catalog=official_catalog,
        rsc_process_service=process_service,
        rsc_activity_service=activity_service,
        rsc_document_service=document_service,
        rsc_evidence_service=evidence_service,
        rsc_scoring_service=scoring_service,
        rsc_validation_service=validation_service,
        use_cases=use_cases,
    )
