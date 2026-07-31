from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from database import EvidenceNotFoundError, SQLiteEvidenceStore
from platform_sdk import Document, Evidence, EvidenceState, Project


class EvidenceAggregateTests(unittest.TestCase):
    def setUp(self) -> None:
        self.project = Project.create(name="Processo", application_id="rsc")
        self.created_at = datetime(2026, 7, 30, tzinfo=timezone.utc)
        self.evidence = Evidence.create(
            project_id=self.project.aggregate_id,
            title="Portaria de designação",
            description="Comprovação funcional",
            metadata=(("origem", "manual"),),
            now=self.created_at,
        )
        self.document = Document(
            document_id="doc-001",
            name="portaria.pdf",
            relative_path="documents/portaria.pdf",
            document_type="application/pdf",
            sha256="a" * 64,
            size=2048,
        )

    def test_create_and_edit_title_preserve_identity(self):
        updated = self.evidence.edit(
            title="Portaria atualizada",
            now=self.created_at + timedelta(minutes=1),
        )

        self.assertTrue(updated.same_evidence(self.evidence))
        self.assertEqual(updated.aggregate_id, self.evidence.aggregate_id)
        self.assertEqual(updated.created_at, self.created_at)
        self.assertGreater(updated.updated_at, self.evidence.updated_at)
        self.assertEqual(updated.state, EvidenceState.ACTIVE)

    def test_add_and_remove_document(self):
        with_document = self.evidence.add_document(
            self.document,
            now=self.created_at + timedelta(minutes=1),
        )
        without_document = with_document.remove_document(
            self.document.document_id,
            now=self.created_at + timedelta(minutes=2),
        )

        self.assertEqual(with_document.documents, (self.document,))
        self.assertEqual(without_document.documents, ())
        self.assertTrue(without_document.same_evidence(self.evidence))

    def test_document_path_must_be_workspace_relative(self):
        with self.assertRaises(ValueError):
            Document(
                document_id="doc-002",
                name="externo.pdf",
                relative_path="../externo.pdf",
                document_type="application/pdf",
            )


class SQLiteEvidenceStoreTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = TemporaryDirectory()
        self.database_path = (
            Path(self.temporary_directory.name) / "projects.sqlite"
        )
        self.project = Project.create(name="Processo", application_id="rsc")
        self.timestamp = datetime(2026, 7, 30, 12, tzinfo=timezone.utc)

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def test_persist_and_reopen_preserves_identity_and_documents(self):
        document = Document(
            document_id="documento-1",
            name="certidao.pdf",
            relative_path="documents/certidao.pdf",
            document_type="application/pdf",
            size=512,
        )
        evidence = Evidence.create(
            project_id=self.project.aggregate_id,
            title="Certidão",
            description="Documento comprobatório",
            metadata=(("categoria", "funcional"),),
            now=self.timestamp,
        ).add_document(document, now=self.timestamp + timedelta(seconds=1))

        with SQLiteEvidenceStore(self.database_path) as store:
            store.save(evidence)
        with SQLiteEvidenceStore(self.database_path) as reopened_store:
            reopened = reopened_store.get(evidence.aggregate_id)

        self.assertTrue(reopened.same_evidence(evidence))
        self.assertEqual(reopened.project_id, self.project.aggregate_id)
        self.assertEqual(reopened.documents, (document,))
        self.assertEqual(reopened.metadata, evidence.metadata)
        self.assertEqual(reopened.created_at, evidence.created_at)
        self.assertEqual(reopened.updated_at, evidence.updated_at)

    def test_list_is_scoped_to_project_and_delete_is_persistent(self):
        other_project = Project.create(name="Outro", application_id="rsc")
        first = Evidence.create(
            project_id=self.project.aggregate_id,
            title="Primeira",
            now=self.timestamp,
        )
        second = Evidence.create(
            project_id=other_project.aggregate_id,
            title="Segunda",
            now=self.timestamp,
        )

        with SQLiteEvidenceStore(self.database_path) as store:
            store.save(first)
            store.save(second)
            self.assertEqual(store.list_for_project(
                self.project.aggregate_id
            ), (first,))
            store.delete(first.aggregate_id)
            with self.assertRaises(EvidenceNotFoundError):
                store.get(first.aggregate_id)


if __name__ == "__main__":
    unittest.main()
