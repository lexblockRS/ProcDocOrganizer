import ast
from pathlib import Path
import unittest

from applications.rsc import RscApplication, RscProjectSession
from applications.rsc.composition import (
    RscRepositories,
    create_in_memory_rsc_repositories,
    create_rsc_project_session,
)
from applications.rsc.ports import (
    ActivityRepository,
    FunctionalAssignmentEvidenceRepository,
    FunctionalExerciseRepository,
    ProjectRepository,
)
from applications.rsc.repositories import (
    InMemoryActivityRepository,
    InMemoryFunctionalAssignmentEvidenceRepository,
    InMemoryFunctionalExerciseRepository,
    InMemoryProjectRepository,
)


class EvidenceLookupStub:
    def exists(self, _evidence_id):
        return True


class AssignmentRepositoryDouble(
    InMemoryFunctionalAssignmentEvidenceRepository
):
    pass


class ExerciseRepositoryDouble(InMemoryFunctionalExerciseRepository):
    pass


def alternative_repositories():
    return RscRepositories(
        activity=InMemoryActivityRepository(),
        project=InMemoryProjectRepository(),
        functional_assignment_evidence=AssignmentRepositoryDouble(),
        functional_exercise=ExerciseRepositoryDouble(),
    )


class RscCompositionBoundaryTests(unittest.TestCase):
    def test_session_repository_annotations_use_ports(self):
        annotations = RscProjectSession.__annotations__

        self.assertIs(
            annotations["activity_repository"],
            ActivityRepository,
        )
        self.assertIs(
            annotations["project_repository"],
            ProjectRepository,
        )
        self.assertIs(
            annotations["functional_assignment_evidence_repository"],
            FunctionalAssignmentEvidenceRepository,
        )
        self.assertIs(
            annotations["functional_exercise_repository"],
            FunctionalExerciseRepository,
        )

    def test_session_module_does_not_import_in_memory_repositories(self):
        path = (
            Path(__file__).parents[1]
            / "applications"
            / "rsc"
            / "project_session.py"
        )
        source = path.read_text(encoding="utf-8")

        self.assertNotIn("InMemory", source)
        self.assertNotIn("applications.rsc.repositories", source)

    def test_default_repository_factory_creates_in_memory_adapters(self):
        repositories = create_in_memory_rsc_repositories()

        self.assertIsInstance(
            repositories.functional_assignment_evidence,
            InMemoryFunctionalAssignmentEvidenceRepository,
        )
        self.assertIsInstance(
            repositories.functional_exercise,
            InMemoryFunctionalExerciseRepository,
        )

    def test_repositories_can_be_injected_into_composition(self):
        repositories = alternative_repositories()

        session = create_rsc_project_session(
            EvidenceLookupStub(),
            repositories,
        )

        self.assertIs(
            session.functional_assignment_evidence_repository,
            repositories.functional_assignment_evidence,
        )
        self.assertIs(
            session.functional_exercise_repository,
            repositories.functional_exercise,
        )

    def test_services_share_injected_repository_instances(self):
        repositories = alternative_repositories()
        session = create_rsc_project_session(
            EvidenceLookupStub(),
            repositories,
        )

        self.assertIs(
            session.create_functional_assignment_evidence_service
            ._repository,
            repositories.functional_assignment_evidence,
        )
        self.assertIs(
            session.list_functional_assignment_evidences_service
            ._repository,
            repositories.functional_assignment_evidence,
        )
        self.assertIs(
            session.create_functional_exercise_service
            ._assignment_evidence_repository,
            repositories.functional_assignment_evidence,
        )
        self.assertIs(
            session.create_functional_exercise_service._repository,
            repositories.functional_exercise,
        )
        self.assertIs(
            session.list_functional_exercises_service._repository,
            repositories.functional_exercise,
        )

    def test_application_accepts_alternative_repository_factory(self):
        created = []

        def repository_factory():
            repositories = alternative_repositories()
            created.append(repositories)
            return repositories

        application = RscApplication(repository_factory)

        first = application.create_project_session(EvidenceLookupStub())
        second = application.create_project_session(EvidenceLookupStub())

        self.assertIs(
            first.functional_exercise_repository,
            created[0].functional_exercise,
        )
        self.assertIs(
            second.functional_exercise_repository,
            created[1].functional_exercise,
        )
        self.assertIsNot(
            first.functional_exercise_repository,
            second.functional_exercise_repository,
        )

    def test_default_public_application_composition_is_compatible(self):
        session = RscApplication().create_project_session(
            EvidenceLookupStub()
        )

        self.assertIsInstance(session, RscProjectSession)
        self.assertIsInstance(
            session.functional_assignment_evidence_repository,
            InMemoryFunctionalAssignmentEvidenceRepository,
        )
        self.assertIsInstance(
            session.functional_exercise_repository,
            InMemoryFunctionalExerciseRepository,
        )

    def test_rsc_layers_do_not_import_concrete_repositories(self):
        root = Path(__file__).parents[1] / "applications" / "rsc"
        inspected_directories = (
            "models",
            "commands",
            "dto",
            "assemblers",
            "services",
        )

        for directory in inspected_directories:
            for path in (root / directory).glob("*.py"):
                with self.subTest(path=path):
                    source = path.read_text(encoding="utf-8")
                    self.assertNotIn(
                        "applications.rsc.repositories",
                        source,
                    )
                    self.assertNotIn("InMemory", source)

    def test_rsc_has_no_forbidden_runtime_imports(self):
        root = Path(__file__).parents[1] / "applications" / "rsc"

        for path in root.rglob("*.py"):
            with self.subTest(path=path):
                tree = ast.parse(path.read_text(encoding="utf-8"))
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
                    any("pyside6" in imported.lower() for imported in imports)
                )
                if not (
                    path.parent.name == "repositories"
                    and path.name.startswith("sqlite_")
                ):
                    self.assertFalse(
                        any(
                            "sqlite3" in imported.lower()
                            for imported in imports
                        )
                    )


if __name__ == "__main__":
    unittest.main()
