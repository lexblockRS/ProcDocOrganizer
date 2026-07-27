import ast
from datetime import date
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from applications import RscApplication
from applications.rsc import RscProjectSession
from applications.rsc.commands import (
    CreateActivityCommand,
    CreateFunctionalAssignmentEvidenceCommand,
    CreateFunctionalExerciseCommand,
    CreateProjectCommand,
)
from applications.rsc.repositories import (
    InMemoryProjectRepository,
    SQLiteActivityRepository,
    SQLiteFunctionalAssignmentEvidenceRepository,
    SQLiteFunctionalExerciseRepository,
)
from applications.rsc.services import (
    CreateActivityService,
    CreateFunctionalExerciseService,
    CreateProjectService,
    ListFunctionalExercisesService,
)
from core.application_registry import ApplicationRegistry
from core.project_manager import ProjectManager
from core.project_session_factory import ProjectSessionFactory


def create_project(parent: Path, name: str, application_id: str):
    return ProjectManager().create_project(
        name,
        parent,
        application_id=application_id,
    )


def create_factory():
    return ProjectSessionFactory(
        ApplicationRegistry([RscApplication()])
    )


class RscProjectSessionCompositionTests(unittest.TestCase):
    def test_rsc_project_receives_rsc_session(self):
        with TemporaryDirectory() as temporary_directory:
            project = create_project(
                Path(temporary_directory),
                "RSC",
                "rsc",
            )

            session = create_factory().create(project)

            self.assertIsInstance(session.rsc_session, RscProjectSession)

    def test_session_exposes_usable_repositories_and_services(self):
        with TemporaryDirectory() as temporary_directory:
            project = create_project(
                Path(temporary_directory),
                "RSC",
                "rsc",
            )
            rsc = create_factory().create(project).rsc_session

            self.assertIsInstance(
                rsc.activity_repository,
                SQLiteActivityRepository,
            )
            self.assertIsInstance(
                rsc.project_repository,
                InMemoryProjectRepository,
            )
            self.assertIsInstance(
                rsc.functional_exercise_repository,
                SQLiteFunctionalExerciseRepository,
            )
            self.assertIsInstance(
                rsc.functional_assignment_evidence_repository,
                SQLiteFunctionalAssignmentEvidenceRepository,
            )
            self.assertIsInstance(
                rsc.create_activity_service,
                CreateActivityService,
            )
            self.assertIsInstance(
                rsc.create_project_service,
                CreateProjectService,
            )
            self.assertIsInstance(
                rsc.create_functional_exercise_service,
                CreateFunctionalExerciseService,
            )
            self.assertIsInstance(
                rsc.list_functional_exercises_service,
                ListFunctionalExercisesService,
            )

            activity = rsc.create_activity_service.execute(
                CreateActivityCommand(description="Comissão")
            )
            rsc_project = rsc.create_project_service.execute(
                CreateProjectCommand(title="Projeto RSC")
            )
            assignment = (
                rsc.functional_assignment_normalizer.normalize(
                    rsc.functional_assignment_evidence_assembler.assemble(
                        CreateFunctionalAssignmentEvidenceCommand(
                            person_id="person-1",
                            source_evidence_reference="source-1",
                            exercise_type_code="comissao",
                            exercise_type_label="Participação em comissão",
                            role="Membro",
                            organization="Instituição",
                            start_date=date(2024, 1, 1),
                        )
                    )
                )
            )
            rsc.functional_assignment_evidence_repository.save(assignment)
            exercise = rsc.create_functional_exercise_service.execute(
                CreateFunctionalExerciseCommand(
                    person_id="person-1",
                    exercise_type_code="comissao",
                    exercise_type_label="Participação em comissão",
                    role="Membro",
                    context_organization="Instituição",
                    start_date=date(2024, 1, 1),
                    functional_assignment_evidence_ids=(
                        str(assignment.id),
                    ),
                )
            )

            self.assertIsNotNone(
                rsc.activity_repository.get(activity.activity_id)
            )
            self.assertIsNotNone(
                rsc.project_repository.get(rsc_project.project_id)
            )
            self.assertEqual(
                rsc.list_functional_exercises_service.execute(),
                (exercise,),
            )

    def test_services_share_session_repositories(self):
        with TemporaryDirectory() as temporary_directory:
            project = create_project(
                Path(temporary_directory),
                "RSC",
                "rsc",
            )
            rsc = create_factory().create(project).rsc_session

            self.assertIs(
                rsc.create_activity_service._repository,
                rsc.activity_repository,
            )
            self.assertIs(
                rsc.create_project_service._repository,
                rsc.project_repository,
            )
            self.assertIs(
                rsc.create_functional_exercise_service._repository,
                rsc.functional_exercise_repository,
            )
            self.assertIs(
                rsc.list_functional_exercises_service._repository,
                rsc.functional_exercise_repository,
            )
            self.assertIs(
                rsc.create_functional_exercise_service._assembler,
                rsc.manual_functional_exercise_assembler,
            )

    def test_non_rsc_project_does_not_receive_rsc_session(self):
        with TemporaryDirectory() as temporary_directory:
            project = create_project(
                Path(temporary_directory),
                "Legacy",
                "ProcDocOrganizer",
            )

            session = create_factory().create(project)

            self.assertIsNone(session.application)
            self.assertIsNone(session.rsc_session)

    def test_distinct_project_sessions_do_not_share_rsc_state(self):
        with TemporaryDirectory() as temporary_directory:
            parent = Path(temporary_directory)
            factory = create_factory()
            first = factory.create(
                create_project(parent, "Primeiro", "rsc")
            )
            second = factory.create(
                create_project(parent, "Segundo", "rsc")
            )

            first.rsc_session.create_activity_service.execute(
                CreateActivityCommand(description="Primeira")
            )

            self.assertIsNot(first.rsc_session, second.rsc_session)
            self.assertIsNot(
                first.rsc_session.activity_repository,
                second.rsc_session.activity_repository,
            )
            self.assertIsNot(
                first.rsc_session.project_repository,
                second.rsc_session.project_repository,
            )
            self.assertIsNot(
                first.rsc_session.functional_exercise_repository,
                second.rsc_session.functional_exercise_repository,
            )
            self.assertEqual(
                len(first.rsc_session.activity_repository.list_all()),
                1,
            )
            self.assertEqual(
                second.rsc_session.activity_repository.list_all(),
                (),
            )

    def test_rsc_composition_requires_no_pyside_or_sqlite(self):
        root = Path(__file__).parents[1]
        for relative_path in (
            "applications/rsc/project_session.py",
            "applications/rsc/application.py",
            "core/project_session.py",
            "core/project_session_factory.py",
        ):
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
                        for forbidden in ("pyside", "sqlite", "database")
                    )
                )


if __name__ == "__main__":
    unittest.main()
