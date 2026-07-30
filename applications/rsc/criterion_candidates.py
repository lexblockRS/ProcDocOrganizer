"""Seleção estrutural de critérios que merecem análise posterior."""

from __future__ import annotations

from collections.abc import Iterator, Mapping, Sequence
from dataclasses import dataclass
from enum import Enum
from typing import Protocol

from applications.rsc.evaluation_context import (
    EvaluationActivity,
    EvaluationContext,
    EvaluationDocument,
    EvaluationEvidence,
    EvaluationFunctionalAssignmentEvidence,
    EvaluationFunctionalExercise,
)


class CriterionCandidateError(ValueError):
    """Falha de integridade durante a produção de candidatos."""


class InvalidCandidateLinkError(CriterionCandidateError):
    """Um vínculo explícito é incompleto ou contradiz o snapshot."""


class UnknownNormativeObjectError(CriterionCandidateError):
    """Um vínculo aponta para critério ou requisito normativo ausente."""


class StructuralConfidence(str, Enum):
    """Qualificador factual e não estatístico da associação."""

    EXPLICIT_CHAIN = "explicit_chain"
    ACCEPTED_DOCUMENT_CHAIN = "accepted_document_chain"


class NormativeCriterionRecord(Protocol):
    id: str
    requirement_id: str
    document_id: str
    legal_reference: str
    hierarchy: Sequence[str]


class NormativeRequirementRecord(Protocol):
    id: str


class AcceptedDocumentRecord(Protocol):
    id: str
    legal_reference: str


class ReadOnlyNormativeModel(Protocol):
    """Parcela somente leitura da API normativa exigida pelo Engine."""

    def find_criterion(
        self,
        criterion_id: str,
    ) -> NormativeCriterionRecord | None: ...

    def find_requirement(
        self,
        requirement_id: str,
    ) -> NormativeRequirementRecord | None: ...

    def find_accepted_document(
        self,
        document_type_id: str,
    ) -> AcceptedDocumentRecord | None: ...


@dataclass(frozen=True, slots=True)
class NormativeOrigin:
    document_id: str
    legal_reference: str
    hierarchy: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class FactualTraceability:
    activity_id: str
    functional_exercise_id: str
    functional_assignment_evidence_id: str
    evidence_id: str
    document_id: str
    document_identity: str
    accepted_document_id: str | None


@dataclass(frozen=True, slots=True)
class CriterionCandidate:
    """Hipótese de análise; não expressa atendimento do critério."""

    criterion_id: str
    requirement_id: str
    normative_origin: NormativeOrigin
    activity: EvaluationActivity
    functional_exercise: EvaluationFunctionalExercise
    confidence: StructuralConfidence
    technical_justification: str
    factual_traceability: FactualTraceability


@dataclass(frozen=True, slots=True)
class CriterionCandidateCollection:
    candidates: tuple[CriterionCandidate, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.candidates, tuple):
            raise TypeError("candidates deve ser uma tupla.")
        if any(
            not isinstance(candidate, CriterionCandidate)
            for candidate in self.candidates
        ):
            raise TypeError("candidates contém objeto inválido.")
        identities = tuple(
            (
                candidate.criterion_id,
                candidate.activity.activity_id,
                candidate.functional_exercise.id,
            )
            for candidate in self.candidates
        )
        if len(identities) != len(set(identities)):
            raise ValueError("candidates não pode conter duplicidades.")

    def __iter__(self) -> Iterator[CriterionCandidate]:
        return iter(self.candidates)

    def __len__(self) -> int:
        return len(self.candidates)

    def __bool__(self) -> bool:
        return bool(self.candidates)


