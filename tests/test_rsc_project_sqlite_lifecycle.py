from datetime import date
import json
from pathlib import Path
import sqlite3
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import Mock, patch

from applications import RscApplication
from applications.rsc.commands import (
    CreateFunctionalAssignmentEvidenceCommand,
    CreateFunctionalExerciseCommand,
)
from applications.rsc.repositories import (
    InMemoryFunctionalAssignmentEvidenceRepository,
    SQLiteFunctionalAssignmentEvidenceRepository,
    SQLiteFunctionalExerciseRepository,
)
from core.application_registry import ApplicationRegistry
from core.project_manager import ProjectManager
from core.project_session_factory import ProjectSessionFactory
from database import DatabaseError, ProjectDatabase, get_schema_version
from models import CreateEvidenceRequest
from services.indexing import DocumentIndexer


def factory(application=None):
    return ProjectSessionFactory(
        ApplicationRegistry([application or RscApplication()])
    )


def create_rsc_project(root, name):
    return ProjectManager().create_project(
        name,
        root,
        application_id="rsc",
    )


def create_host_evidence(session, project, marker):
    sha = marker * 64
    processing_file = project.project_path / f"processing-{marker}.json"
    processing_file.write_text(
        json.dumps(
            {
                "document_sha256": sha,
                "processed_at": "2026-01-10T10:00:00",
                "status": "processed",
                "page_count": 1,
                "pages": [{"page": 1, "text": "designação"}],
                "metadata": {"title": f"Portaria {marker}"},
            }
        ),
        encoding="utf-8",
    )
    DocumentIndexer(
        project.project_path / project.database
    ).index_processing_result(processing_file)
    return session.evidence_service.create(
        CreateEvidenceRequest(
            document_identity=sha,
            page_number=1,
            title=f"Designação {marker}",
        )
    )


def create_rsc_data(session, evidence, marker):
    assignment = (
        session.rsc_session
        .create_functional_assignment_evidence_service.execute(
            CreateFunctionalAssignmentEvidenceCommand(
                person_id=f"person-{marker}",
                source_evidence_reference=evidence.id,
                exercise_type_code="coordenacao",
                exercise_type_label="Coordenação",
                role=f"Coordenador {marker}",
                organization="Universidade",
                start_date=date(2024, 1, 1),
            )
        )
    )
    exercise = session.rsc_session.create_functional_exercise_service.execute(
        CreateFunctionalExerciseCommand(
            person_id=assignment.person_id,
            exercise_type_code=assignment.exercise_type_code,
            exercise_type_label=assignment.exercise_type_label,
            role=assignment.role,
            context_organization=assignment.organization,
            start_date=assignment.start_date,
            functional_assignment_evidence_ids=(assignment.id,),
        )
    )
    return assignment, exercise


