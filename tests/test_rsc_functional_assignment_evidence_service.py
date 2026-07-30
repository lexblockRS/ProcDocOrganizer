import ast
from dataclasses import FrozenInstanceError, fields
from datetime import date
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from applications import RscApplication
from applications.rsc.assemblers import (
    FunctionalAssignmentEvidenceAssembler,
)
from applications.rsc.commands import (
    CreateFunctionalAssignmentEvidenceCommand,
    CreateFunctionalExerciseCommand,
)
from applications.rsc.dto import FunctionalAssignmentEvidenceDTO
from applications.rsc.models import (
    FunctionalAssignmentEvidenceId,
    FunctionalAssignmentEvidenceStatus,
)
from applications.rsc.repositories import (
    DuplicateFunctionalAssignmentEvidenceError,
    InMemoryFunctionalAssignmentEvidenceRepository,
)
from applications.rsc.services import (
    CreateFunctionalAssignmentEvidenceService,
    FunctionalAssignmentNormalizer,
    ListFunctionalAssignmentEvidencesService,
    SourceEvidenceNotFoundError,
)
from core.application_registry import ApplicationRegistry
from core.project_manager import ProjectManager
from core.project_session_factory import ProjectSessionFactory
from models import CreateEvidenceRequest
from services.indexing import DocumentIndexer


EVIDENCE_ID = "11111111-1111-4111-8111-111111111111"
SHA = "a" * 64


def command(
    source_evidence_reference=EVIDENCE_ID,
    role="  Coordenador   Acadêmico  ",
):
    return CreateFunctionalAssignmentEvidenceCommand(
        person_id="person-1",
        source_evidence_reference=source_evidence_reference,
        exercise_type_code="coordenacao",
        exercise_type_label="  Coordenação   Acadêmica ",
        role=role,
        organization="  Instituto   Federal ",
        start_date=date(2024, 1, 1),
        end_date=None,
        unit="  Campus   Centro ",
        administrative_reference="  Portaria   10/2024 ",
    )


class EvidenceLookup:
    def __init__(self, existing=()):
        self.existing = set(existing)
        self.calls = []

    def exists(self, evidence_id):
        self.calls.append(evidence_id)
        return evidence_id in self.existing


class AssemblerSpy:
    def __init__(self):
        self.delegate = FunctionalAssignmentEvidenceAssembler()
        self.commands = []

    def assemble(self, received):
        self.commands.append(received)
        return self.delegate.assemble(received)


class NormalizerSpy:
    def __init__(self):
        self.delegate = FunctionalAssignmentNormalizer()
        self.inputs = []

    def normalize(self, evidence):
        self.inputs.append(evidence)
        return self.delegate.normalize(evidence)


def service(existing=(EVIDENCE_ID,)):
    lookup = EvidenceLookup(existing)
    repository = InMemoryFunctionalAssignmentEvidenceRepository()
    assembler = AssemblerSpy()
    normalizer = NormalizerSpy()
    created = CreateFunctionalAssignmentEvidenceService(
        lookup,
        repository,
        assembler,
        normalizer,
    )
    return created, lookup, repository, assembler, normalizer


class CreateFunctionalAssignmentEvidenceServiceTests(unittest.TestCase):
    def test_creates_raw_stores_and_returns_dto_without_automation(self):
        created, lookup, repository, assembler, normalizer = service()
        request = command()

        result = created.execute(request)

        self.assertIsInstance(result, FunctionalAssignmentEvidenceDTO)
        self.assertEqual(result.status, "raw")
        self.assertEqual(result.role, "Coordenador Acadêmico")
        self.assertEqual(result.organization, "Instituto Federal")
        self.assertEqual(result.unit, "Campus Centro")
        self.assertEqual(
            result.administrative_reference,
            "Portaria 10/2024",
        )
        self.assertEqual(lookup.calls, [EVIDENCE_ID])
        self.assertEqual(assembler.commands, [request])
        self.assertEqual(normalizer.inputs, [])

        stored = repository.list_all()[0]
        self.assertEqual(str(stored.id), result.id)
        self.assertIs(
            stored.status,
            FunctionalAssignmentEvidenceStatus.RAW,
        )

    def test_missing_source_fails_before_assembly_and_storage(self):
        created, lookup, repository, assembler, normalizer = service(())

        with self.assertRaises(SourceEvidenceNotFoundError):
            created.execute(command())

        self.assertEqual(lookup.calls, [EVIDENCE_ID])
        self.assertEqual(assembler.commands, [])
        self.assertEqual(normalizer.inputs, [])
        self.assertEqual(repository.list_all(), ())

    def test_preserves_source_reference_without_copying_evidence(self):
        created, _, repository, _, _ = service()

        result = created.execute(command())
        stored = repository.list_all()[0]

        self.assertEqual(result.source_evidence_reference, EVIDENCE_ID)
        self.assertEqual(
            str(stored.source_evidence_reference),
            EVIDENCE_ID,
        )
        self.assertFalse(hasattr(stored, "source_evidence"))
        self.assertFalse(hasattr(stored, "evidence"))

    def test_returned_dto_is_immutable_and_contains_no_domain_objects(self):
        result = service()[0].execute(command())

        with self.assertRaises(FrozenInstanceError):
            result.role = "Outro"
        for field in fields(result):
            value = getattr(result, field.name)
            self.assertNotEqual(
                value.__class__.__module__,
                "applications.rsc.models.functional_assignment_evidence",
            )

    def test_rejects_invalid_command_before_lookup(self):
        created, lookup, _, _, _ = service()

        with self.assertRaises(TypeError):
            created.execute(object())

        self.assertEqual(lookup.calls, [])


