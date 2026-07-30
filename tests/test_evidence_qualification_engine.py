from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
import unittest

from applications.rsc.criterion_candidates import (
    CriterionCandidate,
    CriterionCandidateCollection,
    FactualTraceability,
    NormativeOrigin,
    StructuralConfidence,
)
from applications.rsc.evaluation_context import (
    EvaluationActivity,
    EvaluationContext,
    EvaluationDocument,
    EvaluationFunctionalExercise,
    EvaluationProject,
)
from applications.rsc.evidence_qualification import (
    EvidenceQualificationEngine,
    QualifiedCriterionCandidateCollection,
)


@dataclass(frozen=True)
class AcceptedDocumentRecord:
    id: str
    legal_reference: str


class NormativeModelStub:
    def __init__(self) -> None:
        self.documents = {
            "DOC-CATEGORY-1": AcceptedDocumentRecord(
                "DOC-CATEGORY-1",
                "Art. 4º, parágrafo único, inciso I",
            ),
            "DOC-CATEGORY-2": AcceptedDocumentRecord(
                "DOC-CATEGORY-2",
                "Art. 4º, parágrafo único, inciso II",
            ),
        }

    def find_accepted_document(self, document_type_id):
        return self.documents.get(document_type_id)

    def find_criterion(self, criterion_id):
        raise AssertionError("A qualificação não consulta critérios.")

    def find_requirement(self, requirement_id):
        raise AssertionError("A qualificação não consulta requisitos.")


def project_snapshot() -> EvaluationProject:
    return EvaluationProject(
        project_name="Project",
        project_path="C:/project",
        created_at="2026-07-01T09:00:00",
        last_opened_at="2026-07-01T09:00:00",
        application="rsc",
        format_version=1,
        database="database.db",
    )


def activity(index: int) -> EvaluationActivity:
    return EvaluationActivity(
        activity_id=f"activity-{index}",
        description=f"Activity {index}",
        state="lembrada",
        functional_assignment_evidence_ids=(),
        functional_exercise_ids=(),
    )


def exercise(index: int) -> EvaluationFunctionalExercise:
    return EvaluationFunctionalExercise(
        id=f"exercise-{index}",
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
        functional_assignment_evidence_ids=(),
    )


def document(index: int) -> EvaluationDocument:
    return EvaluationDocument(
        id=f"document-{index}",
        document_identity=str(index) * 64,
        name=f"Document {index}",
        relative_path=f"documents/{index}.pdf",
        imported_at="2026-07-01T10:00:00",
        pages=1,
        status="imported",
        document_type="explicit",
        processed_at=None,
        processing_status="not_processed",
        original_filename=f"{index}.pdf",
        stored_filename=f"{index}.pdf",
        file_size=1,
        extension=".pdf",
        mime_type="application/pdf",
        created_at="2026-07-01T10:00:00",
        updated_at="2026-07-01T10:00:00",
    )


def candidate(
    index: int,
    *,
    category_id: str | None = "DOC-CATEGORY-1",
) -> CriterionCandidate:
    related_activity = activity(index)
    related_exercise = exercise(index)
    return CriterionCandidate(
        criterion_id=f"criterion-{index}",
        requirement_id="requirement-1",
        normative_origin=NormativeOrigin(
            document_id="BR-DEC-13048-2026",
            legal_reference=f"Anexo I, item {index}",
            hierarchy=("decree", "annex:I", f"item:{index}"),
        ),
        activity=related_activity,
        functional_exercise=related_exercise,
        confidence=StructuralConfidence.EXPLICIT_CHAIN,
        technical_justification="Vínculo estrutural explícito.",
        factual_traceability=FactualTraceability(
            activity_id=related_activity.activity_id,
            functional_exercise_id=related_exercise.id,
            functional_assignment_evidence_id=f"assignment-{index}",
            evidence_id=f"evidence-{index}",
            document_id=f"document-{index}",
            document_identity=str(index) * 64,
            accepted_document_id=category_id,
        ),
    )


def link(
    item: CriterionCandidate,
    document_index: int,
    category_id: str | None,
    *,
    document_id: str | None = None,
):
    values = {
        "criterion_id": item.criterion_id,
        "activity_id": item.activity.activity_id,
        "functional_exercise_id": item.functional_exercise.id,
        "document_identity": str(document_index) * 64,
        "accepted_document_id": category_id,
    }
    if document_id is not None:
        values["document_id"] = document_id
    return values


def context(documents=(), links=()) -> EvaluationContext:
    return EvaluationContext(
        project=project_snapshot(),
        activities=(),
        functional_exercises=(),
        functional_assignment_evidences=(),
        evidences=(),
        documents=tuple(documents),
        metadata=MappingProxyType({
            "criterion_candidate_links": tuple(
                MappingProxyType(dict(item)) for item in links
            )
        }),
    )


