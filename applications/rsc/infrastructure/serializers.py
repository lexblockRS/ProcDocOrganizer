"""Serializers JSON externos ao domínio RSC."""

from datetime import date, datetime
from decimal import Decimal
from typing import Any

from applications.rsc.domain import (
    ActivityStatus,
    DocumentStatus,
    EvidenceStatus,
    RscActivity,
    RscDocument,
    RscEvidence,
    RscProcess,
    RscProcessStatus,
)


def _datetime(value: datetime) -> str:
    return value.isoformat()


def _optional_date(value: date | None) -> str | None:
    return None if value is None else value.isoformat()


def _read_datetime(value: Any, field: str) -> datetime:
    if not isinstance(value, str):
        raise ValueError(f"{field} deve ser uma data/hora ISO.")
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{field} deve ser uma data/hora ISO.") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError(f"{field} deve possuir fuso horário.")
    return parsed


def _read_date(value: Any, field: str) -> date | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError(f"{field} deve ser uma data ISO.")
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{field} deve ser uma data ISO.") from exc


def _mapping(value: Any, field: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{field} deve ser um objeto JSON.")
    return value


class ActivitySerializer:
    schema = "rsc.activity/1"

    @classmethod
    def dump(cls, value: RscActivity) -> dict[str, Any]:
        return {
            "id": value.id,
            "criterion_id": value.criterion_id,
            "title": value.title,
            "quantity": str(value.quantity),
            "description": value.description,
            "score_variant_id": value.score_variant_id,
            "start_date": _optional_date(value.start_date),
            "end_date": _optional_date(value.end_date),
            "status": value.status.value,
            "evidence_ids": list(value.evidence_ids),
            "notes": value.notes,
            "created_at": _datetime(value.created_at),
            "updated_at": _datetime(value.updated_at),
        }

    @classmethod
    def load(cls, raw: Any) -> RscActivity:
        data = _mapping(raw, "activity")
        return RscActivity(
            id=data["id"],
            criterion_id=data["criterion_id"],
            title=data["title"],
            quantity=Decimal(data["quantity"]),
            description=data.get("description"),
            score_variant_id=data.get("score_variant_id"),
            start_date=_read_date(data.get("start_date"), "start_date"),
            end_date=_read_date(data.get("end_date"), "end_date"),
            status=ActivityStatus(data["status"]),
            evidence_ids=tuple(data.get("evidence_ids", ())),
            notes=data.get("notes"),
            created_at=_read_datetime(data["created_at"], "created_at"),
            updated_at=_read_datetime(data["updated_at"], "updated_at"),
        )


class DocumentSerializer:
    schema = "rsc.document/1"

    @classmethod
    def dump(cls, value: RscDocument) -> dict[str, Any]:
        return {
            "id": value.id,
            "file_name": value.file_name,
            "original_path": value.original_path,
            "stored_path": value.stored_path,
            "mime_type": value.mime_type,
            "checksum": value.checksum,
            "document_date": _optional_date(value.document_date),
            "description": value.description,
            "status": value.status.value,
            "created_at": _datetime(value.created_at),
            "metadata": dict(value.metadata),
        }

    @classmethod
    def load(cls, raw: Any) -> RscDocument:
        data = _mapping(raw, "document")
        return RscDocument(
            id=data["id"],
            file_name=data["file_name"],
            original_path=data.get("original_path"),
            stored_path=data.get("stored_path"),
            mime_type=data.get("mime_type"),
            checksum=data.get("checksum"),
            document_date=_read_date(data.get("document_date"), "document_date"),
            description=data.get("description"),
            status=DocumentStatus(data["status"]),
            created_at=_read_datetime(data["created_at"], "created_at"),
            metadata=_mapping(data.get("metadata", {}), "metadata"),
        )


class EvidenceSerializer:
    schema = "rsc.evidence/1"

    @classmethod
    def dump(cls, value: RscEvidence) -> dict[str, Any]:
        return {
            "id": value.id,
            "activity_id": value.activity_id,
            "document_ids": list(value.document_ids),
            "description": value.description,
            "status": value.status.value,
            "justification": value.justification,
            "created_at": _datetime(value.created_at),
            "updated_at": _datetime(value.updated_at),
        }

    @classmethod
    def load(cls, raw: Any) -> RscEvidence:
        data = _mapping(raw, "evidence")
        return RscEvidence(
            id=data["id"],
            activity_id=data["activity_id"],
            document_ids=tuple(data["document_ids"]),
            description=data["description"],
            status=EvidenceStatus(data["status"]),
            justification=data.get("justification"),
            created_at=_read_datetime(data["created_at"], "created_at"),
            updated_at=_read_datetime(data["updated_at"], "updated_at"),
        )


class ProcessSerializer:
    schema = "rsc.process/1"

    @classmethod
    def dump(cls, value: RscProcess) -> dict[str, Any]:
        return {
            "id": value.id,
            "applicant_name": value.applicant_name,
            "institution": value.institution,
            "applicant_identifier": value.applicant_identifier,
            "status": value.status.value,
            "created_at": _datetime(value.created_at),
            "updated_at": _datetime(value.updated_at),
            "activity_ids": [item.id for item in value.activities],
            "document_ids": list(value.document_ids),
            "metadata": dict(value.metadata),
        }

    @classmethod
    def load(
        cls, raw: Any, activities_by_id: dict[str, RscActivity]
    ) -> RscProcess:
        data = _mapping(raw, "process")
        activity_ids = tuple(data.get("activity_ids", ()))
        try:
            activities = tuple(activities_by_id[value] for value in activity_ids)
        except KeyError as exc:
            raise ValueError(
                f"processo referencia atividade ausente: {exc.args[0]}"
            ) from exc
        return RscProcess(
            id=data["id"],
            applicant_name=data["applicant_name"],
            institution=data["institution"],
            applicant_identifier=data.get("applicant_identifier"),
            status=RscProcessStatus(data["status"]),
            created_at=_read_datetime(data["created_at"], "created_at"),
            updated_at=_read_datetime(data["updated_at"], "updated_at"),
            activities=activities,
            document_ids=tuple(data.get("document_ids", ())),
            metadata=_mapping(data.get("metadata", {}), "metadata"),
        )


class ProjectSerializer:
    schema = "rsc.project/1"

    @classmethod
    def dump(
        cls, processes: tuple[RscProcess, ...], catalog_ids: tuple[str, ...]
    ) -> dict[str, Any]:
        return {
            "schema": cls.schema,
            "application": "rsc",
            "process_ids": [value.id for value in processes],
            "catalog": {"criterion_ids": list(catalog_ids)},
        }


class SummarySerializer:
    """Representação estável dos resultados derivados para auditoria."""

    schema = "rsc.summary/1"

    @classmethod
    def dump(cls, validation: Any, score: Any) -> dict[str, Any]:
        return {
            "validation": {
                "is_valid": validation.is_valid,
                "issues": [
                    {
                        "code": issue.code,
                        "severity": issue.severity.value,
                        "entity_type": issue.entity_type,
                        "entity_id": issue.entity_id,
                        "field": issue.field,
                    }
                    for issue in validation.issues
                ],
            },
            "score": {
                "total": str(score.total_score),
                "by_requirement": [
                    {
                        "requirement_id": item.requirement_id,
                        "total": str(item.total_score),
                    }
                    for item in score.requirement_scores
                ],
            },
        }
