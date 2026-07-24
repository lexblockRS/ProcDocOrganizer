"""Estado temporário e imutável do formulário de evidência."""

from dataclasses import dataclass

from .evidence import Evidence
from .evidence_requests import CreateEvidenceRequest, UpdateEvidenceRequest
from .evidence_source_candidate import EvidenceSourceCandidate


@dataclass(frozen=True, init=False)
class EvidenceDraft:
    evidence_id: str | None = None
    document_identity: str = ""
    page_number: int | None = None
    title: str = ""
    source_snippet: str = ""
    user_notes: str = ""
    category: str = ""
    start_date: str = ""
    end_date: str = ""

    def __init__(
        self,
        evidence_id: str | None = None,
        document_identity: str | None = None,
        page_number: int | None = None,
        title: str = "",
        source_snippet: str = "",
        user_notes: str = "",
        category: str = "",
        start_date: str = "",
        end_date: str = "",
    ) -> None:
        for field, value in (
            ("evidence_id", evidence_id),
            ("document_identity", document_identity or ""),
            ("page_number", page_number),
            ("title", title),
            ("source_snippet", source_snippet),
            ("user_notes", user_notes),
            ("category", category),
            ("start_date", start_date),
            ("end_date", end_date),
        ):
            object.__setattr__(self, field, value)

    @classmethod
    def empty(cls) -> "EvidenceDraft":
        return cls()

    @classmethod
    def from_evidence(cls, evidence: Evidence) -> "EvidenceDraft":
        return cls(
            evidence_id=evidence.id,
            document_identity=evidence.document_identity,
            page_number=evidence.page_number,
            title=evidence.title,
            source_snippet=evidence.source_snippet or "",
            user_notes=evidence.user_notes or "",
            category=evidence.category or "",
            start_date=evidence.start_date or "",
            end_date=evidence.end_date or "",
        )

    @classmethod
    def from_source_candidate(
        cls, candidate: EvidenceSourceCandidate
    ) -> "EvidenceDraft":
        if not isinstance(candidate, EvidenceSourceCandidate):
            raise TypeError("candidate deve ser EvidenceSourceCandidate.")
        return cls(
            evidence_id=None,
            document_identity=candidate.document_identity,
            page_number=candidate.page_number,
            title=candidate.suggested_title or "Evidência da pesquisa",
            source_snippet=candidate.source_snippet,
        )

    def to_create_request(self) -> CreateEvidenceRequest:
        if self.evidence_id is not None:
            raise ValueError("Um draft de criação não pode possuir evidence_id.")
        return CreateEvidenceRequest(**self._request_values())

    def to_update_request(self) -> UpdateEvidenceRequest:
        if self.evidence_id is None:
            raise ValueError("Um draft de atualização exige evidence_id.")
        return UpdateEvidenceRequest(
            evidence_id=self.evidence_id, **self._request_values()
        )

    def is_minimally_valid(self) -> bool:
        return bool(self.document_identity.strip()) and bool(self.title.strip())

    def _request_values(self) -> dict:
        return {
            "document_identity": self.document_identity,
            "page_number": self.page_number,
            "title": self.title,
            "source_snippet": self.source_snippet or None,
            "user_notes": self.user_notes or None,
            "category": self.category or None,
            "start_date": self.start_date or None,
            "end_date": self.end_date or None,
        }
