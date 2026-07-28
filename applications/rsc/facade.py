"""Ponto único de entrada da camada Application RSC."""

from .project_session import RscProjectSession
from .use_cases import (
    CalculateScoreCommand,
    CalculateScoreUseCase,
    CreateActivityCommand,
    CreateActivityUseCase,
    CreateEvidenceCommand,
    CreateEvidenceUseCase,
    CreateProcessCommand,
    CreateProcessUseCase,
    GenerateSummaryCommand,
    GenerateSummaryUseCase,
    RegisterDocumentCommand,
    RegisterDocumentUseCase,
    ValidateProcessCommand,
    ValidateProcessUseCase,
)


class RscApplicationFacade:
    """Delega cada operação ao Registry da sessão recebida."""

    __slots__ = ("_session",)

    def __init__(self, session: RscProjectSession) -> None:
        if not isinstance(session, RscProjectSession):
            raise TypeError("session deve ser RscProjectSession.")
        self._session = session

    def create_process(self, command: CreateProcessCommand):
        return self._execute(CreateProcessUseCase, command)

    def register_document(self, command: RegisterDocumentCommand):
        return self._execute(RegisterDocumentUseCase, command)

    def create_activity(self, command: CreateActivityCommand):
        return self._execute(CreateActivityUseCase, command)

    def create_evidence(self, command: CreateEvidenceCommand):
        return self._execute(CreateEvidenceUseCase, command)

    def validate_process(self, command: ValidateProcessCommand):
        return self._execute(ValidateProcessUseCase, command)

    def calculate_score(self, command: CalculateScoreCommand):
        return self._execute(CalculateScoreUseCase, command)

    def generate_summary(self, command: GenerateSummaryCommand):
        return self._execute(GenerateSummaryUseCase, command)

    def _execute(self, use_case_type, command):
        return self._session.use_cases.get(use_case_type).execute(command)