class FunctionalAssignmentEvidenceRepositoryTests(unittest.TestCase):
    def test_lists_in_insertion_order_and_gets_by_id(self):
        created, _, repository, _, _ = service()
        first = created.execute(command(role="Primeiro"))
        second = created.execute(command(role="Segundo"))

        items = repository.list_all()

        self.assertEqual(
            tuple(item.role for item in items),
            ("Primeiro", "Segundo"),
        )
        self.assertIs(repository.get_by_id(items[0].id), items[0])
        self.assertEqual(
            tuple(str(item.id) for item in items),
            (first.id, second.id),
        )

    def test_duplicate_id_is_rejected_explicitly(self):
        created, _, repository, _, _ = service()
        created.execute(command())
        existing = repository.list_all()[0]

        with self.assertRaises(
            DuplicateFunctionalAssignmentEvidenceError
        ):
            repository.save(existing)

        self.assertEqual(repository.list_all(), (existing,))

    def test_list_service_returns_dtos_in_repository_order(self):
        created, _, repository, _, _ = service()
        first = created.execute(command(role="Primeiro"))
        second = created.execute(command(role="Segundo"))

        listed = ListFunctionalAssignmentEvidencesService(
            repository
        ).execute()

        self.assertEqual(listed, (first, second))
        self.assertIsInstance(listed, tuple)


