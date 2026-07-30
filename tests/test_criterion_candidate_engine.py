from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
import unittest

from applications.rsc.criterion_candidates import (
    CriterionCandidateCollection,
    CriterionCandidateEngine,
    StructuralConfidence,
)
from applications.rsc.evaluation_context import (
    EvaluationActivity,
    EvaluationContext,
    EvaluationDocument,
    EvaluationEvidence,
    EvaluationFunctionalAssignmentEvidence,
    EvaluationFunctionalExercise,
    EvaluationProject,
)


@dataclass(frozen=True)
class CriterionRecord:
    id: str
    requirement_id: str
    document_id: str = "BR-DEC-13048-2026"
    legal_reference: str = "Anexo I, item 1"
    hierarchy: tuple[str, ...] = ("decree", "annex:I", "item:1")


@dataclass(frozen=True)
class RequirementRecord:
    id: str


@dataclass(frozen=True)
class DocumentRecord:
    id: str
    legal_reference: str = "Art. 4º, parágrafo único, inciso I"


class NormativeModelStub:
    def __init__(self) -> None:
        self.criteria = {
            "DEC13048-ANX-I-ITEM-01": CriterionRecord(
                id="DEC13048-ANX-I-ITEM-01",
                requirement_id="DEC13048-ART3-I",
            ),
            "DEC13048-ANX-I-ITEM-02": CriterionRecord(
                id="DEC13048-ANX-I-ITEM-02",
                requirement_id="DEC13048-ART3-I",
                legal_reference="Anexo I, item 2",
                hierarchy=("decree", "annex:I", "item:2"),
            ),
        }
        self.requirements = {
            "DEC13048-ART3-I": RequirementRecord("DEC13048-ART3-I")
        }
        self.documents = {
            "DEC13048-ART4-PU-I": DocumentRecord(
                "DEC13048-ART4-PU-I"
            )
        }

    def find_criterion(self, criterion_id):
        return self.criteria.get(criterion_id)

    def find_requirement(self, requirement_id):
        return self.requirements.get(requirement_id)

    def find_accepted_document(self, document_type_id):
        return self.documents.get(document_type_id)


def factual_chain(index: int):
    suffix = str(index)
    document_identity = suffix * 64
    activity = EvaluationActivity(
        activity_id=f"activity-{suffix}",
        description=f"Activity {suffix}",
        state="lembrada",
        functional_assignment_evidence_ids=(f"assignment-{suffix}",),
        functional_exercise_ids=(f"exercise-{suffix}",),
    )
    exercise = EvaluationFunctionalExercise(
        id=f"exercise-{suffix}",
        person_id="person-1",
        exercise_type_code="explicit",
        exercise_type_label="Explicit",
        role="Role",
        organization="Institution",
        unit=None,
        administrative_reference=None,
        start_date="2020-01-01",
        end_date=None,
        status="active",
        functional_assignment_evidence_ids=(f"assignment-{suffix}",),
    )
    assignment = EvaluationFunctionalAssignmentEvidence(
        id=f"assignment-{suffix}",
        person_id="person-1",
        source_evidence_id=f"evidence-{suffix}",
        exercise_type_code="explicit",
        exercise_type_label="Explicit",
        role="Role",
        organization="Institution",
        start_date="2020-01-01",
        end_date=None,
        unit=None,
        administrative_reference=None,
        status="linked",
    )
    evidence = EvaluationEvidence(
        id=f"evidence-{suffix}",
        document_identity=document_identity,
        page_number=1,
        title="Evidence",
        source_snippet="Source",
        user_notes=None,
        category=None,
        start_date=None,
        end_date=None,
        created_at="2026-07-01T10:00:00",
        updated_at="2026-07-01T10:00:00",
    )
    document = EvaluationDocument(
        id=f"document-{suffix}",
        document_identity=document_identity,
        name=f"Document {suffix}",
        relative_path=f"documents/{suffix}.pdf",
        imported_at="2026-07-01T10:00:00",
        pages=1,
        status="imported",
        document_type="portaria",
        processed_at=None,
        processing_status="not_processed",
        original_filename=f"{suffix}.pdf",
        stored_filename=f"{suffix}.pdf",
        file_size=1,
        extension=".pdf",
        mime_type="application/pdf",
        created_at="2026-07-01T10:00:00",
        updated_at="2026-07-01T10:00:00",
    )
    link = {
        "criterion_id": "DEC13048-ANX-I-ITEM-01",
        "activity_id": activity.activity_id,
        "functional_exercise_id": exercise.id,
        "functional_assignment_evidence_id": assignment.id,
        "evidence_id": evidence.id,
        "document_identity": document.document_identity,
        "accepted_document_id": "DEC13048-ART4-PU-I",
    }
    return activity, exercise, assignment, evidence, document, link


