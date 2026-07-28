"""Consolidação operacional baseada exclusivamente em casos de uso."""

from datetime import datetime, timezone
from decimal import Decimal

from ._support import require_command
from .commands import (
    CalculateScoreCommand,
    GenerateSummaryCommand,
    GetProcessCommand,
    ListActivitiesCommand,
    ListDocumentsCommand,
    ListEvidenceByActivityCommand,
    ValidateProcessCommand,
)
from .process_summary import ProcessSummary
from .registry import RscUseCaseRegistry
from .results import SummaryUseCaseResult
from .activity_use_cases import ListActivitiesUseCase
from .document_use_cases import ListDocumentsUseCase
from .evidence_use_cases import ListEvidenceByActivityUseCase
from .process_use_cases import GetProcessUseCase
from .validation_scoring_use_cases import (
    CalculateScoreUseCase,
    ValidateProcessUseCase,
)


class GenerateSummaryUseCase:
    def __init__(self, use_cases: RscUseCaseRegistry) -> None:
        if not isinstance(use_cases, RscUseCaseRegistry):
            raise TypeError("use_cases deve ser RscUseCaseRegistry.")
        self._use_cases = use_cases

    def execute(
        self, command: GenerateSummaryCommand
    ) -> SummaryUseCaseResult:
        require_command(command, GenerateSummaryCommand)
        process_result = self._use_cases.get(GetProcessUseCase).execute(
            GetProcessCommand(command.process_id)
        )
        documents_result = self._use_cases.get(
            ListDocumentsUseCase
        ).execute(ListDocumentsCommand(command.process_id))
        activities_result = self._use_cases.get(
            ListActivitiesUseCase
        ).execute(ListActivitiesCommand(command.process_id))
        evidence = tuple(
            item
            for activity in activities_result.activities
            for item in self._use_cases.get(
                ListEvidenceByActivityUseCase
            ).execute(
                ListEvidenceByActivityCommand(
                    command.process_id, activity.id
                )
            ).evidence
        )
        validation_result = self._use_cases.get(
            ValidateProcessUseCase
        ).execute(ValidateProcessCommand(command.process_id))
        score_result = self._use_cases.get(
            CalculateScoreUseCase
        ).execute(CalculateScoreCommand(command.process_id))
        completed = sum(
            1
            for activity in activities_result.activities
            if activity.evidence_ids
        )
        total_activities = len(activities_result.activities)
        completion = (
            Decimal("0")
            if total_activities == 0
            else (
                Decimal(completed)
                / Decimal(total_activities)
                * Decimal("100")
            )
        )
        score_by_requirement = tuple(
            (item.requirement_id, item.total_score)
            for item in score_result.requirement_scores
        )
        generated_at = datetime.now(timezone.utc)
        summary = ProcessSummary(
            process_id=process_result.process_id,
            created_at=process_result.process.created_at,
            total_documents=len(documents_result.documents),
            total_activities=total_activities,
            total_evidence=len(evidence),
            total_requirements=len(score_result.requirement_scores),
            total_validation_errors=validation_result.error_count,
            total_validation_warnings=validation_result.warning_count,
            validation_result=validation_result,
            score_result=score_result,
            total_score=score_result.total_score,
            score_by_requirement=score_by_requirement,
            completion_percentage=completion,
            generated_at=generated_at,
        )
        return SummaryUseCaseResult(
            process_id=summary.process_id,
            generated_at=generated_at,
            summary=summary,
        )