class RscFunctionalAssignmentSessionTests(unittest.TestCase):
    def test_create_and_list_services_share_repository(self):
        with TemporaryDirectory() as temporary_directory:
            project = ProjectManager().create_project(
                "RSC",
                Path(temporary_directory),
                application_id="rsc",
            )
            session = ProjectSessionFactory(
                ApplicationRegistry([RscApplication()])
            ).create(project)
            rsc = session.rsc_session

            self.assertIs(
                rsc.create_functional_assignment_evidence_service._repository,
                rsc.functional_assignment_evidence_repository,
            )
            self.assertIs(
                rsc.list_functional_assignment_evidences_service._repository,
                rsc.functional_assignment_evidence_repository,
            )
            self.assertIs(
                rsc.create_functional_assignment_evidence_service._assembler,
                rsc.functional_assignment_evidence_assembler,
            )
            self.assertIs(
                rsc.create_functional_assignment_evidence_service._normalizer,
                rsc.functional_assignment_normalizer,
            )

    def test_two_sessions_do_not_share_assignments(self):
        with TemporaryDirectory() as temporary_directory:
            parent = Path(temporary_directory)
            factory = ProjectSessionFactory(
                ApplicationRegistry([RscApplication()])
            )
            first = factory.create(
                ProjectManager().create_project(
                    "First",
                    parent,
                    application_id="rsc",
                )
            )
            second = factory.create(
                ProjectManager().create_project(
                    "Second",
                    parent,
                    application_id="rsc",
                )
            )
            first.rsc_session.functional_assignment_evidence_repository.save(
                FunctionalAssignmentNormalizer().normalize(
                    FunctionalAssignmentEvidenceAssembler().assemble(
                        command()
                    )
                )
            )

            self.assertEqual(
                len(
                    first.rsc_session
                    .functional_assignment_evidence_repository
                    .list_all()
                ),
                1,
            )
            self.assertEqual(
                second.rsc_session
                .functional_assignment_evidence_repository
                .list_all(),
                (),
            )

    def test_vertical_flow_uses_existing_host_evidence(self):
        with TemporaryDirectory() as temporary_directory:
            project = ProjectManager().create_project(
                "RSC",
                Path(temporary_directory),
                application_id="rsc",
            )
            session = ProjectSessionFactory(
                ApplicationRegistry([RscApplication()])
            ).create(project)
            processing_file = (
                Path(temporary_directory) / "processing-result.json"
            )
            processing_file.write_text(
                json.dumps(
                    {
                        "document_sha256": SHA,
                        "processed_at": "2026-01-10T10:00:00",
                        "status": "processed",
                        "page_count": 1,
                        "pages": [{"page": 1, "text": "designação"}],
                        "metadata": {"title": "Portaria"},
                    }
                ),
                encoding="utf-8",
            )
            DocumentIndexer(
                project.project_path / project.database
            ).index_processing_result(processing_file)
            evidence = session.evidence_service.create(
                CreateEvidenceRequest(
                    document_identity=SHA,
                    page_number=1,
                    title="Designação",
                )
            )

            created = (
                session.rsc_session
                .create_functional_assignment_evidence_service
                .execute(command(evidence.id))
            )
            repository = (
                session.rsc_session
                .functional_assignment_evidence_repository
            )
            assignment = repository.get_by_id(
                FunctionalAssignmentEvidenceId.from_string(created.id)
            )
            repository.update(
                assignment.mark_identified().mark_linked()
            )
            exercise = (
                session.rsc_session.create_functional_exercise_service.execute(
                    CreateFunctionalExerciseCommand(
                        person_id=created.person_id,
                        exercise_type_code=created.exercise_type_code,
                        exercise_type_label=created.exercise_type_label,
                        role=created.role,
                        context_organization=created.organization,
                        start_date=created.start_date,
                        end_date=created.end_date,
                        context_unit=created.unit,
                        context_reference=(
                            created.administrative_reference
                        ),
                        functional_assignment_evidence_ids=(created.id,),
                    )
                )
            )
            listed = (
                session.rsc_session
                .list_functional_assignment_evidences_service
                .execute()
            )
            listed_exercises = (
                session.rsc_session.list_functional_exercises_service.execute()
            )

            self.assertEqual(listed[0].id, created.id)
            self.assertEqual(listed[0].status, "linked")
            self.assertEqual(listed_exercises, (exercise,))
            self.assertEqual(
                exercise.functional_assignment_evidence_ids,
                (created.id,),
            )
            self.assertEqual(
                created.source_evidence_reference,
                evidence.id,
            )
            stored = (
                session.rsc_session
                .functional_assignment_evidence_repository
                .list_all()[0]
            )
            self.assertFalse(hasattr(stored, "evidence"))
            stored_exercise = (
                session.rsc_session.functional_exercise_repository
                .list_all()[0]
            )
            self.assertFalse(hasattr(stored_exercise, "evidence"))
            self.assertFalse(
                hasattr(
                    stored_exercise,
                    "functional_assignment_evidences",
                )
            )

    def test_rsc_flow_has_no_pyside_or_direct_sqlite_import(self):
        root = Path(__file__).parents[1]
        relative_paths = (
            "applications/rsc/project_session.py",
            "applications/rsc/dto/functional_assignment_evidence.py",
            "applications/rsc/ports/source_evidence_lookup.py",
            "applications/rsc/ports/"
            "functional_assignment_evidence_repository.py",
            "applications/rsc/repositories/"
            "in_memory_functional_assignment_evidence_repository.py",
            "applications/rsc/services/"
            "create_functional_assignment_evidence_service.py",
            "applications/rsc/services/"
            "list_functional_assignment_evidences_service.py",
        )
        for relative_path in relative_paths:
            with self.subTest(path=relative_path):
                tree = ast.parse(
                    (root / relative_path).read_text(encoding="utf-8")
                )
                imports = {
                    alias.name
                    for node in ast.walk(tree)
                    if isinstance(node, ast.Import)
                    for alias in node.names
                }
                imports.update(
                    node.module or ""
                    for node in ast.walk(tree)
                    if isinstance(node, ast.ImportFrom)
                )
                self.assertFalse(
                    any(
                        forbidden in imported.lower()
                        for imported in imports
                        for forbidden in (
                            "pyside",
                            "sqlite",
                            "database",
                        )
                    )
                )

    def test_rsc_module_does_not_define_duplicate_evidence_entity(self):
        root = Path(__file__).parents[1] / "applications" / "rsc"
        for path in root.rglob("*.py"):
            with self.subTest(path=path):
                tree = ast.parse(path.read_text(encoding="utf-8"))
                classes = {
                    node.name
                    for node in ast.walk(tree)
                    if isinstance(node, ast.ClassDef)
                }
                self.assertNotIn("Evidence", classes)


if __name__ == "__main__":
    unittest.main()
