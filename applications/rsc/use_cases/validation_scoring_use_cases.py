"""Orquestração de validação e pontuação sem regras normativas próprias."""

from datetime import datetime, timezone

from applications.rsc.domain import ValidationSeverity
from applications.rsc.services import (
    RscDocumentService,
    RscEvidenceService,
    RscProcessService,
    RscScoringService,
    RscValidationService,
)

from ._support import require_command, require_uuid
from .commands import CalculateScoreCommand, ValidateProcessCommand
from .errors import DomainValidationError, ProcessNotFoundError
from .results import ScoreUseCaseResult, ValidationUseCaseResult


class _ProcessPipelineUseCase:
    def __init__(self, processes: RscProcessService) -> None:
        self._processes = processes

    def _get_process(self, process_id: str):
        normalized = require_uuid(process_id, "process_id")
        try:
            return self._processes.get_process(normalized)
        except KeyError as exc:
            raise ProcessNotFoundError(
                f"processo não encontrado: {normalized}"
            ) from exc


class ValidateProcessUseCase(_ProcessPipelineUseCase):
    def __init__(
        self,
        processes: RscProcessService,
        documents: RscDocumentService,
        evidence: RscEvidenceService,
        validation: RscValidationService,
    ) -> None:
        super().__init__(processes)
        self._documents = documents
        self._evidence = evidence
        self._validation = validation

    def execute(
        self, command: ValidateProcessCommand
    ) -> ValidationUseCaseResult:
        require_command(command, ValidateProcessCommand)
        process = self._get_process(command.process_id)
        evidence = tuple(
            item
            for activity in process.list_activities()
            for item in self._evidence.list_by_activity(activity)
        )
        documents = tuple(
            self._documents.get_document(document_id)
            for document_id in process.document_ids
        )
        result = self._validation.validate_process(
            process,
            evidence=evidence,
            documents=documents,
        )
        issues = tuple(result.issues)
        errors = tuple(
            issue
            for issue in issues
            if issue.severity is ValidationSeverity.ERROR
        )
        warnings = tuple(
            issue
            for issue in issues
            if issue.severity is ValidationSeverity.WARNING
        )
        return ValidationUseCaseResult(
            process_id=process.id,
            validated_at=datetime.now(timezone.utc),
            executed=True,
            is_valid=result.is_valid,
            issues=issues,
            errors=errors,
            warnings=warnings,
            error_count=result.error_count,
            warning_count=result.warning_count,
            validation=result,
        )


class CalculateScoreUseCase(_ProcessPipelineUseCase):
    def __init__(
        self,
        processes: RscProcessService,
        scoring: RscScoringService,
    ) -> None:
        super().__init__(processes)
        self._scoring = scoring

    def execute(
        self, command: CalculateScoreCommand
    ) -> ScoreUseCaseResult:
        require_command(command, CalculateScoreCommand)
        process = self._get_process(command.process_id)
        try:
            result = self._scoring.calculate_process(process)
        except (KeyError, TypeError, ValueError) as exc:
            raise DomainValidationError(str(exc)) from exc
        return ScoreUseCaseResult(
            process_id=process.id,
            calculated_at=result.calculated_at,
            total_score=result.total_score,
            requirement_scores=tuple(result.requirement_scores),
            warnings=tuple(result.warnings),
            score=result,
        )
