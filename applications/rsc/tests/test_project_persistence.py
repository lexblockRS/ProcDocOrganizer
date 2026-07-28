from dataclasses import replace
from datetime import date, datetime, timezone
from decimal import Decimal
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from zipfile import ZIP_DEFLATED, ZipFile

from applications.rsc import RscApplication, RscApplicationFacade
from applications.rsc.domain import (
    ActivityStatus,
    DocumentStatus,
    EvidenceStatus,
    criterion_id,
)
from applications.rsc.infrastructure import (
    FutureSchemaError,
    InvalidProjectFileError,
    ProjectRepository,
)
from applications.rsc.use_cases import (
    CalculateScoreCommand,
    CreateActivityCommand,
    CreateEvidenceCommand,
    CreateProcessCommand,
    LoadProjectCommand,
    RegisterDocumentCommand,
    SaveProjectCommand,
    ValidateProcessCommand,
)


class EvidenceLookup:
    def exists(self, _evidence_id):
        return True


class ProjectPersistenceTests(unittest.TestCase):
    def setUp(self):
        self.temporary = TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.path = Path(self.temporary.name) / "project.pdop"
        self.application = RscApplication()
        self.session = self.application.create_project_session(EvidenceLookup())
        self.facade = RscApplicationFacade(self.session)

    def populate(self):
        process = self.facade.create_process(
            CreateProcessCommand("Pessoa", "Instituição", "123")
        )
        document = self.facade.register_document(
            RegisterDocumentCommand(
                process.process_id,
                "ato.pdf",
                original_path="Z:/ato.pdf",
                stored_path="docs/ato.pdf",
                mime_type="application/pdf",
                checksum="abc",
                description="Ato",
            )
        )
        activity = self.facade.create_activity(
            CreateActivityCommand(
                process.process_id,
                criterion_id(1, 2),
                "Comissão",
                "2.50",
                description="Descrição",
                start_date=date(2024, 1, 2),
                end_date=date(2024, 3, 4),
                notes="Nota",
            )
        )
        evidence = self.facade.create_evidence(
            CreateEvidenceCommand(
                process.process_id,
                activity.activity_id,
                (document.document_id,),
                "Portaria",
            )
        )
        updated_activity = replace(
            process.process.activities[0],
            status=ActivityStatus.COMPLETE,
            created_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
            updated_at=datetime(2024, 4, 1, tzinfo=timezone.utc),
        )
        self.session.rsc_activity_service.update_activity(
            process.process, updated_activity
        )
        old_document = document.document
        updated_document = replace(
            old_document,
            status=DocumentStatus.ARCHIVED,
            document_date=date(2023, 12, 1),
            created_at=datetime(2024, 1, 2, tzinfo=timezone.utc),
            metadata={"source": "manual", "pages": 2},
        )
        self.session.rsc_document_service.remove_document(old_document.id)
        self.session.rsc_document_service.add_document(updated_document)
        old_evidence = evidence.evidence
        updated_evidence = replace(
            old_evidence,
            status=EvidenceStatus.ACCEPTED,
            justification="Conferida",
            created_at=datetime(2024, 2, 1, tzinfo=timezone.utc),
            updated_at=datetime(2024, 4, 2, tzinfo=timezone.utc),
        )
        self.session.rsc_evidence_service.clear()
        self.session.rsc_evidence_service.create_evidence(
            id=updated_evidence.id,
            activity_id=updated_evidence.activity_id,
            document_ids=updated_evidence.document_ids,
            description=updated_evidence.description,
            status=updated_evidence.status,
            justification=updated_evidence.justification,
            created_at=updated_evidence.created_at,
            updated_at=updated_evidence.updated_at,
        )
        return process.process_id

    def state(self, session):
        return (
            session.rsc_process_service.list_processes(),
            session.rsc_document_service.list_documents(),
            session.rsc_evidence_service.list_all(),
        )

    def test_empty_project_save_and_load(self):
        saved = self.facade.save_project(SaveProjectCommand(self.path))
        self.assertEqual(saved.process_count, 0)
        with ZipFile(self.path) as archive:
            self.assertEqual(
                set(archive.namelist()),
                {
                    "project.json",
                    "process.json",
                    "documents.json",
                    "activities.json",
                    "evidence.json",
                    "metadata.json",
                },
            )

        restored = RscApplication().create_project_session(EvidenceLookup())
        result = RscApplicationFacade(restored).load_project(
            LoadProjectCommand(self.path)
        )
        self.assertEqual(result.process_count, 0)
        self.assertEqual(self.state(restored), ((), (), ()))

    def test_complete_round_trip_preserves_full_structural_state(self):
        process_id = self.populate()
        original = self.state(self.session)
        original_validation = self.facade.validate_process(
            ValidateProcessCommand(process_id)
        )
        original_score = self.facade.calculate_score(
            CalculateScoreCommand(process_id)
        )

        self.facade.save_project(SaveProjectCommand(self.path))
        restored = RscApplication().create_project_session(EvidenceLookup())
        restored_facade = RscApplicationFacade(restored)
        result = restored_facade.load_project(LoadProjectCommand(self.path))

        self.assertEqual(result.process_count, 1)
        self.assertEqual(result.activity_count, 1)
        self.assertEqual(result.document_count, 1)
        self.assertEqual(result.evidence_count, 1)
        self.assertEqual(self.state(restored), original)
        self.assertIsNot(self.state(restored)[0][0], original[0][0])
        self.assertIsInstance(
            restored.rsc_process_service.list_processes()[0].activities[0].quantity,
            Decimal,
        )
        validation = restored_facade.validate_process(
            ValidateProcessCommand(process_id)
        )
        score = restored_facade.calculate_score(
            CalculateScoreCommand(process_id)
        )
        self.assertEqual(validation.issues, original_validation.issues)
        self.assertEqual(score.total_score, original_score.total_score)
        self.assertEqual(
            score.requirement_scores, original_score.requirement_scores
        )
        self.assertEqual(
            tuple(item.id for item in restored.official_catalog.list_criteria()),
            tuple(item.id for item in self.session.official_catalog.list_criteria()),
        )

    def test_multiple_saves_preserve_created_at_and_update_saved_at(self):
        self.facade.save_project(SaveProjectCommand(self.path))
        with ZipFile(self.path) as archive:
            first = json.loads(archive.read("metadata.json"))
        self.facade.save_project(SaveProjectCommand(self.path))
        with ZipFile(self.path) as archive:
            second = json.loads(archive.read("metadata.json"))
        self.assertEqual(first["created_at"], second["created_at"])
        self.assertGreaterEqual(second["saved_at"], first["saved_at"])
        self.assertEqual(second["schema_version"], 1)
        self.assertEqual(second["application_version"], "1.5")

    def test_multiple_loads_replace_state_with_new_instances(self):
        self.populate()
        self.facade.save_project(SaveProjectCommand(self.path))
        self.facade.load_project(LoadProjectCommand(self.path))
        first = self.session.rsc_process_service.list_processes()[0]
        self.facade.load_project(LoadProjectCommand(self.path))
        second = self.session.rsc_process_service.list_processes()[0]
        self.assertEqual(first, second)
        self.assertIsNot(first, second)

    def test_invalid_missing_incompatible_and_nonexistent_projects(self):
        invalid = Path(self.temporary.name) / "invalid.pdop"
        invalid.write_text("not a zip", encoding="utf-8")
        with self.assertRaises(InvalidProjectFileError):
            self.facade.load_project(LoadProjectCommand(invalid))
        with self.assertRaises(FileNotFoundError):
            self.facade.load_project(
                LoadProjectCommand(Path(self.temporary.name) / "missing.pdop")
            )

        self.facade.save_project(SaveProjectCommand(self.path))
        self.rewrite_archive("documents.json", None)
        with self.assertRaises(InvalidProjectFileError):
            ProjectRepository().validate(self.path)

        self.facade.save_project(SaveProjectCommand(self.path))
        with ZipFile(self.path) as archive:
            metadata = json.loads(archive.read("metadata.json"))
        metadata["schema_version"] = 999
        self.rewrite_archive("metadata.json", metadata)
        with self.assertRaisesRegex(FutureSchemaError, "schema futuro"):
            ProjectRepository().load(self.path)

    def test_save_rejects_bad_extension_and_nonexistent_directory(self):
        with self.assertRaises(ValueError):
            self.facade.save_project(
                SaveProjectCommand(Path(self.temporary.name) / "project.json")
            )
        with self.assertRaises(FileNotFoundError):
            self.facade.save_project(
                SaveProjectCommand(
                    Path(self.temporary.name) / "absent" / "project.pdop"
                )
            )

    def rewrite_archive(self, target, replacement):
        with ZipFile(self.path) as source:
            values = {
                name: source.read(name)
                for name in source.namelist()
                if name != target
            }
        if replacement is not None:
            values[target] = json.dumps(replacement).encode()
        rewritten = self.path.with_suffix(".rewrite")
        with ZipFile(rewritten, "w", ZIP_DEFLATED) as destination:
            for name, value in values.items():
                destination.writestr(name, value)
        rewritten.replace(self.path)


if __name__ == "__main__":
    unittest.main()
