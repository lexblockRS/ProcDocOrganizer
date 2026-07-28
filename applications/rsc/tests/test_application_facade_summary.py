import ast
from dataclasses import FrozenInstanceError, replace
from decimal import Decimal
from pathlib import Path
import unittest

from applications.rsc import RscApplication, RscApplicationFacade
from applications.rsc.domain import ActivityStatus, criterion_id
from applications.rsc.use_cases import (
    CalculateScoreCommand,
    CalculateScoreUseCase,
    CreateActivityCommand,
    CreateEvidenceCommand,
    CreateProcessCommand,
    GenerateSummaryCommand,
    GenerateSummaryUseCase,
    RegisterDocumentCommand,
    SessionDisposedError,
    ValidateProcessCommand,
    ValidateProcessUseCase,
)


class EvidenceLookup:
    def exists(self, _evidence_id):
        return True


class ApplicationFacadeSummaryTests(unittest.TestCase):
    def setUp(self):
        self.application = RscApplication()
        self.session = self.application.create_project_session(
            EvidenceLookup()
        )
        self.facade = RscApplicationFacade(self.session)

    def create_process(self):
        return self.facade.create_process(
            CreateProcessCommand("Pessoa", "Instituição")
        )

    def test_facade_executes_complete_flow_using_one_session(self):
        process = self.create_process()
        document = self.facade.register_document(
            RegisterDocumentCommand(process.process_id, "ato.pdf")
        )
        activity = self.facade.create_activity(
            CreateActivityCommand(
                process.process_id,
                criterion_id(1, 2),
                "Comissão",
                "2",
            )
        )
        evidence = self.facade.create_evidence(
            CreateEvidenceCommand(
                process.process_id,
                activity.activity_id,
                (document.document_id,),
                "Ato",
            )
        )
        validation = self.facade.validate_process(
            ValidateProcessCommand(process.process_id)
        )
        score = self.facade.calculate_score(
            CalculateScoreCommand(process.process_id)
        )
        summary = self.facade.generate_summary(
            GenerateSummaryCommand(process.process_id)
        ).summary

        self.assertEqual(evidence.activity_id, activity.activity_id)
        self.assertTrue(validation.is_valid)
        self.assertEqual(score.total_score, Decimal("9.0"))
        self.assertEqual(summary.process_id, process.process_id)
        self.assertEqual(summary.total_documents, 1)
        self.assertEqual(summary.total_activities, 1)
        self.assertEqual(summary.total_evidence, 1)
        self.assertEqual(summary.total_requirements, 6)
        self.assertEqual(summary.total_validation_errors, 0)
        self.assertEqual(summary.total_validation_warnings, 0)
        self.assertEqual(summary.total_score, Decimal("9.0"))
        self.assertEqual(summary.completion_percentage, Decimal("100"))

    def test_empty_process_summary_is_immutable_and_zeroed(self):
        process = self.create_process()

        summary = self.facade.generate_summary(
            GenerateSummaryCommand(process.process_id)
        ).summary

        self.assertEqual(summary.created_at, process.created_at)
        self.assertEqual(summary.total_documents, 0)
        self.assertEqual(summary.total_activities, 0)
        self.assertEqual(summary.total_evidence, 0)
        self.assertEqual(summary.total_requirements, 6)
        self.assertEqual(summary.total_score, Decimal("0"))
        self.assertEqual(summary.completion_percentage, Decimal("0"))
        self.assertEqual(len(summary.score_by_requirement), 6)
        with self.assertRaises(FrozenInstanceError):
            summary.total_score = Decimal("100")

    def test_partial_summary_uses_operational_evidence_percentage(self):
        process = self.create_process()
        document = self.facade.register_document(
            RegisterDocumentCommand(process.process_id, "ato.pdf")
        )
        first = self.facade.create_activity(
            CreateActivityCommand(
                process.process_id,
                criterion_id(1, 1),
                "Primeira",
                "1",
            )
        )
        self.facade.create_activity(
            CreateActivityCommand(
                process.process_id,
                criterion_id(2, 1),
                "Segunda",
                "1",
            )
        )
        self.facade.create_evidence(
            CreateEvidenceCommand(
                process.process_id,
                first.activity_id,
                (document.document_id,),
                "Ato",
            )
        )

        summary = self.facade.generate_summary(
            GenerateSummaryCommand(process.process_id)
        ).summary

        self.assertEqual(summary.total_activities, 2)
        self.assertEqual(summary.total_evidence, 1)
        self.assertEqual(summary.completion_percentage, Decimal("50.0"))
        self.assertEqual(summary.total_validation_warnings, 1)
        self.assertEqual(summary.total_validation_errors, 0)
        self.assertEqual(summary.total_score, Decimal("10.5"))

    def test_summary_preserves_validation_errors(self):
        process = self.create_process()
        activity = self.facade.create_activity(
            CreateActivityCommand(
                process.process_id,
                criterion_id(1, 1),
                "Completa",
                "1",
            )
        )
        self.session.rsc_activity_service.update_activity(
            process.process,
            replace(activity.activity, status=ActivityStatus.COMPLETE),
        )

        summary = self.facade.generate_summary(
            GenerateSummaryCommand(process.process_id)
        ).summary

        self.assertEqual(summary.total_validation_errors, 1)
        self.assertEqual(summary.total_validation_warnings, 0)
        self.assertFalse(summary.validation_result.is_valid)

    def test_summary_delegates_once_to_validation_and_scoring_use_cases(self):
        process = self.create_process()
        validation = self.session.use_cases.get(ValidateProcessUseCase)
        scoring = self.session.use_cases.get(CalculateScoreUseCase)

        class Spy:
            def __init__(self, target):
                self.target = target
                self.calls = []

            def execute(self, command):
                self.calls.append(command)
                return self.target.execute(command)

        validation_spy = Spy(validation)
        scoring_spy = Spy(scoring)
        self.session.use_cases._instances[
            ValidateProcessUseCase
        ] = validation_spy
        self.session.use_cases._instances[
            CalculateScoreUseCase
        ] = scoring_spy

        self.facade.generate_summary(
            GenerateSummaryCommand(process.process_id)
        )

        self.assertEqual(len(validation_spy.calls), 1)
        self.assertEqual(len(scoring_spy.calls), 1)
        self.assertIsInstance(
            validation_spy.calls[0], ValidateProcessCommand
        )
        self.assertIsInstance(
            scoring_spy.calls[0], CalculateScoreCommand
        )

    def test_facade_propagates_session_disposal_error(self):
        self.session.dispose()

        with self.assertRaises(SessionDisposedError):
            self.facade.create_process(
                CreateProcessCommand("Pessoa", "Instituição")
            )
        with self.assertRaises(SessionDisposedError):
            self.facade.generate_summary(
                GenerateSummaryCommand("processo")
            )

    def test_facade_and_summary_have_no_domain_algorithm_or_service_creation(self):
        root = Path(__file__).parents[1]
        facade_source = (root / "facade.py").read_text(encoding="utf-8")
        summary_source = (
            root / "use_cases" / "summary_use_case.py"
        ).read_text(encoding="utf-8")
        summary_tree = ast.parse(summary_source)

        self.assertNotIn("services", facade_source)
        self.assertNotIn("RscValidationService", summary_source)
        self.assertNotIn("RscScoringService", summary_source)
        self.assertNotIn("points_per_unit", summary_source)
        self.assertNotIn("raw_score", summary_source)
        calls = {
            node.func.attr
            for node in ast.walk(summary_tree)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
        }
        self.assertIn("execute", calls)


if __name__ == "__main__":
    unittest.main()
