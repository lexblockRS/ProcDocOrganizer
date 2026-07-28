import unittest

from applications.rsc import RscApplication
from applications.rsc.use_cases import (
    CalculateScoreUseCase,
    CreateProcessUseCase,
    CreateActivityUseCase,
    CreateEvidenceUseCase,
    GetActivityUseCase,
    GetDocumentUseCase,
    GetProcessUseCase,
    GetEvidenceUseCase,
    GenerateSummaryUseCase,
    ListActivitiesByCriterionUseCase,
    ListActivitiesByRequirementUseCase,
    ListActivitiesUseCase,
    ListDocumentsUseCase,
    ListProcessesUseCase,
    ListEvidenceByActivityUseCase,
    ListEvidenceUseCase,
    RegisterDocumentUseCase,
    RemoveDocumentUseCase,
    RscUseCaseRegistry,
    SessionDisposedError,
    ValidateProcessUseCase,
)


class EvidenceLookup:
    def exists(self, _evidence_id):
        return True


class UseCaseSessionTests(unittest.TestCase):
    def test_each_session_receives_one_populated_independent_registry(self):
        application = RscApplication()

        first = application.create_project_session(EvidenceLookup())
        second = application.create_project_session(EvidenceLookup())

        self.assertIsInstance(first.use_cases, RscUseCaseRegistry)
        expected = (
            CreateProcessUseCase,
            RegisterDocumentUseCase,
            GetProcessUseCase,
            ListProcessesUseCase,
            GetDocumentUseCase,
            ListDocumentsUseCase,
            RemoveDocumentUseCase,
            CreateActivityUseCase,
            GetActivityUseCase,
            ListActivitiesUseCase,
            ListActivitiesByCriterionUseCase,
            ListActivitiesByRequirementUseCase,
            CreateEvidenceUseCase,
            GetEvidenceUseCase,
            ListEvidenceUseCase,
            ListEvidenceByActivityUseCase,
            ValidateProcessUseCase,
            CalculateScoreUseCase,
            GenerateSummaryUseCase,
        )
        self.assertEqual(len(first.use_cases), len(expected))
        for use_case_type in expected:
            with self.subTest(use_case_type=use_case_type.__name__):
                self.assertIsInstance(
                    first.use_cases.get(use_case_type), use_case_type
                )
        self.assertIsNot(first.use_cases, second.use_cases)

    def test_session_disposal_disposes_registry(self):
        session = RscApplication().create_project_session(EvidenceLookup())

        session.dispose()

        self.assertTrue(session.use_cases.is_disposed)
        with self.assertRaises(SessionDisposedError):
            tuple(session.use_cases)


if __name__ == "__main__":
    unittest.main()
