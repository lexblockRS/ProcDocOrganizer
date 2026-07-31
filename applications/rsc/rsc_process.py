"""Aggregate de orquestração de um processo RSC completo."""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import date
from decimal import Decimal
from enum import Enum

from applications.rsc.execution_compatibility import (
    ExecutionCompatibilityCollection,
)
from applications.rsc.execution_facts import ExecutionFactCollection
from applications.rsc.execution_validation import (
    ExecutionValidationCollection,
)
from applications.rsc.normative_catalog import (
    NormativeCriterionCatalog,
    OFFICIAL_NORMATIVE_CATALOG,
)
from applications.rsc.requirement_scoring import (
    RequirementScore,
    RequirementScoreCollection,
)
from applications.rsc.scoring_kernel import (
    CriterionScore,
    CriterionScoreCollection,
)
from applications.rsc.temporal_attention import (
    TemporalAttention,
    TemporalAttentionCollection,
)


class RSCProcessError(ValueError):
    """O processo viola uma invariante de orquestração."""


class RSCProcessStage(str, Enum):
    DRAFT = "DRAFT"
    EVIDENCE = "EVIDENCE"
    FACTS = "FACTS"
    VALIDATED = "VALIDATED"
    COMPATIBLE = "COMPATIBLE"
    SCORED = "SCORED"
    AGGREGATED = "AGGREGATED"
    CONSOLIDATED = "CONSOLIDATED"


class IntendedRSCLevel(str, Enum):
    RSC_I = "RSC-I"
    RSC_II = "RSC-II"
    RSC_III = "RSC-III"
    RSC_IV = "RSC-IV"
    RSC_V = "RSC-V"
    RSC_VI = "RSC-VI"


@dataclass(frozen=True, slots=True)
class RSCServer:
    server_id: str
    name: str
    functional_registration: str

    def __post_init__(self) -> None:
        _require_text(self.server_id, "server_id")
        _require_text(self.name, "name")
        _require_text(
            self.functional_registration,
            "functional_registration",
        )


@dataclass(frozen=True, slots=True)
class RSCInstitution:
    institution_id: str
    name: str

    def __post_init__(self) -> None:
        _require_text(self.institution_id, "institution_id")
        _require_text(self.name, "name")


@dataclass(frozen=True, slots=True)
class RSCProcessDocument:
    document_id: str
    name: str

    def __post_init__(self) -> None:
        _require_text(self.document_id, "document_id")
        _require_text(self.name, "name")


@dataclass(frozen=True, slots=True)
class RSCProcessEvidence:
    evidence_id: str
    document_id: str
    description: str
    criterion_codes: tuple[str, ...] = ()
    metadata: tuple[tuple[str, str], ...] = ()
    documents: tuple[RSCProcessDocument, ...] = ()

    def __post_init__(self) -> None:
        _require_text(self.evidence_id, "evidence_id")
        _require_text(self.document_id, "document_id")
        _require_text(self.description, "description")
        _require_text_tuple(self.criterion_codes, "criterion_codes")
        if not isinstance(self.documents, tuple) or any(
            not isinstance(item, RSCProcessDocument)
            for item in self.documents
        ):
            raise TypeError(
                "documents deve ser uma tupla de RSCProcessDocument."
            )
        _require_unique(
            (item.document_id for item in self.documents),
            "Document",
        )
        if self.documents and self.document_id not in {
            item.document_id for item in self.documents
        }:
            raise RSCProcessError(
                "document_id deve identificar um Document da Evidence."
            )
        if not isinstance(self.metadata, tuple) or any(
            not isinstance(item, tuple)
            or len(item) != 2
            or not all(
                isinstance(value, str) and value.strip()
                for value in item
            )
            for item in self.metadata
        ):
            raise TypeError(
                "metadata deve ser uma tupla de pares textuais."
            )
        keys = tuple(key for key, _ in self.metadata)
        if len(keys) != len(set(keys)):
            raise RSCProcessError(
                "A Evidence não pode repetir chaves de metadata."
            )