class EvidenceQualificationEngineTests(unittest.TestCase):
    def setUp(self) -> None:
        self.model = NormativeModelStub()

    def qualify(self, context_value, *candidates):
        return EvidenceQualificationEngine(
            context_value,
            self.model,
        ).qualify(CriterionCandidateCollection(tuple(candidates)))

    def test_candidate_without_document_reports_missing_and_pending(self):
        item = candidate(1)

        result = self.qualify(context(), item).candidates[0]

        self.assertFalse(result.has_compatible_documentation)
        self.assertEqual(result.presented_documents, ())
        self.assertEqual(result.accepted_documents, ())
        self.assertEqual(
            tuple(entry.document_id for entry in result.missing_documents),
            ("document-1",),
        )
        self.assertEqual(
            tuple(
                entry.category_id for entry in result.pending_categories
            ),
            ("DOC-CATEGORY-1",),
        )

    def test_incompatible_document_is_present_but_not_accepted(self):
        item = candidate(1, category_id="UNKNOWN-CATEGORY")

        result = self.qualify(
            context((document(1),)),
            item,
        ).candidates[0]

        self.assertEqual(len(result.presented_documents), 1)
        self.assertEqual(result.accepted_documents, ())
        self.assertEqual(result.satisfied_categories, ())
        self.assertFalse(result.has_compatible_documentation)

    def test_multiple_documents_are_qualified_without_duplication(self):
        item = candidate(1)
        links = (
            link(item, 1, "DOC-CATEGORY-1"),
            link(item, 2, "DOC-CATEGORY-2"),
            link(item, 1, "DOC-CATEGORY-1"),
        )

        result = self.qualify(
            context((document(1), document(2)), links),
            item,
        ).candidates[0]

        self.assertEqual(
            tuple(entry.document_id for entry in result.presented_documents),
            ("document-1", "document-2"),
        )
        self.assertEqual(len(result.accepted_documents), 2)
        self.assertEqual(
            tuple(
                entry.category_id
                for entry in result.satisfied_categories
            ),
            ("DOC-CATEGORY-1", "DOC-CATEGORY-2"),
        )

    def test_satisfied_and_pending_categories_are_separated(self):
        item = candidate(1)
        links = (
            link(item, 1, "DOC-CATEGORY-1"),
            link(
                item,
                2,
                "DOC-CATEGORY-2",
                document_id="document-2",
            ),
        )

        result = self.qualify(
            context((document(1),), links),
            item,
        ).candidates[0]

        self.assertEqual(
            tuple(
                entry.category_id
                for entry in result.satisfied_categories
            ),
            ("DOC-CATEGORY-1",),
        )
        self.assertEqual(
            tuple(
                entry.category_id for entry in result.pending_categories
            ),
            ("DOC-CATEGORY-2",),
        )
        self.assertEqual(
            tuple(entry.document_id for entry in result.missing_documents),
            ("document-2",),
        )

    def test_normative_traceability_and_source_candidate_are_preserved(self):
        item = candidate(1)

        result = self.qualify(
            context((document(1),)),
            item,
        ).candidates[0]

        self.assertIs(result.source_candidate, item)
        self.assertIs(
            result.normative_traceability,
            item.normative_origin,
        )
        self.assertEqual(
            result.accepted_documents[0].category.legal_reference,
            "Art. 4º, parágrafo único, inciso I",
        )

    def test_documentary_justification_does_not_decide_criterion(self):
        item = candidate(1)

        result = self.qualify(
            context((document(1),)),
            item,
        ).candidates[0]

        self.assertIn(
            "compatibilidade documental",
            result.documentary_justification,
        )
        self.assertNotIn(
            "critério satisfeito",
            result.documentary_justification,
        )

    def test_qualification_is_repeatable(self):
        item = candidate(1)
        context_value = context((document(1),))
        engine = EvidenceQualificationEngine(context_value, self.model)
        source = CriterionCandidateCollection((item,))

        self.assertEqual(engine.qualify(source), engine.qualify(source))

    def test_candidate_order_is_preserved(self):
        first = candidate(1)
        second = candidate(2)
        source = CriterionCandidateCollection((second, first))

        result = EvidenceQualificationEngine(
            context((document(1), document(2))),
            self.model,
        ).qualify(source)

        self.assertEqual(
            tuple(
                item.source_candidate.criterion_id for item in result
            ),
            ("criterion-2", "criterion-1"),
        )

    def test_empty_collection_remains_empty(self):
        result = self.qualify(context())

        self.assertIsInstance(
            result,
            QualifiedCriterionCandidateCollection,
        )
        self.assertEqual(len(result), 0)


if __name__ == "__main__":
    unittest.main()
