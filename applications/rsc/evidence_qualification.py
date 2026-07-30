"""Qualificação documental determinística de candidatos a critério."""

from __future__ import annotations

from collections.abc import Iterator, Mapping
from dataclasses import dataclass

from applications.rsc.criterion_candidates import (
    AcceptedDocumentRecord,
    CriterionCandidate,
    CriterionCandidateCollection,
    NormativeOrigin,
    ReadOnlyNormativeModel,
)
from applications.rsc.evaluation_context import (
    EvaluationContext,
    EvaluationDocument,
)


class EvidenceQualificationError(ValueError):
    """Falha estrutural durante a qualificação documental."""


@dataclass(frozen=True, slots=True)
class PresentedDocument:
    document_id: str
    document_identity: str
    name: str


@dataclass(frozen=True, slots=True)
class MissingDocument:
    document_id: str
    document_identity: str


@dataclass(frozen=True, slots=True)
class OfficialDocumentCategory:
    category_id: str
    legal_reference: str


@dataclass(frozen=True, slots=True)
class AcceptedDocument:
    document: PresentedDocument
    category: OfficialDocumentCategory


@dataclass(frozen=True, slots=True)
class QualifiedCriterionCandidate:
    """Candidato acrescido de qualificação documental, não normativa."""

    source_candidate: CriterionCandidate
    presented_documents: tuple[PresentedDocument, ...]
    accepted_documents: tuple[AcceptedDocument, ...]
    missing_documents: tuple[MissingDocument, ...]
    satisfied_categories: tuple[OfficialDocumentCategory, ...]
    pending_categories: tuple[OfficialDocumentCategory, ...]
    documentary_justification: str
    normative_traceability: NormativeOrigin

    @property
    def has_compatible_documentation(self) -> bool:
        """Informa compatibilidade documental, não satisfação de critério."""

        return bool(self.accepted_documents)


@dataclass(frozen=True, slots=True)
class QualifiedCriterionCandidateCollection:
    candidates: tuple[QualifiedCriterionCandidate, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.candidates, tuple):
            raise TypeError("candidates deve ser uma tupla.")
        if any(
            not isinstance(candidate, QualifiedCriterionCandidate)
            for candidate in self.candidates
        ):
            raise TypeError("candidates contém objeto inválido.")
        identities = tuple(
            (
                item.source_candidate.criterion_id,
                item.source_candidate.activity.activity_id,
                item.source_candidate.functional_exercise.id,
            )
            for item in self.candidates
        )
        if len(identities) != len(set(identities)):
            raise ValueError(
                "candidates qualificados não pode conter duplicidades."
            )

    def __iter__(self) -> Iterator[QualifiedCriterionCandidate]:
        return iter(self.candidates)

    def __len__(self) -> int:
        return len(self.candidates)

    def __bool__(self) -> bool:
        return bool(self.candidates)


