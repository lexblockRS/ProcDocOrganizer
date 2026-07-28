"""Raiz agregada do processo RSC."""

from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import datetime
from types import MappingProxyType

from .activity import RscActivity
from .enums import RscProcessStatus
from .identifiers import (
    normalize_uuid,
    optional_text,
    require_aware,
    required_text,
    utc_now,
)


def _metadata(values: Mapping[str, object]) -> Mapping[str, object]:
    allowed = (str, int, float, bool, type(None))
    result = dict(values)
    if any(
        not isinstance(key, str) or not isinstance(value, allowed)
        for key, value in result.items()
    ):
        raise ValueError("metadata aceita somente dados serializáveis simples.")
    return MappingProxyType(result)


@dataclass(slots=True)
class RscProcess:
    applicant_name: str
    institution: str
    id: str | None = None
    applicant_identifier: str | None = None
    status: RscProcessStatus = RscProcessStatus.DRAFT
    created_at: datetime | None = None
    updated_at: datetime | None = None
    activities: tuple[RscActivity, ...] = ()
    document_ids: tuple[str, ...] = ()
    metadata: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.id = normalize_uuid(self.id)
        if not isinstance(self.applicant_name, str):
            raise TypeError("applicant_name deve ser string.")
        if not isinstance(self.institution, str):
            raise TypeError("institution deve ser string.")
        self.applicant_name = " ".join(self.applicant_name.split())
        self.institution = " ".join(self.institution.split())
        self.applicant_identifier = optional_text(
            self.applicant_identifier, "applicant_identifier"
        )
        if not isinstance(self.status, RscProcessStatus):
            raise TypeError("status deve ser RscProcessStatus.")
        created = self.created_at or utc_now()
        self.created_at = require_aware(created, "created_at")
        self.updated_at = require_aware(
            self.updated_at or created, "updated_at"
        )
        self.activities = tuple(self.activities)
        if any(not isinstance(item, RscActivity) for item in self.activities):
            raise TypeError("activities deve conter RscActivity.")
        if len({item.id for item in self.activities}) != len(self.activities):
            raise ValueError("IDs de atividades não podem duplicar.")
        self.document_ids = tuple(
            required_text(value, "document_id") for value in self.document_ids
        )
        if len(set(self.document_ids)) != len(self.document_ids):
            raise ValueError("documentos não podem duplicar.")
        self.metadata = _metadata(self.metadata)

    def touch(self) -> None:
        self.updated_at = utc_now()

    def add_activity(self, activity: RscActivity) -> None:
        if not isinstance(activity, RscActivity):
            raise TypeError("activity deve ser RscActivity.")
        if any(item.id == activity.id for item in self.activities):
            raise ValueError(f"atividade duplicada: {activity.id}")
        self.activities = (*self.activities, activity)
        self.touch()

    def update_activity(self, activity: RscActivity) -> None:
        if not isinstance(activity, RscActivity):
            raise TypeError("activity deve ser RscActivity.")
        if not any(item.id == activity.id for item in self.activities):
            raise KeyError(f"atividade inexistente: {activity.id}")
        self.activities = tuple(
            activity if item.id == activity.id else item
            for item in self.activities
        )
        self.touch()

    def remove_activity(self, activity_id: str) -> RscActivity:
        activity = self.get_activity(activity_id)
        self.activities = tuple(
            item for item in self.activities if item.id != activity_id
        )
        self.touch()
        return activity

    def get_activity(self, activity_id: str) -> RscActivity:
        for activity in self.activities:
            if activity.id == activity_id:
                return activity
        raise KeyError(f"atividade inexistente: {activity_id}")

    def list_activities(self) -> tuple[RscActivity, ...]:
        return self.activities

    def attach_document(self, document_id: str) -> None:
        normalized = required_text(document_id, "document_id")
        if normalized in self.document_ids:
            raise ValueError("documento já anexado.")
        self.document_ids = (*self.document_ids, normalized)
        self.touch()

    def detach_document(self, document_id: str) -> None:
        normalized = required_text(document_id, "document_id")
        if normalized not in self.document_ids:
            raise KeyError(f"documento inexistente: {normalized}")
        self.document_ids = tuple(
            value for value in self.document_ids if value != normalized
        )
        self.touch()

    def mark_in_preparation(self) -> None:
        if self.status is not RscProcessStatus.DRAFT:
            raise ValueError("somente processo draft pode entrar em preparação.")
        self.status = RscProcessStatus.IN_PREPARATION
        self.touch()
