"""Analyzer determinístico de cobertura estrutural."""

from __future__ import annotations

from collections import Counter
from fractions import Fraction

from .coverage import (
    CoverageFinding,
    CoverageInput,
    CoverageResult,
    CoverageScope,
    CoverageSourceRevisions,
    CoverageState,
    DocumentCoverage,
    EvidenceCoverage,
    FactualCoverage,
    NormativeCoverage,
    OverallCoverage,
    StateCount,
)
from .resources import ResourceType


class CoverageAnalyzer:
    """Observa relações fornecidas sem executar regras externas."""

    analysis_version = "1.0"

    def analyze(self, coverage_input: CoverageInput) -> CoverageResult:
        if not isinstance(coverage_input, CoverageInput):
            raise TypeError("coverage_input deve ser CoverageInput.")
        evaluation = coverage_input.evaluation
        document_ids = {item.identity for item in coverage_input.documents}
        evidence_ids = {item.identity for item in coverage_input.evidences}
        fact_ids = {item.identity for item in coverage_input.execution_facts}
        binding_facts = {
            item.execution_fact for item in coverage_input.bindings
        }
        evaluated_evidence = (
            set() if evaluation is None else set(evaluation.used_evidences)
        )
        evaluated_facts = (
            set()
            if evaluation is None
            else set(evaluation.used_execution_facts)
        )
        validated_facts = (
            set()
            if evaluation is None
            else set(evaluation.validated_execution_facts)
        )
        compatible_facts = (
            set()
            if evaluation is None
            else set(evaluation.compatible_execution_facts)
        )

        findings: list[CoverageFinding] = []
        document_coverage = self._documents(coverage_input, findings)
        evidence_coverage = self._evidences(
            coverage_input,
            document_ids,
            fact_ids,
            evaluated_evidence,
            findings,
        )
        factual_coverage = self._facts(
            coverage_input,
            evidence_ids,
            binding_facts,
            evaluated_facts,
            validated_facts,
            compatible_facts,
            findings,
        )
        normative_coverage = self._normative(coverage_input)
        covered = (
            document_coverage.used
            + evidence_coverage.with_documents
            + evidence_coverage.with_execution_facts
            + factual_coverage.bound
        )
        total = (
            document_coverage.total
            + evidence_coverage.total * 2
            + factual_coverage.total
        )
        overall = OverallCoverage(
            state=_state(covered, total),
            covered=covered,
            total=total,
            ratio=Fraction(covered, total) if total else Fraction(0, 1),
        )
        return CoverageResult(
            document_coverage=document_coverage,
            evidence_coverage=evidence_coverage,
            factual_coverage=factual_coverage,
            normative_coverage=normative_coverage,
            overall_coverage=overall,
            findings=tuple(sorted(findings, key=_finding_key)),
            source_revisions=CoverageSourceRevisions(
                project_revision=coverage_input.project_revision,
                evaluation_revision=(
                    None if evaluation is None else evaluation.revision
                ),
            ),
            analysis_version=self.analysis_version,
        )

    @staticmethod
    def _documents(coverage_input, findings) -> DocumentCoverage:
        used = 0
        multiple = 0
        for document in coverage_input.documents:
            relations = len(document.evidences)
            if relations:
                used += 1
            else:
                findings.append(CoverageFinding(
                    CoverageScope.DOCUMENT,
                    document.identity,
                    CoverageState.ABSENT,
                    0,
                    1,
                    "O Document não possui relação com Evidence.",
                    ("DOCUMENT_WITHOUT_EVIDENCE",),
                ))
            if relations > 1:
                multiple += 1
        total = len(coverage_input.documents)
        unused = total - used
        return DocumentCoverage(
            _state(used, total), total, used, unused, multiple, unused
        )

    @staticmethod
    def _evidences(
        coverage_input,
        document_ids,
        fact_ids,
        evaluated,
        findings,
    ) -> EvidenceCoverage:
        with_documents = 0
        with_facts = 0
        inconsistencies = 0
        for evidence in coverage_input.evidences:
            if evidence.documents:
                with_documents += 1
            else:
                findings.append(CoverageFinding(
                    CoverageScope.EVIDENCE,
                    evidence.identity,
                    CoverageState.ABSENT,
                    0,
                    1,
                    "A Evidence não possui referência a Document.",
                    ("EVIDENCE_WITHOUT_DOCUMENT",),
                ))
            if evidence.execution_facts:
                with_facts += 1
            else:
                findings.append(CoverageFinding(
                    CoverageScope.EVIDENCE,
                    evidence.identity,
                    CoverageState.INSUFFICIENT,
                    0,
                    1,
                    "A Evidence não possui referência a ExecutionFact.",
                    ("EVIDENCE_WITHOUT_EXECUTION_FACT",),
                ))
            missing = tuple(
                item
                for item in (*evidence.documents, *evidence.execution_facts)
                if item not in document_ids and item not in fact_ids
            )
            if missing:
                inconsistencies += 1
                findings.append(CoverageFinding(
                    CoverageScope.EVIDENCE,
                    evidence.identity,
                    CoverageState.INCONSISTENT,
                    0,
                    len(missing),
                    "A Evidence referencia elementos ausentes da entrada.",
                    ("EVIDENCE_DANGLING_REFERENCE",),
                    missing,
                ))
        total = len(coverage_input.evidences)
        covered_dimensions = with_documents + with_facts
        state = (
            CoverageState.INCONSISTENT
            if inconsistencies
            else _state(covered_dimensions, total * 2)
        )
        return EvidenceCoverage(
            state,
            total,
            with_documents,
            total - with_documents,
            with_facts,
            total - with_facts,
            sum(item.identity in evaluated for item in coverage_input.evidences),
            inconsistencies,
        )

    @staticmethod
    def _facts(
        coverage_input,
        evidence_ids,
        binding_facts,
        evaluated,
        validated,
        compatible,
        findings,
    ) -> FactualCoverage:
        bound = 0
        inconsistencies = 0
        for fact in coverage_input.execution_facts:
            if fact.identity in binding_facts:
                bound += 1
            else:
                findings.append(CoverageFinding(
                    CoverageScope.FACTUAL,
                    fact.identity,
                    CoverageState.INSUFFICIENT,
                    0,
                    1,
                    "O ExecutionFact existe e aguarda Binding.",
                    ("EXECUTION_FACT_WITHOUT_BINDING",),
                    (fact.evidence,),
                ))
            if fact.evidence not in evidence_ids:
                inconsistencies += 1
                findings.append(CoverageFinding(
                    CoverageScope.FACTUAL,
                    fact.identity,
                    CoverageState.INCONSISTENT,
                    0,
                    1,
                    "O ExecutionFact referencia Evidence ausente da entrada.",
                    ("EXECUTION_FACT_WITHOUT_EVIDENCE",),
                    (fact.evidence,),
                ))
        total = len(coverage_input.execution_facts)
        state = (
            CoverageState.INCONSISTENT
            if inconsistencies
            else _state(bound, total)
        )
        return FactualCoverage(
            state,
            total,
            bound,
            total - bound,
            sum(item.identity in evaluated for item in coverage_input.execution_facts),
            total - bound,
            sum(item.identity in validated for item in coverage_input.execution_facts),
            sum(item.identity in compatible for item in coverage_input.execution_facts),
        )

    @staticmethod
    def _normative(coverage_input) -> NormativeCoverage:
        evaluation = coverage_input.evaluation
        if evaluation is None:
            return NormativeCoverage(CoverageState.NOT_EVALUATED, 0, 0)
        requirements = tuple(
            item for item in evaluation.normative_results
            if item.identity.resource_type is ResourceType.REQUIREMENT
        )
        criteria = tuple(
            item for item in evaluation.normative_results
            if item.identity.resource_type is ResourceType.CRITERION
        )
        return NormativeCoverage(
            CoverageState.COMPLETE,
            len(requirements),
            len(criteria),
            _state_counts(requirements),
            _state_counts(criteria),
        )


def _state(covered: int, total: int) -> CoverageState:
    if total == 0:
        return CoverageState.EMPTY
    if covered == total:
        return CoverageState.COMPLETE
    return CoverageState.PARTIAL


def _state_counts(values) -> tuple[StateCount, ...]:
    counts = Counter(item.state for item in values)
    return tuple(StateCount(state, counts[state]) for state in sorted(counts))


def _finding_key(item: CoverageFinding):
    return (
        item.scope.value,
        item.subject.resource_type.value,
        item.subject.resource_id,
        item.reason_codes,
    )


__all__ = ["CoverageAnalyzer"]
