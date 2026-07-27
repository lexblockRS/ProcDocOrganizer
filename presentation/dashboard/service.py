"""Construção da projeção pronta do Dashboard."""

from models.project import LEGACY_APPLICATION_ID

from .projections import (
    DashboardProjection,
    DashboardState,
    DocumentSummaryProjection,
    EvidenceSummaryProjection,
    ProjectSummaryProjection,
)


class DashboardService:
    """Agrega exclusivamente dados oferecidos pelos serviços da sessão."""

    PROCESSED_STATUS = "processed"
    OCR_REQUIRED_STATUS = "ocr_required"
    FAILED_STATUS = "failed"

    def __init__(self, session) -> None:
        self._session = session

    def build(self) -> DashboardProjection:
        documents = tuple(
            self._session.document_service.list_documents()
        )
        evidence_count = self._session.evidence_service.count()
        return DashboardProjection(
            state=DashboardState.READY,
            project=self.project_summary(),
            documents=self._document_summary(documents),
            evidences=EvidenceSummaryProjection(
                total_evidences=evidence_count
            ),
        )

    def project_summary(self) -> ProjectSummaryProjection:
        project = self._session.project
        application = getattr(self._session, "application", None)
        application_name = (
            application.display_name
            if application is not None
            else (
                "ProcDocOrganizer"
                if project.application == LEGACY_APPLICATION_ID
                else project.application
            )
        )
        return ProjectSummaryProjection(
            project_name=project.project_name,
            project_path=str(project.project_path),
            application_id=project.application,
            application_name=application_name,
            created_at=project.created_at,
            last_opened_at=project.last_opened_at,
        )

    @classmethod
    def _document_summary(
        cls, documents
    ) -> DocumentSummaryProjection:
        processed = sum(
            item.processing_status == cls.PROCESSED_STATUS
            for item in documents
        )
        ocr_required = sum(
            item.processing_status == cls.OCR_REQUIRED_STATUS
            for item in documents
        )
        failed = sum(
            item.processing_status == cls.FAILED_STATUS
            for item in documents
        )
        total = len(documents)
        return DocumentSummaryProjection(
            total_documents=total,
            processed_documents=processed,
            pending_documents=(
                total - processed - ocr_required - failed
            ),
            ocr_required_documents=ocr_required,
            failed_documents=failed,
            processed_pages=sum(
                item.page_count
                for item in documents
                if item.has_processing_result
            ),
        )