class CriterionCandidateEngine:
    """Projeta candidatos exclusivamente a partir de vínculos explícitos."""

    METADATA_KEY = "criterion_candidate_links"
    REQUIRED_LINK_FIELDS = (
        "criterion_id",
        "activity_id",
        "functional_exercise_id",
        "functional_assignment_evidence_id",
        "evidence_id",
        "document_identity",
    )

    def __init__(self, normative_model: ReadOnlyNormativeModel) -> None:
        self._normative_model = normative_model

    def generate(
        self,
        context: EvaluationContext,
    ) -> CriterionCandidateCollection:
        if not isinstance(context, EvaluationContext):
            raise TypeError("context deve ser EvaluationContext.")

        links = self._links(context)
        if not links:
            return CriterionCandidateCollection()

        factual = _FactualIndex(context)
        candidates: list[CriterionCandidate] = []
        seen: set[tuple[str, str, str]] = set()
        for position, link in enumerate(links):
            values = self._link_values(link, position)
            criterion = self._criterion(values["criterion_id"])
            requirement = self._requirement(criterion.requirement_id)
            chain = factual.resolve(values)
            accepted_document = self._accepted_document(
                values.get("accepted_document_id")
            )
            if values.get("accepted_document_id") is not None and (
                accepted_document is None
            ):
                continue

            identity = (
                criterion.id,
                chain.activity.activity_id,
                chain.exercise.id,
            )
            if identity in seen:
                continue
            seen.add(identity)
            confidence = (
                StructuralConfidence.ACCEPTED_DOCUMENT_CHAIN
                if accepted_document is not None
                else StructuralConfidence.EXPLICIT_CHAIN
            )
            candidates.append(
                CriterionCandidate(
                    criterion_id=criterion.id,
                    requirement_id=requirement.id,
                    normative_origin=NormativeOrigin(
                        document_id=criterion.document_id,
                        legal_reference=criterion.legal_reference,
                        hierarchy=tuple(criterion.hierarchy),
                    ),
                    activity=chain.activity,
                    functional_exercise=chain.exercise,
                    confidence=confidence,
                    technical_justification=self._justification(
                        criterion.id,
                        requirement.id,
                        chain,
                        accepted_document,
                    ),
                    factual_traceability=FactualTraceability(
                        activity_id=chain.activity.activity_id,
                        functional_exercise_id=chain.exercise.id,
                        functional_assignment_evidence_id=(
                            chain.assignment.id
                        ),
                        evidence_id=chain.evidence.id,
                        document_id=chain.document.id,
                        document_identity=chain.document.document_identity,
                        accepted_document_id=(
                            accepted_document.id
                            if accepted_document is not None
                            else None
                        ),
                    ),
                )
            )
        return CriterionCandidateCollection(tuple(candidates))

    def _criterion(self, criterion_id: str) -> NormativeCriterionRecord:
        criterion = self._normative_model.find_criterion(criterion_id)
        if criterion is None or criterion.id != criterion_id:
            raise UnknownNormativeObjectError(
                f"Critério normativo desconhecido: {criterion_id}."
            )
        return criterion

    def _requirement(
        self,
        requirement_id: str,
    ) -> NormativeRequirementRecord:
        requirement = self._normative_model.find_requirement(
            requirement_id
        )
        if requirement is None or requirement.id != requirement_id:
            raise UnknownNormativeObjectError(
                f"Requisito normativo desconhecido: {requirement_id}."
            )
        return requirement

    def _accepted_document(
        self,
        document_type_id: str | None,
    ) -> AcceptedDocumentRecord | None:
        if document_type_id is None:
            return None
        return self._normative_model.find_accepted_document(
            document_type_id
        )

    @classmethod
    def _links(
        cls,
        context: EvaluationContext,
    ) -> tuple[Mapping[str, object], ...]:
        raw = context.metadata.get(cls.METADATA_KEY, ())
        if not isinstance(raw, tuple):
            raise InvalidCandidateLinkError(
                f"{cls.METADATA_KEY} deve ser uma tupla imutável."
            )
        if any(not isinstance(item, Mapping) for item in raw):
            raise InvalidCandidateLinkError(
                f"{cls.METADATA_KEY} contém vínculo inválido."
            )
        return raw

    @classmethod
    def _link_values(
        cls,
        link: Mapping[str, object],
        position: int,
    ) -> dict[str, str | None]:
        values: dict[str, str | None] = {}
        for field in cls.REQUIRED_LINK_FIELDS:
            value = link.get(field)
            if not isinstance(value, str) or not value.strip():
                raise InvalidCandidateLinkError(
                    f"Vínculo {position} exige {field} textual."
                )
            values[field] = value.strip()
        accepted = link.get("accepted_document_id")
        if accepted is not None and (
            not isinstance(accepted, str) or not accepted.strip()
        ):
            raise InvalidCandidateLinkError(
                f"Vínculo {position} possui accepted_document_id inválido."
            )
        values["accepted_document_id"] = (
            accepted.strip() if isinstance(accepted, str) else None
        )
        return values

    @staticmethod
    def _justification(
        criterion_id: str,
        requirement_id: str,
        chain: "_ResolvedChain",
        accepted_document: AcceptedDocumentRecord | None,
    ) -> str:
        parts = [
            f"Vínculo explícito ao critério {criterion_id}",
            f"requisito {requirement_id} confirmado pelo modelo normativo",
            (
                f"Activity {chain.activity.activity_id} referencia "
                f"FunctionalExercise {chain.exercise.id}"
            ),
            (
                "cadeia factual alcança Evidence "
                f"{chain.evidence.id} e Document {chain.document.id}"
            ),
        ]
        if accepted_document is not None:
            parts.append(
                "categoria documental aceita "
                f"{accepted_document.id} ({accepted_document.legal_reference})"
            )
        return "; ".join(parts) + "."


