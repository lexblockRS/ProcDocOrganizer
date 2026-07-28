from datetime import datetime, timezone
import hashlib
import os
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from applications.rsc import RscApplication, RscApplicationFacade
from applications.rsc.dto import ManagedDocumentStatus
from applications.rsc.infrastructure import DocumentHashService
from applications.rsc.infrastructure.document_files import (
    FILE_EXTENSION_KEY,
    FILE_SIZE_KEY,
    LAST_MODIFIED_AT_KEY,
    MANAGED_STATUS_KEY,
    REFERENCE_MODE_KEY,
)
from applications.rsc.use_cases import (
    CreateActivityCommand,
    CreateEvidenceCommand,
    CreateProcessCommand,
    LoadProjectCommand,
    RegisterDocumentCommand,
    SaveProjectCommand,
    UpdateDocumentReferenceCommand,
    VerifyDocumentsCommand,
)
from applications.rsc.domain import criterion_id


class EvidenceLookup:
    def exists(self, _evidence_id):
        return True


class DocumentManagementTests(unittest.TestCase):
    def setUp(self):
        self.temporary = TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.session = RscApplication().create_project_session(EvidenceLookup())
        self.facade = RscApplicationFacade(self.session)
        self.process = self.facade.create_process(
            CreateProcessCommand("Pessoa", "Instituição")
        )

    def write(self, name, content):
        path = self.root / name
        path.write_bytes(content)
        return path

    def register_and_update(self, path):
        registered = self.facade.register_document(
            RegisterDocumentCommand(
                self.process.process_id, Path(path).name
            )
        )
        updated = self.facade.update_document_reference(
            UpdateDocumentReferenceCommand(registered.document_id, path)
        )
        return registered, updated

    def diagnostic(self, document_id):
        result = self.facade.verify_documents(VerifyDocumentsCommand())
        return next(
            item for item in result.diagnostics
            if item.document_id == document_id
        )

    def test_hash_service_calculates_sha256_size_timestamp_and_extension(self):
        path = self.write("proof.BIN", b"generic binary")
        result = DocumentHashService().inspect(path)

        self.assertTrue(result.exists)
        self.assertTrue(result.is_file)
        self.assertEqual(
            result.sha256, hashlib.sha256(b"generic binary").hexdigest()
        )
        self.assertEqual(result.size, len(b"generic binary"))
        self.assertEqual(result.extension, ".bin")
        self.assertIsNotNone(
            datetime.fromisoformat(result.last_modified_at).astimezone(
                timezone.utc
            )
        )

    def test_update_reference_preserves_id_links_and_records_identity(self):
        path = self.write("ato.pdf", b"not interpreted as pdf")
        registered, updated = self.register_and_update(path)
        activity = self.facade.create_activity(
            CreateActivityCommand(
                self.process.process_id,
                criterion_id(1, 1),
                "Atividade",
                "1",
            )
        )
        evidence = self.facade.create_evidence(
            CreateEvidenceCommand(
                self.process.process_id,
                activity.activity_id,
                (registered.document_id,),
                "Ato",
            )
        )

        self.assertEqual(updated.document_id, registered.document_id)
        self.assertIn(updated.document_id, self.process.process.document_ids)
        self.assertIn(updated.document_id, evidence.evidence.document_ids)
        self.assertEqual(updated.document.original_path, str(path))
        self.assertEqual(updated.document.metadata[FILE_EXTENSION_KEY], ".pdf")
        self.assertEqual(updated.document.metadata[FILE_SIZE_KEY], 22)
        self.assertEqual(
            updated.document.metadata[MANAGED_STATUS_KEY], "available"
        )
        self.assertEqual(
            updated.document.metadata[REFERENCE_MODE_KEY], "referenced"
        )

    def test_verify_detects_hash_size_and_timestamp_changes(self):
        path = self.write("proof.bin", b"abc")
        registered, updated = self.register_and_update(path)
        baseline_timestamp = datetime.fromisoformat(updated.last_modified_at)

        path.write_bytes(b"xyz")
        os.utime(path, (baseline_timestamp.timestamp(), baseline_timestamp.timestamp()))
        hash_change = self.diagnostic(registered.document_id)
        self.assertIs(hash_change.status, ManagedDocumentStatus.MODIFIED)
        self.assertTrue(hash_change.hash_changed)
        self.assertFalse(hash_change.size_changed)
        self.assertFalse(hash_change.modified_date_changed)

        path.write_bytes(b"longer")
        size_change = self.diagnostic(registered.document_id)
        self.assertTrue(size_change.size_changed)

        path.write_bytes(b"abc")
        future = baseline_timestamp.timestamp() + 10
        os.utime(path, (future, future))
        timestamp_change = self.diagnostic(registered.document_id)
        self.assertFalse(timestamp_change.hash_changed)
        self.assertFalse(timestamp_change.size_changed)
        self.assertTrue(timestamp_change.modified_date_changed)

    def test_verify_detects_missing_invalid_and_duplicate_documents(self):
        shared = self.write("shared.bin", b"same")
        first, _ = self.register_and_update(shared)
        second = self.facade.register_document(
            RegisterDocumentCommand(self.process.process_id, "copy.bin")
        )
        self.facade.update_document_reference(
            UpdateDocumentReferenceCommand(second.document_id, shared)
        )
        invalid = self.facade.register_document(
            RegisterDocumentCommand(self.process.process_id, "no-path.bin")
        )

        result = self.facade.verify_documents(VerifyDocumentsCommand())
        by_id = {item.document_id: item for item in result.diagnostics}
        self.assertIs(
            by_id[first.document_id].status,
            ManagedDocumentStatus.DUPLICATED,
        )
        self.assertIs(
            by_id[second.document_id].status,
            ManagedDocumentStatus.DUPLICATED,
        )
        self.assertIs(
            by_id[invalid.document_id].status,
            ManagedDocumentStatus.INVALID_REFERENCE,
        )
        shared.unlink()
        missing = self.diagnostic(first.document_id)
        self.assertIs(missing.status, ManagedDocumentStatus.MISSING)
        self.assertFalse(missing.exists)

    def test_document_identity_round_trip_and_multiple_documents(self):
        first, first_update = self.register_and_update(
            self.write("one.bin", b"one")
        )
        second, second_update = self.register_and_update(
            self.write("two.txt", b"two two")
        )
        project = self.root / "documents.pdop"

        self.facade.save_project(SaveProjectCommand(project))
        restored = RscApplication().create_project_session(EvidenceLookup())
        restored_facade = RscApplicationFacade(restored)
        restored_facade.load_project(LoadProjectCommand(project))
        documents = restored.rsc_document_service.list_documents()

        self.assertEqual(
            tuple(item.id for item in documents),
            (first.document_id, second.document_id),
        )
        self.assertEqual(
            tuple(item.checksum for item in documents),
            (first_update.checksum, second_update.checksum),
        )
        self.assertEqual(
            tuple(item.metadata[FILE_SIZE_KEY] for item in documents),
            (3, 7),
        )
        self.assertTrue(
            all(
                LAST_MODIFIED_AT_KEY in item.metadata
                for item in documents
            )
        )
        verification = restored_facade.verify_documents(
            VerifyDocumentsCommand()
        )
        self.assertEqual(verification.total, 2)
        self.assertEqual(verification.healthy_count, 2)


if __name__ == "__main__":
    unittest.main()
