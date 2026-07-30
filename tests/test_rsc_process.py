from __future__ import annotations

from dataclasses import FrozenInstanceError
from datetime import date
from decimal import Decimal
import unittest

from applications.rsc.execution_compatibility import (
    ExecutionCompatibilityCollection,
)
from applications.rsc.execution_contracts import (
    CriterionExecutionContractCollection,
)
from applications.rsc.execution_facts import ExecutionFactCollection
from applications.rsc.execution_validation import (
    ExecutionValidationCollection,
)
from applications.rsc.requirement_scoring import RequirementScoreAggregator
from applications.rsc.rsc_process import (
    IntendedRSCLevel,
    RSCInstitution,
    RSCProcess,
    RSCProcessError,
    RSCProcessEvidence,
    RSCProcessResult,
    RSCProcessStage,
    RSCServer,
)
from applications.rsc.scoring_kernel import (
    CriterionScoringKernel,
    ScoringState,
)
from applications.rsc.temporal_attention import TemporalAttentionAnalyzer
from test_per_year_scoring import year_contract
from test_scoring_kernel import contracts


def process() -> RSCProcess:
    return RSCProcess.create(
        process_id="process-1",
        server=RSCServer(
            server_id="server-1",
            name="Servidor Teste",
            functional_registration="12345",
        ),
        institution=RSCInstitution(
            institution_id="institution-1",
            name="Instituição Teste",
        ),
        intended_level=IntendedRSCLevel.RSC_II,
        process_date=date(2026, 7, 30),
    )


def sources(*collections) -> CriterionExecutionContractCollection:
    return CriterionExecutionContractCollection(tuple(
        contract
        for collection in collections
        for contract in collection
    ))


def advance(
    source: CriterionExecutionContractCollection,
    *,
    initial: RSCProcess | None = None,
) -> RSCProcess:
    facts = ExecutionFactCollection(tuple(
        contract.source_execution_fact for contract in source
    ))
    validations = ExecutionValidationCollection(tuple(
        contract.source_validation for contract in source
    ))
    compatibilities = ExecutionCompatibilityCollection(tuple(
        contract.source_compatibility for contract in source
    ))
    scores = CriterionScoringKernel().score(source)
    requirements = RequirementScoreAggregator().aggregate(scores)
    current = initial or process()
    return (
        current.record_execution_facts(facts)
        .record_validations(validations)
        .record_compatibilities(compatibilities)
        .record_criterion_scores(scores)
        .record_requirement_scores(requirements)
    )


def consolidate(
    current: RSCProcess,
    *,
    used_evidence_ids: tuple[str, ...] = (),
) -> RSCProcess:
    executed = tuple(
        score.criterion_id
        for score in current.criterion_scores
        if score.scoring_state is ScoringState.EXECUTED
    )
    non_computable = tuple(
        score.criterion_id
        for score in current.criterion_scores
        if score.scoring_state is not ScoringState.EXECUTED
    )
    total = sum(
        (
            requirement.total_score
            for requirement in current.requirement_scores
        ),
        Decimal(0),
    )
    pending = tuple(
        f"{score.criterion_id}:{score.scoring_state.value}"
        for score in current.criterion_scores
        if score.scoring_state is not ScoringState.EXECUTED
    )
    attentions = TemporalAttentionAnalyzer().analyze(
        current.criterion_scores
    )
    return current.consolidate(RSCProcessResult(
        total_score=total,
        computable_criterion_ids=executed,
        non_computable_criterion_ids=non_computable,
        pending_items=pending,
        temporal_attentions=attentions,
        used_evidence_ids=used_evidence_ids,
        explanation="Consolidação produzida externamente ao processo.",
    ))


