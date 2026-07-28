"""Operações de evidência documental da avaliação RSC."""

from applications.rsc.domain import RscActivity, RscEvidence


class RscEvidenceService:
    def __init__(self) -> None:
        self._evidence: dict[str, RscEvidence] = {}

    def create_evidence(self, **values) -> RscEvidence:
        evidence = RscEvidence(**values)
        if evidence.id in self._evidence:
            raise ValueError(f"evidência duplicada: {evidence.id}")
        self._evidence[evidence.id] = evidence
        return evidence

    def add_evidence(
        self, activity: RscActivity, evidence: RscEvidence
    ) -> RscActivity:
        if evidence.activity_id != activity.id:
            raise ValueError("evidência não corresponde à atividade.")
        existing = self._evidence.get(evidence.id)
        if existing is not None and existing != evidence:
            raise ValueError(f"evidência duplicada: {evidence.id}")
        self._evidence[evidence.id] = evidence
        return activity.link_evidence(evidence.id)

    def remove_evidence(
        self, activity: RscActivity, evidence_id: str
    ) -> RscActivity:
        updated = activity.unlink_evidence(evidence_id)
        self._evidence.pop(evidence_id, None)
        return updated

    def list_evidence(
        self, activity: RscActivity
    ) -> tuple[RscEvidence, ...]:
        return tuple(
            self._evidence[evidence_id]
            for evidence_id in activity.evidence_ids
            if evidence_id in self._evidence
        )

    def get_evidence(self, evidence_id: str) -> RscEvidence:
        try:
            return self._evidence[evidence_id]
        except KeyError as exc:
            raise KeyError(
                f"evidência inexistente: {evidence_id}"
            ) from exc

    def list_all(self) -> tuple[RscEvidence, ...]:
        return tuple(self._evidence.values())

    def list_by_activity(
        self, activity: RscActivity
    ) -> tuple[RscEvidence, ...]:
        return self.list_evidence(activity)

    def link_document(
        self, evidence: RscEvidence, document_id: str
    ) -> RscEvidence:
        updated = evidence.link_document(document_id)
        self._evidence[updated.id] = updated
        return updated

    def unlink_document(
        self, evidence: RscEvidence, document_id: str
    ) -> RscEvidence:
        updated = evidence.unlink_document(document_id)
        self._evidence[updated.id] = updated
        return updated

    def clear(self) -> None:
        self._evidence.clear()