class RscProjectSQLiteLifecycleTests(unittest.TestCase):
    def test_new_project_uses_sqlite_repositories_and_shared_instances(self):
        with TemporaryDirectory() as temporary_directory:
            project = create_rsc_project(
                Path(temporary_directory),
                "Novo",
            )

            session = factory().create(project)
            rsc = session.rsc_session

            self.assertIsInstance(
                rsc.functional_assignment_evidence_repository,
                SQLiteFunctionalAssignmentEvidenceRepository,
            )
            self.assertIsInstance(
                rsc.functional_exercise_repository,
                SQLiteFunctionalExerciseRepository,
            )
            self.assertIs(
                rsc.create_functional_assignment_evidence_service
                ._repository,
                rsc.functional_assignment_evidence_repository,
            )
            self.assertIs(
                rsc.create_functional_exercise_service._repository,
                rsc.functional_exercise_repository,
            )
            self.assertEqual(
                rsc.functional_exercise_repository.database_path,
                project.project_path / project.database,
            )

    def test_new_project_data_survives_real_reopening_flow(self):
        with TemporaryDirectory() as temporary_directory:
            manager = ProjectManager()
            project = manager.create_project(
                "Persistente",
                Path(temporary_directory),
                application_id="rsc",
            )
            session = factory().create(project)
            evidence = create_host_evidence(session, project, "a")
            assignment, exercise = create_rsc_data(
                session,
                evidence,
                "a",
            )

            session = None
            reopened_project = manager.open_project(project.project_path)
            reopened = factory().create(reopened_project)

            self.assertEqual(
                reopened.rsc_session
                .list_functional_assignment_evidences_service.execute(),
                (assignment,),
            )
            self.assertEqual(
                reopened.rsc_session
                .list_functional_exercises_service.execute(),
                (exercise,),
            )
            self.assertEqual(
                reopened.rsc_session
                .list_functional_exercises_service.execute()[0]
                .functional_assignment_evidence_ids,
                (assignment.id,),
            )
            with ProjectDatabase(
                reopened_project.project_path / reopened_project.database
            ) as database:
                self.assertEqual(get_schema_version(database.connection), 7)

    def test_existing_version_three_project_migrates_and_persists_rsc(self):
        with TemporaryDirectory() as temporary_directory:
            manager = ProjectManager()
            project = manager.create_project(
                "Existente",
                Path(temporary_directory),
                application_id="rsc",
            )
            database_path = project.project_path / project.database
            connection = sqlite3.connect(database_path)
            try:
                connection.execute(
                    "INSERT INTO index_state(key, value) VALUES (?, ?)",
                    ("preserved-host-data", "intacto"),
                )
                connection.execute(
                    "DROP INDEX idx_rsc_activity_functional_exercise"
                )
                connection.execute(
                    "DROP TABLE rsc_activity_functional_exercises"
                )
                connection.execute(
                    "DROP INDEX idx_rsc_activity_assignment_evidence"
                )
                connection.execute(
                    "DROP TABLE "
                    "rsc_activity_functional_assignment_evidences"
                )
                connection.execute("DROP TABLE rsc_activities")
                connection.execute(
                    "DROP INDEX idx_rsc_exercise_assignment_evidence"
                )
                connection.execute(
                    "DROP TABLE "
                    "rsc_functional_exercise_assignment_evidences"
                )
                connection.execute("DROP TABLE rsc_functional_exercises")
                connection.execute(
                    "DROP INDEX idx_rsc_assignment_evidences_source"
                )
                connection.execute(
                    "DROP TABLE rsc_functional_assignment_evidences"
                )
                connection.execute(
                    "UPDATE index_state SET value = '3' "
                    "WHERE key = 'schema_version'"
                )
                connection.execute("PRAGMA user_version = 3")
                connection.commit()
            finally:
                connection.close()

            reopened_project = manager.open_project(project.project_path)
            session = factory().create(reopened_project)
            evidence = create_host_evidence(
                session,
                reopened_project,
                "b",
            )
            assignment, exercise = create_rsc_data(
                session,
                evidence,
                "b",
            )
            reopened = factory().create(
                manager.open_project(project.project_path)
            )

            self.assertEqual(
                reopened.rsc_session
                .list_functional_assignment_evidences_service.execute(),
                (assignment,),
            )
            self.assertEqual(
                reopened.rsc_session
                .list_functional_exercises_service.execute(),
                (exercise,),
            )
            with ProjectDatabase(database_path) as database:
                preserved = database.connection.execute(
                    "SELECT value FROM index_state WHERE key = ?",
                    ("preserved-host-data",),
                ).fetchone()["value"]
            self.assertEqual(preserved, "intacto")

    def test_two_projects_remain_isolated_after_reopening(self):
        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            manager = ProjectManager()
            first_project = manager.create_project(
                "ProjetoA",
                root,
                application_id="rsc",
            )
            second_project = manager.create_project(
                "ProjetoB",
                root,
                application_id="rsc",
            )
            first_session = factory().create(first_project)
            second_session = factory().create(second_project)
            first_data = create_rsc_data(
                first_session,
                create_host_evidence(
                    first_session,
                    first_project,
                    "c",
                ),
                "a",
            )
            second_data = create_rsc_data(
                second_session,
                create_host_evidence(
                    second_session,
                    second_project,
                    "d",
                ),
                "b",
            )

            first_reopened = factory().create(
                manager.open_project(first_project.project_path)
            )
            second_reopened = factory().create(
                manager.open_project(second_project.project_path)
            )

            self.assertEqual(
                first_reopened.rsc_session
                .list_functional_assignment_evidences_service.execute(),
                (first_data[0],),
            )
            self.assertEqual(
                first_reopened.rsc_session
                .list_functional_exercises_service.execute(),
                (first_data[1],),
            )
            self.assertEqual(
                second_reopened.rsc_session
                .list_functional_assignment_evidences_service.execute(),
                (second_data[0],),
            )
            self.assertEqual(
                second_reopened.rsc_session
                .list_functional_exercises_service.execute(),
                (second_data[1],),
            )
            self.assertIsNot(
                first_reopened.rsc_session.functional_exercise_repository,
                second_reopened.rsc_session.functional_exercise_repository,
            )

    def test_sqlite_failure_propagates_without_memory_fallback(self):
        with TemporaryDirectory() as temporary_directory:
            project = create_rsc_project(
                Path(temporary_directory),
                "Falha",
            )
            memory_factory = Mock(
                return_value=InMemoryFunctionalAssignmentEvidenceRepository()
            )
            application = RscApplication(memory_factory)
            expected = DatabaseError("falha controlada")

            with patch(
                "applications.rsc.application."
                "create_sqlite_rsc_repositories",
                side_effect=expected,
            ):
                with self.assertRaisesRegex(
                    DatabaseError,
                    "falha controlada",
                ):
                    factory(application).create(project)

            memory_factory.assert_not_called()

    def test_repositories_hold_no_open_connection_resource(self):
        with TemporaryDirectory() as temporary_directory:
            project = create_rsc_project(
                Path(temporary_directory),
                "SemConexaoPermanente",
            )
            rsc = factory().create(project).rsc_session

            for repository in (
                rsc.functional_assignment_evidence_repository,
                rsc.functional_exercise_repository,
            ):
                self.assertFalse(hasattr(repository, "connection"))
                self.assertFalse(hasattr(repository, "_connection"))


if __name__ == "__main__":
    unittest.main()