class RSCProcessTests(unittest.TestCase):
    def test_empty_process_is_an_immutable_draft(self):
        current = process()

        self.assertEqual(current.stage, RSCProcessStage.DRAFT)
        self.assertEqual(len(current.execution_facts), 0)
        self.assertEqual(current.total_score, None)
        with self.assertRaises(FrozenInstanceError):
            current.process_id = "changed"

    def test_identity_is_stable_while_snapshot_equality_is_structural(self):
        original = process()
        revised = original.record_execution_facts(
            ExecutionFactCollection()
        )
        another = RSCProcess.create(
            process_id="process-2",
            server=original.server,
            institution=original.institution,
            intended_level=original.intended_level,
            process_date=original.process_date,
        )

        self.assertEqual(original.aggregate_id, "process-1")
        self.assertEqual(revised.aggregate_id, original.aggregate_id)
        self.assertTrue(original.same_process(revised))
        self.assertFalse(original.same_process(another))
        self.assertFalse(original.same_process(object()))
        self.assertNotEqual(original, revised)
        self.assertEqual((original.revision, revised.revision), (0, 1))

    def test_adds_one_simple_evidence_without_mutating_source(self):
        current = process()
        evidence = RSCProcessEvidence(
            evidence_id="evidence-1",
            document_id="document-1",
            description="Portaria funcional.",
            criterion_codes=("DEC13048-ANX-II-ITEM-07",),
        )

        updated = current.add_evidence(evidence)

        self.assertEqual(current.evidences, ())
        self.assertEqual(updated.evidences, (evidence,))
        self.assertEqual(updated.stage, RSCProcessStage.EVIDENCE)
        self.assertEqual(updated.revision, 1)

    def test_complete_process_exposes_multiple_criteria_and_requirements(self):
        source = sources(
            contracts(
                "DEC13048-ANX-II-ITEM-07",
                "DEC13048-ART3-II",
                "event_count",
                2,
            ),
            contracts(
                "DEC13048-ANX-VI-ITEM-10",
                "DEC13048-ART3-VI",
                "publication_count",
                3,
            ),
        )

        completed = consolidate(advance(source))

        self.assertEqual(completed.stage, RSCProcessStage.CONSOLIDATED)
        self.assertIsNotNone(
            completed.criterion_score("DEC13048-ANX-II-ITEM-07")
        )
        self.assertIsNotNone(
            completed.requirement_score("DEC13048-ART3-VI")
        )
        self.assertGreater(completed.total_score, Decimal(0))
        self.assertEqual(completed.pending_items, ())

    def test_partially_computable_process_preserves_pending_criterion(self):
        source = sources(
            contracts(
                "DEC13048-ANX-II-ITEM-07",
                "DEC13048-ART3-II",
                "event_count",
                1,
            ),
            contracts(
                "DEC13048-ANX-VI-ITEM-10",
                "DEC13048-ART3-VI",
                "publication_count",
                None,
            ),
        )

        completed = consolidate(advance(source))

        self.assertEqual(
            completed.result.computable_criterion_ids,
            ("DEC13048-ANX-II-ITEM-07",),
        )
        self.assertEqual(
            completed.result.non_computable_criterion_ids,
            ("DEC13048-ANX-VI-ITEM-10",),
        )
        self.assertEqual(len(completed.pending_items), 1)

    def test_incompatible_fact_remains_visible_as_a_blocked_score(self):
        source = contracts(
            "DEC13048-ANX-II-ITEM-07",
            "DEC13048-ART3-II",
            "duration_days",
            1,
        )

        completed = consolidate(advance(source))

        score = completed.criterion_scores.scores[0]
        self.assertEqual(score.scoring_state, ScoringState.BLOCKED)
        self.assertIn(score.criterion_id, completed.pending_items[0])

    def test_temporal_attention_is_preserved_in_result(self):
        temporal = CriterionExecutionContractCollection((
            year_contract(
                "2020-01-01",
                "2020-07-01",
                temporal_rule="FRACTION_ABOVE_SIX_MONTHS",
            ),
        ))

        completed = consolidate(advance(temporal))

        self.assertGreaterEqual(len(completed.temporal_attentions), 1)
        self.assertEqual(
            completed.temporal_attentions,
            completed.result.temporal_attentions.attentions,
        )

    def test_used_evidence_and_catalog_reference_are_queryable(self):
        evidence = RSCProcessEvidence(
            evidence_id="evidence-1",
            document_id="document-1",
            description="Documento do evento.",
            criterion_codes=("DEC13048-ANX-II-ITEM-07",),
        )
        current = process().add_evidence(evidence)
        source = contracts(
            "DEC13048-ANX-II-ITEM-07",
            "DEC13048-ART3-II",
            "event_count",
            1,
        )

        completed = consolidate(
            advance(source, initial=current),
            used_evidence_ids=("evidence-1",),
        )

        self.assertEqual(
            completed.evidences_for_criterion(
                "DEC13048-ANX-II-ITEM-07"
            ),
            (evidence,),
        )
        self.assertEqual(
            completed.result.used_evidence_ids,
            ("evidence-1",),
        )

    def test_rejects_criterion_outside_official_catalog(self):
        evidence = RSCProcessEvidence(
            evidence_id="evidence-1",
            document_id="document-1",
            description="Documento sem critério oficial.",
            criterion_codes=("UNKNOWN-CRITERION",),
        )

        with self.assertRaises(RSCProcessError):
            process().add_evidence(evidence)

    def test_rejects_skipped_pipeline_stage(self):
        with self.assertRaises(RSCProcessError):
            process().record_validations(
                ExecutionValidationCollection()
            )


if __name__ == "__main__":
    unittest.main()
