"""Validação estrutural, sem criar regras normativas adicionais."""

from applications.rsc.catalogs import OfficialRscCatalog
from applications.rsc.domain import (
    ActivityStatus,
    DocumentStatus,
    RscActivity,
    RscDocument,
    RscEvidence,
    RscProcess,
    RscValidationResult,
    ValidationIssue,
    ValidationSeverity,
)


class RscValidationService:
    def __init__(self, catalog: OfficialRscCatalog) -> None:
        self._catalog = catalog

    @staticmethod
    def _issue(
        code,
        severity,
        message,
        entity_type,
        entity_id,
        field=None,
    ):
        return ValidationIssue(
            code, severity, message, entity_type, str(entity_id), field
        )

    def validate_activity(
        self,
        activity: RscActivity,
        evidence: tuple[RscEvidence, ...] = (),
    ) -> RscValidationResult:
        issues = []
        try:
            criterion = self._catalog.get_criterion(activity.criterion_id)
        except KeyError:
            criterion = None
            issues.append(self._issue(
                "activity.criterion.invalid",
                ValidationSeverity.ERROR,
                "O critério informado não existe.",
                "activity",
                activity.id,
                "criterion_id",
            ))
        if activity.quantity <= 0:
            issues.append(self._issue(
                "activity.quantity.invalid",
                ValidationSeverity.ERROR,
                "A quantidade deve ser positiva.",
                "activity",
                activity.id,
                "quantity",
            ))
        if criterion is not None:
            if criterion.score_variants and activity.score_variant_id is None:
                issues.append(self._issue(
                    "activity.variant.required",
                    ValidationSeverity.ERROR,
                    "O critério exige uma variante de pontuação.",
                    "activity",
                    activity.id,
                    "score_variant_id",
                ))
            elif criterion.score_variants:
                try:
                    criterion.get_variant(activity.score_variant_id)
                except KeyError:
                    issues.append(self._issue(
                        "activity.variant.invalid",
                        ValidationSeverity.ERROR,
                        "A variante de pontuação não existe.",
                        "activity",
                        activity.id,
                        "score_variant_id",
                    ))
            elif activity.score_variant_id is not None:
                issues.append(self._issue(
                    "activity.variant.forbidden",
                    ValidationSeverity.ERROR,
                    "O critério não aceita variante de pontuação.",
                    "activity",
                    activity.id,
                    "score_variant_id",
                ))
        if (
            activity.start_date is not None
            and activity.end_date is not None
            and activity.start_date > activity.end_date
        ):
            issues.append(self._issue(
                "activity.date_range.invalid",
                ValidationSeverity.ERROR,
                "O intervalo de datas é inválido.",
                "activity",
                activity.id,
                "start_date",
            ))
        linked_ids = {item.id for item in evidence}
        missing = set(activity.evidence_ids) - linked_ids
        if missing:
            issues.append(self._issue(
                "activity.evidence.reference_missing",
                ValidationSeverity.ERROR,
                "Há referência para evidência não fornecida.",
                "activity",
                activity.id,
                "evidence_ids",
            ))
        if not activity.evidence_ids:
            severity = (
                ValidationSeverity.ERROR
                if activity.status is ActivityStatus.COMPLETE
                else ValidationSeverity.WARNING
            )
            issues.append(self._issue(
                "activity.evidence.missing",
                severity,
                "A atividade não possui evidência.",
                "activity",
                activity.id,
                "evidence_ids",
            ))
        return RscValidationResult(tuple(issues))

    def validate_evidence(
        self, evidence: RscEvidence, activity: RscActivity | None = None
    ) -> RscValidationResult:
        issues = []
        if not evidence.document_ids:
            issues.append(self._issue(
                "evidence.documents.missing",
                ValidationSeverity.ERROR,
                "A evidência exige ao menos um documento.",
                "evidence",
                evidence.id,
                "document_ids",
            ))
        if len(set(evidence.document_ids)) != len(evidence.document_ids):
            issues.append(self._issue(
                "evidence.documents.duplicate",
                ValidationSeverity.ERROR,
                "A evidência contém documentos duplicados.",
                "evidence",
                evidence.id,
                "document_ids",
            ))
        if activity is not None and evidence.activity_id != activity.id:
            issues.append(self._issue(
                "evidence.activity.mismatch",
                ValidationSeverity.ERROR,
                "A evidência não corresponde à atividade.",
                "evidence",
                evidence.id,
                "activity_id",
            ))
        return RscValidationResult(tuple(issues))

    def validate_document(
        self, document: RscDocument
    ) -> RscValidationResult:
        issues = []
        if not document.file_name.strip():
            issues.append(self._issue(
                "document.file_name.missing",
                ValidationSeverity.ERROR,
                "O nome do arquivo é obrigatório.",
                "document",
                document.id,
                "file_name",
            ))
        if not isinstance(document.status, DocumentStatus):
            issues.append(self._issue(
                "document.status.invalid",
                ValidationSeverity.ERROR,
                "O status do documento é inválido.",
                "document",
                document.id,
                "status",
            ))
        return RscValidationResult(tuple(issues))

    def validate_process(
        self,
        process: RscProcess,
        evidence: tuple[RscEvidence, ...] = (),
        documents: tuple[RscDocument, ...] = (),
    ) -> RscValidationResult:
        issues = []
        if not process.applicant_name.strip():
            issues.append(self._issue(
                "process.applicant_name.missing",
                ValidationSeverity.ERROR,
                "O nome do requerente é obrigatório.",
                "process",
                process.id,
                "applicant_name",
            ))
        if not process.institution.strip():
            issues.append(self._issue(
                "process.institution.missing",
                ValidationSeverity.ERROR,
                "A instituição é obrigatória.",
                "process",
                process.id,
                "institution",
            ))
        activities = process.list_activities()
        if len({item.id for item in activities}) != len(activities):
            issues.append(self._issue(
                "process.activities.duplicate",
                ValidationSeverity.ERROR,
                "O processo contém atividades duplicadas.",
                "process",
                process.id,
                "activities",
            ))
        evidence_by_activity = {
            activity.id: tuple(
                item for item in evidence if item.activity_id == activity.id
            )
            for activity in activities
        }
        for activity in activities:
            issues.extend(
                self.validate_activity(
                    activity, evidence_by_activity[activity.id]
                ).issues
            )
        activity_ids = {item.id for item in activities}
        for item in evidence:
            activity = next(
                (value for value in activities if value.id == item.activity_id),
                None,
            )
            issues.extend(self.validate_evidence(item, activity).issues)
            if item.activity_id not in activity_ids:
                issues.append(self._issue(
                    "process.evidence.activity_missing",
                    ValidationSeverity.ERROR,
                    "A evidência referencia atividade ausente.",
                    "evidence",
                    item.id,
                    "activity_id",
                ))
        document_ids = {item.id for item in documents}
        if documents:
            missing = set(process.document_ids) - document_ids
            if missing:
                issues.append(self._issue(
                    "process.document.reference_missing",
                    ValidationSeverity.ERROR,
                    "Há referência para documento não fornecido.",
                    "process",
                    process.id,
                    "document_ids",
                ))
        for document in documents:
            issues.extend(self.validate_document(document).issues)
        return RscValidationResult(tuple(issues))