class EvidenceQualificationEngine:
    """Qualifica documentos por vínculos e categorias oficiais explícitos."""

    METADATA_KEY = "criterion_candidate_links"

    def __init__(
        self,
        context: EvaluationContext,
        normative_model: ReadOnlyNormativeModel,
    ) -> None:
        if not isinstance(context, EvaluationContext):
            raise TypeError("context deve ser EvaluationContext.")
        self._context = context
        self._normative_model = normative_model
        self._documents_by_id = {
            document.id: document for document in context.documents
        }
        self._documents_by_identity = {
            document.document_identity.lower(): document
            for document in context.documents
        }

    def qualify(
        self,
        candidates: CriterionCandidateCollection,
    ) -> QualifiedCriterionCandidateCollection:
        if not isinstance(candidates, CriterionCandidateCollection):
            raise TypeError(
                "candidates deve ser CriterionCandidateCollection."
            )
        return QualifiedCriterionCandidateCollection(tuple(
            self._qualify_candidate(candidate)
            for candidate in candidates
        ))

    def _qualify_candidate(
        self,
        candidate: CriterionCandidate,
    ) -> QualifiedCriterionCandidate:
        links = self._document_links(candidate)
        presented: list[PresentedDocument] = []
        accepted: list[AcceptedDocument] = []
        missing: list[MissingDocument] = []
        satisfied: list[OfficialDocumentCategory] = []
        pending: list[OfficialDocumentCategory] = []
        seen_presented: set[str] = set()
        seen_accepted: set[tuple[str, str]] = set()
        seen_missing: set[tuple[str, str]] = set()
        seen_satisfied: set[str] = set()
        seen_pending: set[str] = set()

        for link in links:
            document_id = self._text(link, "document_id")
            document_identity = self._text(link, "document_identity")
            category_id = self._optional_text(
                link,
                "accepted_document_id",
            )
            category_record = (
                self._normative_model.find_accepted_document(category_id)
                if category_id is not None
                else None
            )
            category = (
                self._category(category_record)
                if category_record is not None
                else None
            )
            document = self._find_document(
                document_id,
                document_identity,
            )
            if document is None:
                key = (document_id, document_identity.lower())
                if key not in seen_missing:
                    seen_missing.add(key)
                    missing.append(MissingDocument(
                        document_id=document_id,
                        document_identity=document_identity,
                    ))
                if (
                    category is not None
                    and category.category_id not in seen_pending
                ):
                    seen_pending.add(category.category_id)
                    pending.append(category)
                continue

            presented_document = PresentedDocument(
                document_id=document.id,
                document_identity=document.document_identity,
                name=document.name,
            )
            if document.id not in seen_presented:
                seen_presented.add(document.id)
                presented.append(presented_document)
            if category is None:
                continue
            accepted_key = (document.id, category.category_id)
            if accepted_key not in seen_accepted:
                seen_accepted.add(accepted_key)
                accepted.append(AcceptedDocument(
                    document=presented_document,
                    category=category,
                ))
            if category.category_id not in seen_satisfied:
                seen_satisfied.add(category.category_id)
                satisfied.append(category)

        pending = [
            category
            for category in pending
            if category.category_id not in seen_satisfied
        ]
        return QualifiedCriterionCandidate(
            source_candidate=candidate,
            presented_documents=tuple(presented),
            accepted_documents=tuple(accepted),
            missing_documents=tuple(missing),
            satisfied_categories=tuple(satisfied),
            pending_categories=tuple(pending),
            documentary_justification=self._justification(
                candidate,
                presented,
                accepted,
                missing,
                satisfied,
                pending,
            ),
            normative_traceability=candidate.normative_origin,
        )

    def _document_links(
        self,
        candidate: CriterionCandidate,
    ) -> tuple[Mapping[str, object], ...]:
        raw = self._context.metadata.get(self.METADATA_KEY, ())
        if not isinstance(raw, tuple) or any(
            not isinstance(item, Mapping) for item in raw
        ):
            raise EvidenceQualificationError(
                f"{self.METADATA_KEY} deve ser uma coleção imutável."
            )
        matching = tuple(
            self._normalized_link(candidate, item)
            for item in raw
            if self._matches(candidate, item)
        )
        if matching:
            return matching
        trace = candidate.factual_traceability
        return ({
            "document_id": trace.document_id,
            "document_identity": trace.document_identity,
            "accepted_document_id": trace.accepted_document_id,
        },)

    @staticmethod
    def _matches(
        candidate: CriterionCandidate,
        link: Mapping[str, object],
    ) -> bool:
        return (
            link.get("criterion_id") == candidate.criterion_id
            and link.get("activity_id") == candidate.activity.activity_id
            and link.get("functional_exercise_id")
            == candidate.functional_exercise.id
        )

    def _normalized_link(
        self,
        candidate: CriterionCandidate,
        link: Mapping[str, object],
    ) -> Mapping[str, object]:
        document_identity = self._text(link, "document_identity")
        document = self._documents_by_identity.get(
            document_identity.lower()
        )
        document_id = link.get("document_id")
        if document_id is None and document is not None:
            document_id = document.id
        if (
            document_id is None
            and document_identity.lower()
            == candidate.factual_traceability.document_identity.lower()
        ):
            document_id = candidate.factual_traceability.document_id
        if not isinstance(document_id, str) or not document_id.strip():
            raise EvidenceQualificationError(
                "Vínculo documental exige document_id."
            )
        return {
            "document_id": document_id.strip(),
            "document_identity": document_identity,
            "accepted_document_id": link.get("accepted_document_id"),
        }

    def _find_document(
        self,
        document_id: str,
        document_identity: str,
    ) -> EvaluationDocument | None:
        by_id = self._documents_by_id.get(document_id)
        by_identity = self._documents_by_identity.get(
            document_identity.lower()
        )
        if by_id is not None and by_identity is not None:
            if by_id is not by_identity:
                raise EvidenceQualificationError(
                    "ID e identidade indicam Documents diferentes."
                )
            return by_id
        return None

    @staticmethod
    def _category(
        record: AcceptedDocumentRecord,
    ) -> OfficialDocumentCategory:
        return OfficialDocumentCategory(
            category_id=record.id,
            legal_reference=record.legal_reference,
        )

    @staticmethod
    def _text(
        values: Mapping[str, object],
        field: str,
    ) -> str:
        value = values.get(field)
        if not isinstance(value, str) or not value.strip():
            raise EvidenceQualificationError(
                f"Vínculo documental exige {field} textual."
            )
        return value.strip()

    @staticmethod
    def _optional_text(
        values: Mapping[str, object],
        field: str,
    ) -> str | None:
        value = values.get(field)
        if value is None:
            return None
        if not isinstance(value, str) or not value.strip():
            raise EvidenceQualificationError(
                f"Vínculo documental possui {field} inválido."
            )
        return value.strip()

    @staticmethod
    def _justification(
        candidate: CriterionCandidate,
        presented: list[PresentedDocument],
        accepted: list[AcceptedDocument],
        missing: list[MissingDocument],
        satisfied: list[OfficialDocumentCategory],
        pending: list[OfficialDocumentCategory],
    ) -> str:
        return (
            f"Candidato {candidate.criterion_id}: "
            f"{len(presented)} documento(s) apresentado(s), "
            f"{len(accepted)} associação(ões) com categoria oficial, "
            f"{len(missing)} documento(s) ausente(s), "
            f"{len(satisfied)} categoria(s) documental(is) satisfeita(s) e "
            f"{len(pending)} categoria(s) documental(is) pendente(s). "
            "A qualificação registra apenas compatibilidade documental."
        )


__all__ = [
    "AcceptedDocument",
    "EvidenceQualificationEngine",
    "EvidenceQualificationError",
    "MissingDocument",
    "OfficialDocumentCategory",
    "PresentedDocument",
    "QualifiedCriterionCandidate",
    "QualifiedCriterionCandidateCollection",
]
