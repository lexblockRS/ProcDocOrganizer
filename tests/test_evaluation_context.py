from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
from datetime import date
import json
from pathlib import Path
import unittest
from uuid import uuid4

from applications.rsc.evaluation_context import (
    DuplicateEvaluationObjectError,
    EvaluationContextBuilder,
    IncompleteEvaluationTraceabilityError,
    InvalidEvaluationReferenceError,
)
from applications.rsc.models import (
    Activity,
    FunctionalAssignmentEvidence,
    FunctionalAssignmentEvidenceId,
    FunctionalAssignmentEvidenceStatus,
    FunctionalContext,
    FunctionalExercise,
    FunctionalExerciseId,
    FunctionalExerciseStatus,
    FunctionalExerciseType,
    FunctionalPeriod,
    FunctionalRole,
    SourceEvidenceReference,
)
from models import Document, Evidence, Project


class OrderedRepository:
    def __init__(self, *values) -> None:
        self.values = list(values)
        self.read_count = 0

    def list_all(self):
        self.read_count += 1
        return tuple(self.values)


class EvaluationContextTests(unittest.TestCase):
    def setUp(self) -> None:
        self.document_hash = "a" * 64
        self.document = Document(
            id=str(uuid4()),
            name="Portaria.pdf",
            relative_path="documents/portaria.pdf",
            imported_at="2026-07-01T10:00:00",
            pages=3,
            sha256=self.document_hash,
            document_type="portaria",
            original_filename="Portaria.pdf",
            stored_filename="portaria.pdf",
            file_size=1024,
            extension=".pdf",
            mime_type="application/pdf",
            created_at="2026-07-01T10:00:00",
            updated_at="2026-07-01T10:00:00",
        )
        self.evidence = Evidence(
            id=str(uuid4()),
            document_identity=self.document_hash,
            page_number=2,
            title="Designação",
            source_snippet="Trecho factual",
            user_notes="Conferido",
            category="ato",
            start_date="2020-01-01",
            end_date=None,
            created_at="2026-07-01T10:01:00",
            updated_at="2026-07-01T10:01:00",
        )
        self.assignment_id = FunctionalAssignmentEvidenceId(str(uuid4()))
        self.assignment = FunctionalAssignmentEvidence(
            id=self.assignment_id,
            person_id="person-1",
            source_evidence_reference=SourceEvidenceReference(
                self.evidence.id
            ),
            exercise_type_code="chefia",
            exercise_type_label="Chefia",
            role="Chefe",
            organization="Instituição",
            start_date=date(2020, 1, 1),
            unit="Unidade",
            administrative_reference="Portaria 1/2020",
            status=FunctionalAssignmentEvidenceStatus.LINKED,
        )
        self.exercise_id = FunctionalExerciseId(str(uuid4()))
        self.exercise = FunctionalExercise(
            id=self.exercise_id,
            person_id="person-1",
            exercise_type=FunctionalExerciseType("chefia", "Chefia"),
            role=FunctionalRole("Chefe"),
            context=FunctionalContext(
                organization="Instituição",
                unit="Unidade",
                reference="Portaria 1/2020",
            ),
            period=FunctionalPeriod(start_date=date(2020, 1, 1)),
            status=FunctionalExerciseStatus.ACTIVE,
            functional_assignment_evidence_ids=(self.assignment_id,),
        )
        self.activity = Activity(
            activity_id="activity-1",
            description="Exercício de chefia",
            functional_assignment_evidence_ids=(self.assignment_id,),
            functional_exercise_ids=(self.exercise_id,),
        )
        self.project = Project(
            project_name="Projeto",
            project_path=Path("C:/projetos/projeto"),
            created_at="2026-07-01T09:00:00",
            last_opened_at="2026-07-01T09:30:00",
            application="rsc",
        )
        self.activity_repository = OrderedRepository(self.activity)
        self.exercise_repository = OrderedRepository(self.exercise)
        self.assignment_repository = OrderedRepository(self.assignment)
        self.evidence_repository = OrderedRepository(self.evidence)
        self.document_repository = OrderedRepository(self.document)

    def builder(self) -> EvaluationContextBuilder:
        return EvaluationContextBuilder(
            activity_repository=self.activity_repository,
            functional_exercise_repository=self.exercise_repository,
            functional_assignment_evidence_repository=(
                self.assignment_repository
            ),
            evidence_repository=self.evidence_repository,
            document_repository=self.document_repository,
        )

    def test_builds_complete_factual_snapshot(self):
        context = self.builder().build(
            self.project,
            metadata={"source": "manual", "tags": ["validado"]},
        )

        self.assertEqual(context.project.project_name, "Projeto")
        self.assertEqual(
            context.activities[0].functional_exercise_ids,
            (str(self.exercise_id),),
        )
        self.assertEqual(
            context.functional_exercises[
                0
            ].functional_assignment_evidence_ids,
            (str(self.assignment_id),),
        )
        self.assertEqual(
            context.functional_assignment_evidences[0].source_evidence_id,
            self.evidence.id,
        )
        self.assertEqual(
            context.evidences[0].document_identity,
            context.documents[0].document_identity,
        )
        self.assertEqual(context.metadata["tags"], ("validado",))

    def test_snapshot_is_deeply_immutable_and_detached(self):
        metadata = {"nested": {"items": ["original"]}}
        context = self.builder().build(self.project, metadata)

        with self.assertRaises(FrozenInstanceError):
            context.project.project_name = "Outro"
        with self.assertRaises(TypeError):
            context.metadata["new"] = "value"
        with self.assertRaises(TypeError):
            context.metadata["nested"]["new"] = "value"

        self.document.name = "Alterado.pdf"
        self.activity_repository.values.clear()
        metadata["nested"]["items"].append("alterado")

        self.assertEqual(context.documents[0].name, "Portaria.pdf")
        self.assertEqual(len(context.activities), 1)
        self.assertEqual(
            context.metadata["nested"]["items"],
            ("original",),
        )

        with self.assertRaises(TypeError):
            replace(context, activities=list(context.activities))

    def test_preserves_repository_order(self):
        second_document = Document(
            id=str(uuid4()),
            name="Segundo.pdf",
            relative_path="documents/segundo.pdf",
            imported_at="2026-07-02T10:00:00",
            sha256="b" * 64,
        )
        self.document_repository.values.append(second_document)

        context = self.builder().build(self.project)

        self.assertEqual(
            tuple(item.name for item in context.documents),
            ("Portaria.pdf", "Segundo.pdf"),
        )

    def test_rejects_duplicate_identities(self):
        self.evidence_repository.values.append(self.evidence)

        with self.assertRaises(DuplicateEvaluationObjectError):
            self.builder().build(self.project)

    def test_rejects_invalid_activity_reference(self):
        self.activity_repository.values[0] = Activity(
            activity_id="activity-1",
            description="Referência inválida",
            functional_exercise_ids=(
                FunctionalExerciseId(str(uuid4())),
            ),
        )

        with self.assertRaises(InvalidEvaluationReferenceError):
            self.builder().build(self.project)

    def test_rejects_invalid_assignment_to_evidence_reference(self):
        self.assignment_repository.values[0] = (
            FunctionalAssignmentEvidence(
                id=self.assignment_id,
                person_id="person-1",
                source_evidence_reference=SourceEvidenceReference(
                    str(uuid4())
                ),
                exercise_type_code="chefia",
                exercise_type_label="Chefia",
                role="Chefe",
                organization="Instituição",
            )
        )

        with self.assertRaises(InvalidEvaluationReferenceError):
            self.builder().build(self.project)

    def test_rejects_evidence_without_document_origin(self):
        self.document_repository.values.clear()

        with self.assertRaises(IncompleteEvaluationTraceabilityError):
            self.builder().build(self.project)

    def test_serialization_returns_independent_standard_values(self):
        context = self.builder().build(
            self.project,
            {"nested": {"items": ["one", "two"]}},
        )

        payload = context.to_dict()
        encoded = json.dumps(payload)
        payload["metadata"]["nested"]["items"].append("three")

        self.assertIn('"activities"', encoded)
        self.assertEqual(
            context.metadata["nested"]["items"],
            ("one", "two"),
        )

    def test_builder_reads_each_repository_once(self):
        self.builder().build(self.project)

        repositories = (
            self.activity_repository,
            self.exercise_repository,
            self.assignment_repository,
            self.evidence_repository,
            self.document_repository,
        )
        self.assertTrue(
            all(repository.read_count == 1 for repository in repositories)
        )


if __name__ == "__main__":
    unittest.main()