@dataclass(frozen=True, slots=True)
class RSCProcessPendingFact:
    execution_fact_id: str
    evidence_id: str
    description: str
    reason: str

    def __post_init__(self) -> None:
        _require_text(self.execution_fact_id, "execution_fact_id")
        _require_text(self.evidence_id, "evidence_id")
        _require_text(self.description, "description")
        _require_text(self.reason, "reason")


@dataclass(frozen=True, slots=True)
class RSCProcessResult:
    total_score: Decimal
    computable_criterion_ids: tuple[str, ...]
    non_computable_criterion_ids: tuple[str, ...]
    pending_items: tuple[str, ...]
    temporal_attentions: TemporalAttentionCollection
    used_evidence_ids: tuple[str, ...]
    explanation: str

    def __post_init__(self) -> None:
        if not isinstance(self.total_score, Decimal):
            raise TypeError("total_score deve ser Decimal.")
        for value, field_name in (
            (self.computable_criterion_ids, "computable_criterion_ids"),
            (
                self.non_computable_criterion_ids,
                "non_computable_criterion_ids",
            ),
            (self.pending_items, "pending_items"),
            (self.used_evidence_ids, "used_evidence_ids"),
        ):
            _require_text_tuple(value, field_name)
        if set(self.computable_criterion_ids) & set(
            self.non_computable_criterion_ids
        ):
            raise RSCProcessError(
                "Um critério não pode ser computável e não computável."
            )
        if not isinstance(
            self.temporal_attentions,
            TemporalAttentionCollection,
        ):
            raise TypeError(
                "temporal_attentions deve ser TemporalAttentionCollection."
            )
        _require_text(self.explanation, "explanation")