@dataclass(frozen=True, slots=True)
class _ResolvedChain:
    activity: EvaluationActivity
    exercise: EvaluationFunctionalExercise
    assignment: EvaluationFunctionalAssignmentEvidence
    evidence: EvaluationEvidence
    document: EvaluationDocument


class _FactualIndex:
    def __init__(self, context: EvaluationContext) -> None:
        self._activities = {
            item.activity_id: item for item in context.activities
        }
        self._exercises = {
            item.id: item for item in context.functional_exercises
        }
        self._assignments = {
            item.id: item
            for item in context.functional_assignment_evidences
        }
        self._evidences = {
            item.id: item for item in context.evidences
        }
        self._documents = {
            item.document_identity.lower(): item
            for item in context.documents
        }

    def resolve(
        self,
        values: Mapping[str, str | None],
    ) -> _ResolvedChain:
        activity = self._get(
            self._activities,
            values["activity_id"],
            "Activity",
        )
        exercise = self._get(
            self._exercises,
            values["functional_exercise_id"],
            "FunctionalExercise",
        )
        assignment = self._get(
            self._assignments,
            values["functional_assignment_evidence_id"],
            "FunctionalAssignmentEvidence",
        )
        evidence = self._get(
            self._evidences,
            values["evidence_id"],
            "Evidence",
        )
        document_identity = values["document_identity"]
        assert document_identity is not None
        document = self._get(
            self._documents,
            document_identity.lower(),
            "Document",
        )

        if exercise.id not in activity.functional_exercise_ids:
            self._invalid("Activity não referencia FunctionalExercise.")
        if (
            assignment.id
            not in exercise.functional_assignment_evidence_ids
        ):
            self._invalid(
                "FunctionalExercise não referencia "
                "FunctionalAssignmentEvidence."
            )
        if assignment.source_evidence_id != evidence.id:
            self._invalid(
                "FunctionalAssignmentEvidence não referencia Evidence."
            )
        if (
            evidence.document_identity.lower()
            != document.document_identity.lower()
        ):
            self._invalid("Evidence não referencia Document.")
        return _ResolvedChain(
            activity=activity,
            exercise=exercise,
            assignment=assignment,
            evidence=evidence,
            document=document,
        )

    @staticmethod
    def _get(
        index: Mapping[str, object],
        identity: str | None,
        label: str,
    ):
        value = index.get(identity or "")
        if value is None:
            raise InvalidCandidateLinkError(
                f"Vínculo explícito referencia {label} ausente: "
                f"{identity}."
            )
        return value

    @staticmethod
    def _invalid(message: str) -> None:
        raise InvalidCandidateLinkError(message)


__all__ = [
    "CriterionCandidate",
    "CriterionCandidateCollection",
    "CriterionCandidateEngine",
    "CriterionCandidateError",
    "FactualTraceability",
    "InvalidCandidateLinkError",
    "NormativeOrigin",
    "ReadOnlyNormativeModel",
    "StructuralConfidence",
    "UnknownNormativeObjectError",
]
