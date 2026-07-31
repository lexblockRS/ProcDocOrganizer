"""Análise observacional e imutável de cobertura operacional."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from fractions import Fraction

from .resources import ResourceIdentity, ResourceType


class CoverageContractError(ValueError):
    """Um valor não preserva os contratos de Coverage."""


class CoverageScope(str, Enum):
    DOCUMENT = "document"
    EVIDENCE = "evidence"
    FACTUAL = "factual"
    NORMATIVE = "normative"
    OVERALL = "overall"


class CoverageState(str, Enum):
    EMPTY = "empty"
    PARTIAL = "partial"
    COMPLETE = "complete"
    NOT_EVALUATED = "not_evaluated"
    INCONSISTENT = "inconsistent"
    UNKNOWN = "unknown"
    ABSENT = "absent"
    INSUFFICIENT = "insufficient"
    NOT_APPLICABLE = "not_applicable"


def _text(value: object, name: str, *, optional: bool = False) -> str | None:
    if optional and value is None:
        return None
    if not isinstance(value, str):
        suffix = " ou None" if optional else ""
        raise CoverageContractError(f"{name} deve ser string{suffix}.")
    normalized = value.strip()
    if not normalized:
        raise CoverageContractError(f"{name} não pode ser vazio.")
    return normalized


def _revision(value: object, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise CoverageContractError(
            f"{name} deve ser inteiro não negativo."
        )
    return value


def _identity(
    value: object, expected: ResourceType, name: str
) -> ResourceIdentity:
    if not isinstance(value, ResourceIdentity):
        raise CoverageContractError(f"{name} deve ser ResourceIdentity.")
    if value.resource_type is not expected:
        raise CoverageContractError(
            f"{name} deve possuir tipo {expected.value}."
        )
    return value


def _identity_tuple(
    values: object,
    expected: ResourceType,
    name: str,
) -> tuple[ResourceIdentity, ...]:
    if not isinstance(values, tuple):
        raise CoverageContractError(f"{name} deve ser tuple.")
    result = tuple(
        _identity(item, expected, f"{name}[]") for item in values
    )
    if len(set(result)) != len(result):
        raise CoverageContractError(f"{name} contém duplicatas.")
    return result


@dataclass(frozen=True, slots=True)
class DocumentCoverageReference:
    identity: ResourceIdentity
    evidences: tuple[ResourceIdentity, ...] = ()

    def __post_init__(self) -> None:
        _identity(self.identity, ResourceType.DOCUMENT, "identity")
        _identity_tuple(self.evidences, ResourceType.EVIDENCE, "evidences")


@dataclass(frozen=True, slots=True)
class EvidenceCoverageReference:
    identity: ResourceIdentity
    documents: tuple[ResourceIdentity, ...] = ()
    execution_facts: tuple[ResourceIdentity, ...] = ()

    def __post_init__(self) -> None:
        _identity(self.identity, ResourceType.EVIDENCE, "identity")
        _identity_tuple(self.documents, ResourceType.DOCUMENT, "documents")
        _identity_tuple(
            self.execution_facts,
            ResourceType.EXECUTION_FACT,
            "execution_facts",
        )


@dataclass(frozen=True, slots=True)
class ExecutionFactCoverageReference:
    identity: ResourceIdentity
    evidence: ResourceIdentity

    def __post_init__(self) -> None:
        _identity(self.identity, ResourceType.EXECUTION_FACT, "identity")
        _identity(self.evidence, ResourceType.EVIDENCE, "evidence")


@dataclass(frozen=True, slots=True)
class BindingCoverageReference:
    binding_id: str
    execution_fact: ResourceIdentity

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "binding_id", _text(self.binding_id, "binding_id")
        )
        _identity(
            self.execution_fact,
            ResourceType.EXECUTION_FACT,
            "execution_fact",
        )


@dataclass(frozen=True, slots=True)
class NormativeCoverageReference:
    identity: ResourceIdentity
    state: str

    def __post_init__(self) -> None:
        if self.identity.resource_type not in (
            ResourceType.REQUIREMENT,
            ResourceType.CRITERION,
        ):
            raise CoverageContractError(
                "identity normativa deve ser Requirement ou Criterion."
            )
        object.__setattr__(self, "state", _text(self.state, "state"))


@dataclass(frozen=True, slots=True)
class EvaluationCoverageSnapshot:
    evaluation_id: str
    revision: int
    used_evidences: tuple[ResourceIdentity, ...] = ()
    used_execution_facts: tuple[ResourceIdentity, ...] = ()
    validated_execution_facts: tuple[ResourceIdentity, ...] = ()
    compatible_execution_facts: tuple[ResourceIdentity, ...] = ()
    normative_results: tuple[NormativeCoverageReference, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "evaluation_id",
            _text(self.evaluation_id, "evaluation_id"),
        )
        object.__setattr__(self, "revision", _revision(self.revision, "revision"))
        _identity_tuple(
            self.used_evidences, ResourceType.EVIDENCE, "used_evidences"
        )
        for name in (
            "used_execution_facts",
            "validated_execution_facts",
            "compatible_execution_facts",
        ):
            _identity_tuple(
                getattr(self, name), ResourceType.EXECUTION_FACT, name
            )
        if not isinstance(self.normative_results, tuple) or any(
            not isinstance(item, NormativeCoverageReference)
            for item in self.normative_results
        ):
            raise CoverageContractError(
                "normative_results deve ser tuple de NormativeCoverageReference."
            )
        identities = {item.identity for item in self.normative_results}
        if len(identities) != len(self.normative_results):
            raise CoverageContractError(
                "normative_results contém identidades duplicadas."
            )


@dataclass(frozen=True, slots=True)
class CoverageInput:
    project_id: str
    project_revision: int
    documents: tuple[DocumentCoverageReference, ...] = ()
    evidences: tuple[EvidenceCoverageReference, ...] = ()
    execution_facts: tuple[ExecutionFactCoverageReference, ...] = ()
    bindings: tuple[BindingCoverageReference, ...] = ()
    evaluation: EvaluationCoverageSnapshot | None = None

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "project_id", _text(self.project_id, "project_id")
        )
        object.__setattr__(
            self,
            "project_revision",
            _revision(self.project_revision, "project_revision"),
        )
        for name, expected in (
            ("documents", DocumentCoverageReference),
            ("evidences", EvidenceCoverageReference),
            ("execution_facts", ExecutionFactCoverageReference),
            ("bindings", BindingCoverageReference),
        ):
            values = getattr(self, name)
            if not isinstance(values, tuple) or any(
                not isinstance(item, expected) for item in values
            ):
                raise CoverageContractError(
                    f"{name} deve ser tuple de {expected.__name__}."
                )
        for values, name in (
            (self.documents, "documents"),
            (self.evidences, "evidences"),
            (self.execution_facts, "execution_facts"),
        ):
            identities = {item.identity for item in values}
            if len(identities) != len(values):
                raise CoverageContractError(
                    f"{name} contém identidades duplicadas."
                )
        binding_facts = {item.execution_fact for item in self.bindings}
        if len(binding_facts) != len(self.bindings):
            raise CoverageContractError(
                "bindings contém mais de um Binding por ExecutionFact."
            )
        if self.evaluation is not None and not isinstance(
            self.evaluation, EvaluationCoverageSnapshot
        ):
            raise CoverageContractError(
                "evaluation deve ser EvaluationCoverageSnapshot ou None."
            )


@dataclass(frozen=True, slots=True)
class CoverageFinding:
    scope: CoverageScope
    subject: ResourceIdentity
    state: CoverageState
    observed: int
    expected: int | None
    explanation: str
    reason_codes: tuple[str, ...]
    related_resources: tuple[ResourceIdentity, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.scope, CoverageScope):
            raise CoverageContractError("scope deve ser CoverageScope.")
        if not isinstance(self.subject, ResourceIdentity):
            raise CoverageContractError(
                "subject deve ser ResourceIdentity."
            )
        if not isinstance(self.state, CoverageState):
            raise CoverageContractError("state deve ser CoverageState.")
        for value, name in ((self.observed, "observed"),):
            _revision(value, name)
        if self.expected is not None:
            _revision(self.expected, "expected")
        object.__setattr__(
            self, "explanation", _text(self.explanation, "explanation")
        )
        if not isinstance(self.reason_codes, tuple) or not self.reason_codes:
            raise CoverageContractError(
                "reason_codes deve ser tuple não vazia."
            )
        normalized = tuple(
            _text(item, "reason_codes[]") for item in self.reason_codes
        )
        if len(set(normalized)) != len(normalized):
            raise CoverageContractError("reason_codes contém duplicatas.")
        object.__setattr__(self, "reason_codes", normalized)
        if not isinstance(self.related_resources, tuple) or any(
            not isinstance(item, ResourceIdentity)
            for item in self.related_resources
        ):
            raise CoverageContractError(
                "related_resources deve ser tuple de ResourceIdentity."
            )


@dataclass(frozen=True, slots=True)
class DocumentCoverage:
    state: CoverageState
    total: int
    used: int
    unused: int
    multiple_evidences: int
    without_relationship: int

    def __post_init__(self) -> None:
        _summary(self, (
            "total", "used", "unused", "multiple_evidences",
            "without_relationship",
        ))


@dataclass(frozen=True, slots=True)
class EvidenceCoverage:
    state: CoverageState
    total: int
    with_documents: int
    without_documents: int
    with_execution_facts: int
    without_execution_facts: int
    evaluated: int
    inconsistencies: int

    def __post_init__(self) -> None:
        _summary(self, (
            "total", "with_documents", "without_documents",
            "with_execution_facts", "without_execution_facts",
            "evaluated", "inconsistencies",
        ))


@dataclass(frozen=True, slots=True)
class FactualCoverage:
    state: CoverageState
    total: int
    bound: int
    unbound: int
    evaluated: int
    pending: int
    validated: int
    compatible: int

    def __post_init__(self) -> None:
        _summary(self, (
            "total", "bound", "unbound", "evaluated", "pending",
            "validated", "compatible",
        ))


@dataclass(frozen=True, slots=True)
class StateCount:
    state: str
    count: int

    def __post_init__(self) -> None:
        object.__setattr__(self, "state", _text(self.state, "state"))
        _revision(self.count, "count")


@dataclass(frozen=True, slots=True)
class NormativeCoverage:
    state: CoverageState
    requirements_total: int
    criteria_total: int
    requirement_states: tuple[StateCount, ...] = ()
    criterion_states: tuple[StateCount, ...] = ()

    def __post_init__(self) -> None:
        _summary(self, ("requirements_total", "criteria_total"))
        for values, name in (
            (self.requirement_states, "requirement_states"),
            (self.criterion_states, "criterion_states"),
        ):
            if not isinstance(values, tuple) or any(
                not isinstance(item, StateCount) for item in values
            ):
                raise CoverageContractError(
                    f"{name} deve ser tuple de StateCount."
                )


@dataclass(frozen=True, slots=True)
class OverallCoverage:
    state: CoverageState
    covered: int
    total: int
    ratio: Fraction

    def __post_init__(self) -> None:
        _summary(self, ("covered", "total"))
        if not isinstance(self.ratio, Fraction):
            raise CoverageContractError("ratio deve ser Fraction.")
        expected = (
            Fraction(self.covered, self.total)
            if self.total
            else Fraction(0, 1)
        )
        if self.ratio != expected:
            raise CoverageContractError(
                "ratio deve corresponder a covered/total."
            )


@dataclass(frozen=True, slots=True)
class CoverageSourceRevisions:
    project_revision: int
    evaluation_revision: int | None = None

    def __post_init__(self) -> None:
        _revision(self.project_revision, "project_revision")
        if self.evaluation_revision is not None:
            _revision(self.evaluation_revision, "evaluation_revision")


@dataclass(frozen=True, slots=True)
class CoverageResult:
    document_coverage: DocumentCoverage
    evidence_coverage: EvidenceCoverage
    factual_coverage: FactualCoverage
    normative_coverage: NormativeCoverage
    overall_coverage: OverallCoverage
    findings: tuple[CoverageFinding, ...]
    source_revisions: CoverageSourceRevisions
    analysis_version: str
    generated_at: datetime | None = None

    def __post_init__(self) -> None:
        for value, expected, name in (
            (self.document_coverage, DocumentCoverage, "document_coverage"),
            (self.evidence_coverage, EvidenceCoverage, "evidence_coverage"),
            (self.factual_coverage, FactualCoverage, "factual_coverage"),
            (self.normative_coverage, NormativeCoverage, "normative_coverage"),
            (self.overall_coverage, OverallCoverage, "overall_coverage"),
            (self.source_revisions, CoverageSourceRevisions, "source_revisions"),
        ):
            if not isinstance(value, expected):
                raise CoverageContractError(
                    f"{name} deve ser {expected.__name__}."
                )
        if not isinstance(self.findings, tuple) or any(
            not isinstance(item, CoverageFinding) for item in self.findings
        ):
            raise CoverageContractError(
                "findings deve ser tuple de CoverageFinding."
            )
        object.__setattr__(
            self, "analysis_version", _text(
                self.analysis_version, "analysis_version"
            )
        )
        if self.generated_at is not None and not isinstance(
            self.generated_at, datetime
        ):
            raise CoverageContractError(
                "generated_at deve ser datetime ou None."
            )


def _summary(value, count_fields: tuple[str, ...]) -> None:
    if not isinstance(value.state, CoverageState):
        raise CoverageContractError("state deve ser CoverageState.")
    for name in count_fields:
        _revision(getattr(value, name), name)


__all__ = [
    "BindingCoverageReference", "CoverageContractError", "CoverageFinding",
    "CoverageInput", "CoverageResult", "CoverageScope", "CoverageSourceRevisions",
    "CoverageState", "DocumentCoverage", "DocumentCoverageReference",
    "EvaluationCoverageSnapshot", "EvidenceCoverage", "EvidenceCoverageReference",
    "ExecutionFactCoverageReference", "FactualCoverage", "NormativeCoverage",
    "NormativeCoverageReference", "OverallCoverage", "StateCount",
]