def context_with(chains=(), links=()):
    activities = tuple(chain[0] for chain in chains)
    exercises = tuple(chain[1] for chain in chains)
    assignments = tuple(chain[2] for chain in chains)
    evidences = tuple(chain[3] for chain in chains)
    documents = tuple(chain[4] for chain in chains)
    metadata = MappingProxyType({
        "criterion_candidate_links": tuple(
            MappingProxyType(dict(link)) for link in links
        )
    })
    return EvaluationContext(
        project=EvaluationProject(
            project_name="Project",
            project_path="C:/project",
            created_at="2026-07-01T09:00:00",
            last_opened_at="2026-07-01T09:00:00",
            application="rsc",
            format_version=1,
            database="database.db",
        ),
        activities=activities,
        functional_exercises=exercises,
        functional_assignment_evidences=assignments,
        evidences=evidences,
        documents=documents,
        metadata=metadata,
    )


class CriterionCandidateEngineTests(unittest.TestCase):
    def setUp(self) -> None:
        self.model = NormativeModelStub()
        self.engine = CriterionCandidateEngine(self.model)

    def test_empty_context_produces_empty_collection(self):
        result = self.engine.generate(context_with())

        self.assertIsInstance(result, CriterionCandidateCollection)
        self.assertEqual(len(result), 0)

    def test_single_activity_produces_candidate(self):
        chain = factual_chain(1)

        result = self.engine.generate(
            context_with((chain,), (chain[5],))
        )

        self.assertEqual(len(result), 1)
        candidate = result.candidates[0]
        self.assertEqual(
            candidate.criterion_id,
            "DEC13048-ANX-I-ITEM-01",
        )
        self.assertEqual(candidate.requirement_id, "DEC13048-ART3-I")
        self.assertEqual(candidate.activity.activity_id, "activity-1")
        self.assertEqual(
            candidate.functional_exercise.id,
            "exercise-1",
        )
        self.assertIs(
            candidate.confidence,
            StructuralConfidence.ACCEPTED_DOCUMENT_CHAIN,
        )

    def test_multiple_activities_preserve_link_order(self):
        first = factual_chain(1)
        second = factual_chain(2)

        result = self.engine.generate(
            context_with(
                (first, second),
                (second[5], first[5]),
            )
        )

        self.assertEqual(
            tuple(item.activity.activity_id for item in result),
            ("activity-2", "activity-1"),
        )

    def test_repeated_criterion_link_is_deduplicated(self):
        chain = factual_chain(1)

        result = self.engine.generate(
            context_with((chain,), (chain[5], chain[5]))
        )

        self.assertEqual(len(result), 1)

    def test_incompatible_document_category_is_not_candidate(self):
        chain = factual_chain(1)
        incompatible = {
            **chain[5],
            "accepted_document_id": "UNKNOWN-DOCUMENT-TYPE",
        }

        result = self.engine.generate(
            context_with((chain,), (incompatible,))
        )

        self.assertEqual(len(result), 0)

    def test_candidate_preserves_normative_and_factual_traceability(self):
        chain = factual_chain(1)

        candidate = self.engine.generate(
            context_with((chain,), (chain[5],))
        ).candidates[0]

        self.assertEqual(
            candidate.normative_origin.document_id,
            "BR-DEC-13048-2026",
        )
        self.assertEqual(
            candidate.normative_origin.legal_reference,
            "Anexo I, item 1",
        )
        self.assertEqual(
            candidate.factual_traceability.functional_assignment_evidence_id,
            "assignment-1",
        )
        self.assertEqual(
            candidate.factual_traceability.evidence_id,
            "evidence-1",
        )
        self.assertEqual(
            candidate.factual_traceability.document_id,
            "document-1",
        )

    def test_justification_is_technical_and_explicit(self):
        chain = factual_chain(1)

        candidate = self.engine.generate(
            context_with((chain,), (chain[5],))
        ).candidates[0]

        self.assertIn("Vínculo explícito", candidate.technical_justification)
        self.assertIn("Activity activity-1", candidate.technical_justification)
        self.assertIn(
            "categoria documental aceita",
            candidate.technical_justification,
        )
        self.assertNotIn("satisfeito", candidate.technical_justification)

    def test_generation_is_deterministic_and_repeatable(self):
        first = factual_chain(1)
        second = factual_chain(2)
        context = context_with(
            (first, second),
            (first[5], second[5]),
        )

        initial = self.engine.generate(context)
        repeated = self.engine.generate(context)
        fresh_engine = CriterionCandidateEngine(self.model).generate(context)

        self.assertEqual(initial, repeated)
        self.assertEqual(initial, fresh_engine)


if __name__ == "__main__":
    unittest.main()