@dataclass(frozen=True, slots=True)
class RSCProcess:
    process_id: str
    server: RSCServer
    institution: RSCInstitution
    intended_level: IntendedRSCLevel
    process_date: date
    stage: RSCProcessStage = RSCProcessStage.DRAFT
    evidences: tuple[RSCProcessEvidence, ...] = ()
    execution_facts: ExecutionFactCollection = field(
        default_factory=ExecutionFactCollection
    )
    pending_execution_facts: tuple[RSCProcessPendingFact, ...] = ()
    validations: ExecutionValidationCollection = field(
        default_factory=ExecutionValidationCollection
    )
    compatibilities: ExecutionCompatibilityCollection = field(
        default_factory=ExecutionCompatibilityCollection
    )
    criterion_scores: CriterionScoreCollection = field(
        default_factory=CriterionScoreCollection
    )
    requirement_scores: RequirementScoreCollection = field(
        default_factory=RequirementScoreCollection
    )
    result: RSCProcessResult | None = None
    revision: int = 0
    catalog: NormativeCriterionCatalog = field(
        default=OFFICIAL_NORMATIVE_CATALOG,
        repr=False,
        compare=False,
    )

    def __post_init__(self) -> None:
        _require_text(self.process_id, "process_id")
        if not isinstance(self.server, RSCServer):
            raise TypeError("server deve ser RSCServer.")
        if not isinstance(self.institution, RSCInstitution):
            raise TypeError("institution deve ser RSCInstitution.")
        if not isinstance(self.intended_level, IntendedRSCLevel):
            raise TypeError(
                "intended_level deve ser IntendedRSCLevel."
            )
        if not isinstance(self.process_date, date):
            raise TypeError("process_date deve ser date.")
        if not isinstance(self.stage, RSCProcessStage):
            raise TypeError("stage deve ser RSCProcessStage.")
        if not isinstance(self.revision, int) or self.revision < 0:
            raise TypeError("revision deve ser inteiro não negativo.")
        if not isinstance(self.catalog, NormativeCriterionCatalog):
            raise TypeError(
                "catalog deve ser NormativeCriterionCatalog."
            )
        if not isinstance(self.evidences, tuple) or any(
            not isinstance(item, RSCProcessEvidence)
            for item in self.evidences
        ):
            raise TypeError(
                "evidences deve ser uma tupla de RSCProcessEvidence."
            )
        _require_unique(
            (item.evidence_id for item in self.evidences),
            "Evidence",
        )
        if not isinstance(self.pending_execution_facts, tuple) or any(
            not isinstance(item, RSCProcessPendingFact)
            for item in self.pending_execution_facts
        ):
            raise TypeError(
                "pending_execution_facts deve ser uma tupla de "
                "RSCProcessPendingFact."
            )
        _require_unique(
            (
                item.execution_fact_id
                for item in self.pending_execution_facts
            ),
            "ExecutionFact pendente",
        )
        evidence_ids = {item.evidence_id for item in self.evidences}
        if any(
            item.evidence_id not in evidence_ids
            for item in self.pending_execution_facts
        ):
            raise RSCProcessError(
                "ExecutionFact pendente deve referenciar Evidence do processo."
            )
        for collection, expected_type, field_name in (
            (
                self.execution_facts,
                ExecutionFactCollection,
                "execution_facts",
            ),
            (
                self.validations,
                ExecutionValidationCollection,
                "validations",
            ),
            (
                self.compatibilities,
                ExecutionCompatibilityCollection,
                "compatibilities",
            ),
            (
                self.criterion_scores,
                CriterionScoreCollection,
                "criterion_scores",
            ),
            (
                self.requirement_scores,
                RequirementScoreCollection,
                "requirement_scores",
            ),
        ):
            if not isinstance(collection, expected_type):
                raise TypeError(
                    f"{field_name} deve ser {expected_type.__name__}."
                )
        if self.result is not None and not isinstance(
            self.result,
            RSCProcessResult,
        ):
            raise TypeError("result deve ser RSCProcessResult ou None.")
        if (
            self.stage is RSCProcessStage.CONSOLIDATED
        ) != (self.result is not None):
            raise RSCProcessError(
                "Somente um processo consolidado pode possuir resultado."
            )
        self._validate_catalog_references()

    @classmethod
    def create(
        cls,
        *,
        process_id: str,
        server: RSCServer,
        institution: RSCInstitution,
        intended_level: IntendedRSCLevel,
        process_date: date,
        catalog: NormativeCriterionCatalog = (
            OFFICIAL_NORMATIVE_CATALOG
        ),
    ) -> "RSCProcess":
        return cls(
            process_id=process_id,
            server=server,
            institution=institution,
            intended_level=intended_level,
            process_date=process_date,
            catalog=catalog,
        )

    def add_evidence(
        self,
        evidence: RSCProcessEvidence,
    ) -> "RSCProcess":
        self._require_stage(
            RSCProcessStage.DRAFT,
            RSCProcessStage.EVIDENCE,
        )
        if not isinstance(evidence, RSCProcessEvidence):
            raise TypeError("evidence deve ser RSCProcessEvidence.")
        if any(
            item.evidence_id == evidence.evidence_id
            for item in self.evidences
        ):
            raise RSCProcessError("Evidence duplicada no processo.")
        self._require_catalog_codes(evidence.criterion_codes)
        return replace(
            self,
            evidences=(*self.evidences, evidence),
            stage=RSCProcessStage.EVIDENCE,
            revision=self.revision + 1,
        )

    def record_execution_facts(
        self,
        facts: ExecutionFactCollection,
        pending_facts: tuple[RSCProcessPendingFact, ...] = (),
    ) -> "RSCProcess":
        self._require_stage(
            RSCProcessStage.DRAFT,
            RSCProcessStage.EVIDENCE,
        )
        if not isinstance(facts, ExecutionFactCollection):
            raise TypeError("facts deve ser ExecutionFactCollection.")
        if not isinstance(pending_facts, tuple) or any(
            not isinstance(item, RSCProcessPendingFact)
            for item in pending_facts
        ):
            raise TypeError(
                "pending_facts deve ser uma tupla de RSCProcessPendingFact."
            )
        evidence_ids = {item.evidence_id for item in self.evidences}
        if any(item.evidence_id not in evidence_ids for item in pending_facts):
            raise RSCProcessError(
                "ExecutionFact pendente deve referenciar Evidence do processo."
            )
        self._require_catalog_codes(
            tuple(item.criterion_id for item in facts)
        )
        return replace(
            self,
            execution_facts=facts,
            pending_execution_facts=pending_facts,
            stage=RSCProcessStage.FACTS,
            revision=self.revision + 1,
        )

    def record_validations(
        self,
        validations: ExecutionValidationCollection,
    ) -> "RSCProcess":
        self._require_stage(RSCProcessStage.FACTS)
        if not isinstance(
            validations,
            ExecutionValidationCollection,
        ):
            raise TypeError(
                "validations deve ser ExecutionValidationCollection."
            )
        self._require_exact_fact_ids(
            tuple(
                item.execution_fact_id for item in validations
            ),
            "Validation",
        )
        return replace(
            self,
            validations=validations,
            stage=RSCProcessStage.VALIDATED,
            revision=self.revision + 1,
        )

    def record_compatibilities(
        self,
        compatibilities: ExecutionCompatibilityCollection,
    ) -> "RSCProcess":
        self._require_stage(RSCProcessStage.VALIDATED)
        if not isinstance(
            compatibilities,
            ExecutionCompatibilityCollection,
        ):
            raise TypeError(
                "compatibilities deve ser "
                "ExecutionCompatibilityCollection."
            )
        self._require_exact_fact_ids(
            tuple(
                item.execution_fact_id
                for item in compatibilities
            ),
            "Compatibility",
        )
        return replace(
            self,
            compatibilities=compatibilities,
            stage=RSCProcessStage.COMPATIBLE,
            revision=self.revision + 1,
        )

    def record_criterion_scores(
        self,
        scores: CriterionScoreCollection,
    ) -> "RSCProcess":
        self._require_stage(RSCProcessStage.COMPATIBLE)
        if not isinstance(scores, CriterionScoreCollection):
            raise TypeError(
                "scores deve ser CriterionScoreCollection."
            )
        self._require_catalog_codes(
            tuple(item.criterion_id for item in scores)
        )
        self._require_exact_fact_ids(
            tuple(
                item.source_contract.execution_fact_id
                for item in scores
            ),
            "CriterionScore",
        )
        return replace(
            self,
            criterion_scores=scores,
            stage=RSCProcessStage.SCORED,
            revision=self.revision + 1,
        )

    def record_requirement_scores(
        self,
        scores: RequirementScoreCollection,
    ) -> "RSCProcess":
        self._require_stage(RSCProcessStage.SCORED)
        if not isinstance(scores, RequirementScoreCollection):
            raise TypeError(
                "scores deve ser RequirementScoreCollection."
            )
        expected = {
            item.score_id for item in self.criterion_scores
        }
        observed = tuple(
            criterion.score_id
            for requirement in scores
            for criterion in requirement.criterion_scores
        )
        if expected != set(observed) or len(observed) != len(expected):
            raise RSCProcessError(
                "RequirementScores devem preservar todos os "
                "CriterionScores do processo."
            )
        return replace(
            self,
            requirement_scores=scores,
            stage=RSCProcessStage.AGGREGATED,
            revision=self.revision + 1,
        )

    def consolidate(
        self,
        result: RSCProcessResult,
    ) -> "RSCProcess":
        self._require_stage(RSCProcessStage.AGGREGATED)
        if not isinstance(result, RSCProcessResult):
            raise TypeError("result deve ser RSCProcessResult.")
        criterion_ids = {
            item.criterion_id for item in self.criterion_scores
        }
        result_ids = set(result.computable_criterion_ids) | set(
            result.non_computable_criterion_ids
        )
        if result_ids != criterion_ids:
            raise RSCProcessError(
                "O resultado referencia critérios ausentes."
            )
        evidence_ids = {
            item.evidence_id for item in self.evidences
        }
        if not set(result.used_evidence_ids) <= evidence_ids:
            raise RSCProcessError(
                "O resultado referencia Evidence ausente."
            )
        score_ids = {
            item.score_id for item in self.criterion_scores
        }
        if any(
            item.score_id not in score_ids
            for item in result.temporal_attentions
        ):
            raise RSCProcessError(
                "Attention referencia CriterionScore ausente."
            )
        self._require_catalog_codes(tuple(result_ids))
        return replace(
            self,
            result=result,
            stage=RSCProcessStage.CONSOLIDATED,
            revision=self.revision + 1,
        )

    def criterion_score(
        self,
        criterion_code: str,
    ) -> CriterionScore | None:
        return next((
            item
            for item in self.criterion_scores
            if item.criterion_id == criterion_code
        ), None)

    def requirement_score(
        self,
        requirement_id: str,
    ) -> RequirementScore | None:
        return next((
            item
            for item in self.requirement_scores
            if item.requirement_id == requirement_id
        ), None)

    @property
    def aggregate_id(self) -> str:
        """Identidade estável do Aggregate, independente da revisão."""
        return self.process_id

    def same_process(self, other: object) -> bool:
        """Indica se dois snapshots pertencem ao mesmo processo."""
        return (
            isinstance(other, RSCProcess)
            and self.aggregate_id == other.aggregate_id
        )

    def evidences_for_criterion(
        self,
        criterion_code: str,
    ) -> tuple[RSCProcessEvidence, ...]:
        self._require_catalog_codes((criterion_code,))
        return tuple(
            item
            for item in self.evidences
            if criterion_code in item.criterion_codes
        )

    @property
    def total_score(self) -> Decimal | None:
        return (
            self.result.total_score
            if self.result is not None
            else None
        )

    @property
    def pending_items(self) -> tuple[str, ...]:
        return (
            self.result.pending_items
            if self.result is not None
            else ()
        )

    @property
    def temporal_attentions(
        self,
    ) -> tuple[TemporalAttention, ...]:
        return (
            self.result.temporal_attentions.attentions
            if self.result is not None
            else ()
        )

    def _validate_catalog_references(self) -> None:
        codes = tuple(
            code
            for evidence in self.evidences
            for code in evidence.criterion_codes
        )
        codes += tuple(
            item.criterion_id for item in self.execution_facts
        )
        codes += tuple(
            item.criterion_id for item in self.criterion_scores
        )
        if self.result is not None:
            codes += self.result.computable_criterion_ids
            codes += self.result.non_computable_criterion_ids
        self._require_catalog_codes(codes)

    def _require_catalog_codes(
        self,
        codes: tuple[str, ...],
    ) -> None:
        missing = tuple(
            code for code in codes if self.catalog.find(code) is None
        )
        if missing:
            raise RSCProcessError(
                "Critério ausente do catálogo: "
                + ", ".join(dict.fromkeys(missing))
                + "."
            )

    def _require_exact_fact_ids(
        self,
        observed: tuple[str, ...],
        source_name: str,
    ) -> None:
        expected = {
            item.execution_fact_id for item in self.execution_facts
        }
        if expected != set(observed) or len(observed) != len(expected):
            raise RSCProcessError(
                f"{source_name} deve corresponder exatamente aos "
                "ExecutionFacts."
            )

    def _require_stage(
        self,
        *allowed: RSCProcessStage,
    ) -> None:
        if self.stage not in allowed:
            expected = ", ".join(item.value for item in allowed)
            raise RSCProcessError(
                f"Operação inválida no estágio {self.stage.value}; "
                f"esperado: {expected}."
            )


def _require_text(value: object, field_name: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise TypeError(f"{field_name} deve ser texto não vazio.")


def _require_text_tuple(value: object, field_name: str) -> None:
    if not isinstance(value, tuple) or any(
        not isinstance(item, str) or not item.strip() for item in value
    ):
        raise TypeError(f"{field_name} deve ser uma tupla textual.")
    _require_unique(value, field_name)


def _require_unique(values: object, field_name: str) -> None:
    values = tuple(values)
    if len(values) != len(set(values)):
        raise RSCProcessError(
            f"{field_name} não pode conter duplicidades."
        )


__all__ = [
    "IntendedRSCLevel",
    "RSCInstitution",
    "RSCProcess",
    "RSCProcessDocument",
    "RSCProcessError",
    "RSCProcessEvidence",
    "RSCProcessPendingFact",
    "RSCProcessResult",
    "RSCProcessStage",
    "RSCServer",
]
