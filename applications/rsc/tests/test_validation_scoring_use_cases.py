import ast
from dataclasses import replace
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace
import unittest
from uuid import uuid4

from applications.rsc import RscApplication
from applications.rsc.domain import (
    ActivityStatus,
    ValidationSeverity,
    criterion_id,
)
from applications.rsc.use_cases import (
    CalculateScoreCommand,
    CalculateScoreUseCase,
    CreateActivityCommand,
    CreateActivityUseCase,
    CreateEvidenceCommand,
    CreateEvidenceUseCase,
    CreateProcessCommand,
    CreateProcessUseCase,
    InvalidCommandError,
    ProcessNotFoundError,
    RegisterDocumentCommand,
    RegisterDocumentUseCase,
    SessionDisposedError,
    ValidateProcessCommand,
    ValidateProcessUseCase,
)


class EvidenceLookup:
    def exists(self, _evidence_id):
        return True


class ValidationScoringUseCaseTests(unittest.TestCase):
    def setUp(self):
        self.session = RscApplication().create_project_session(
            EvidenceLookup()
        )
        self.registry = self.session.use_cases
        self.process = self.registry.get(CreateProcessUseCase).execute(
            CreateProcessCommand("Pessoa", "Instituição")
        )

    def create_activity(self, criterion=criterion_id(1, 1), **values):
        return self.registry.get(CreateActivityUseCase).execute(
            CreateActivityCommand(
                self.process.process_id,
                criterion,
                values.pop("title", "Atividade"),
                values.pop("quantity", "1"),
                **values,
            )
        )

    def validate(self):
        return self.registry.get(ValidateProcessUseCase).execute(
            ValidateProcessCommand(self.process.process_id)
        )

    def score(self):
        return self.registry.get(CalculateScoreUseCase).execute(
            CalculateScoreCommand(self.process.process_id)
        )

    def test_commands_validate_type_uuid_and_missing_process(self):
        validate = self.registry.get(ValidateProcessUseCase)
        score = self.registry.get(CalculateScoreUseCase)

        for use_case in (validate, score):
            with self.subTest(use_case=type(use_case).__name__):
                with self.assertRaises(InvalidCommandError):
                    use_case.execute(None)
                command_type = (
                    ValidateProcessCommand
                    if use_case is validate
                    else CalculateScoreCommand
                )
                with self.assertRaises(InvalidCommandError):
                    use_case.execute(command_type("inválido"))
                with self.assertRaises(ProcessNotFoundError):
                    use_case.execute(command_type(str(uuid4())))

    def test_empty_process_validation_and_score_are_deterministic(self):
        first_validation = self.validate()
        second_validation = self.validate()
        first_score = self.score()
        second_score = self.score()

        self.assertTrue(first_validation.executed)
        self.assertTrue(first_validation.is_valid)
        self.assertEqual(first_validation.issues, ())
        self.assertEqual(first_validation.issues, second_validation.issues)
        self.assertEqual(first_score.total_score, Decimal("0"))
        self.assertEqual(len(first_score.requirement_scores), 6)
        self.assertEqual(
            tuple(item.total_score for item in first_score.requirement_scores),
            (Decimal("0"),) * 6,
        )
        self.assertEqual(
            first_score.requirement_scores,
            second_score.requirement_scores,
        )

    def test_draft_without_evidence_preserves_warning_structure(self):
        activity = self.create_activity()

        result = self.validate()
        issue = result.issues[0]

        self.assertTrue(result.is_valid)
        self.assertEqual(result.error_count, 0)
        self.assertEqual(result.warning_count, 1)
        self.assertEqual(result.warnings, (issue,))
        self.assertEqual(issue.code, "activity.evidence.missing")
        self.assertIs(issue.severity, ValidationSeverity.WARNING)
        self.assertEqual(issue.entity_type, "activity")
        self.assertEqual(issue.entity_id, activity.activity_id)
        self.assertEqual(issue.field, "evidence_ids")

    def test_complete_without_evidence_preserves_error(self):
        created = self.create_activity()
        complete = replace(
            created.activity, status=ActivityStatus.COMPLETE
        )
        self.session.rsc_activity_service.update_activity(
            self.process.process, complete
        )

        result = self.validate()

        self.assertFalse(result.is_valid)
        self.assertEqual(result.error_count, 1)
        self.assertEqual(result.warning_count, 0)
        self.assertIs(
            result.errors[0].severity, ValidationSeverity.ERROR
        )
        self.assertEqual(
            result.errors[0].code, "activity.evidence.missing"
        )

    def test_valid_evidence_removes_missing_evidence_issue(self):
        activity = self.create_activity()
        document = self.registry.get(RegisterDocumentUseCase).execute(
            RegisterDocumentCommand(self.process.process_id, "ato.pdf")
        )
        self.registry.get(CreateEvidenceUseCase).execute(
            CreateEvidenceCommand(
                self.process.process_id,
                activity.activity_id,
                (document.document_id,),
                "Ato",
            )
        )

        result = self.validate()

        self.assertTrue(result.is_valid)
        self.assertEqual(result.issues, ())

    def test_multiple_validation_issues_preserve_activity_order(self):
        first = self.create_activity(title="Primeira")
        second = self.create_activity(
            criterion_id(1, 2), title="Segunda"
        )

        result = self.validate()

        self.assertEqual(
            tuple(issue.entity_id for issue in result.issues),
            (first.activity_id, second.activity_id),
        )
        self.assertEqual(
            tuple(issue.code for issue in result.issues),
            ("activity.evidence.missing",) * 2,
        )

    def test_score_preserves_decimal_activity_and_requirement_details(self):
        first = self.create_activity(
            criterion_id(1, 2), quantity="2"
        )
        second = self.create_activity(
            criterion_id(2, 1), quantity="1"
        )

        result = self.score()
        requirement_one = result.requirement_scores[0]
        requirement_two = result.requirement_scores[1]

        self.assertIsInstance(result.total_score, Decimal)
        self.assertEqual(result.total_score, Decimal("16.5"))
        self.assertEqual(requirement_one.total_score, Decimal("9.0"))
        self.assertEqual(requirement_two.total_score, Decimal("7.5"))
        self.assertEqual(
            requirement_one.activity_scores[0].activity_id,
            first.activity_id,
        )
        self.assertEqual(
            requirement_two.activity_scores[0].activity_id,
            second.activity_id,
        )

    def test_variant_and_excluded_activity_follow_domain_service(self):
        criterion = criterion_id(5, 1)
        self.create_activity(
            criterion,
            score_variant_id=f"{criterion}.substituto",
        )
        excluded = self.create_activity(
            criterion_id(6, 1), title="Patente"
        )
        self.session.rsc_activity_service.update_activity(
            self.process.process,
            replace(excluded.activity, status=ActivityStatus.EXCLUDED),
        )

        result = self.score()

        self.assertEqual(result.total_score, Decimal("4.5"))
        self.assertEqual(result.requirement_scores[4].total_score, Decimal("4.5"))
        self.assertEqual(result.requirement_scores[5].total_score, Decimal("0"))
        self.assertEqual(
            result.requirement_scores[5].activity_scores, ()
        )

    def test_registry_session_and_disposal_contract(self):
        validate = self.registry.get(ValidateProcessUseCase)
        score = self.registry.get(CalculateScoreUseCase)
        self.assertIsInstance(validate, ValidateProcessUseCase)
        self.assertIsInstance(score, CalculateScoreUseCase)
        self.assertIs(
            validate._validation, self.session.rsc_validation_service
        )
        self.assertIs(score._scoring, self.session.rsc_scoring_service)
        self.assertIs(
            validate._processes, self.session.rsc_process_service
        )

        self.session.dispose()

        with self.assertRaises(SessionDisposedError):
            self.registry.get(ValidateProcessUseCase)
        with self.assertRaises(SessionDisposedError):
            self.registry.get(CalculateScoreUseCase)


class PipelineDelegationTests(unittest.TestCase):
    class ProcessStore:
        def __init__(self, process):
            self.process = process

        def get_process(self, _process_id):
            return self.process

    class ValidationSpy:
        def __init__(self, result):
            self.result = result
            self.calls = []

        def validate_process(self, process, evidence, documents):
            self.calls.append((process, evidence, documents))
            return self.result

    class ScoringSpy:
        def __init__(self, result):
            self.result = result
            self.calls = []

        def calculate_process(self, process):
            self.calls.append(process)
            return self.result

    def test_use_cases_delegate_without_reimplementing_rules(self):
        process_id = str(uuid4())
        process = SimpleNamespace(
            id=process_id,
            document_ids=(),
            list_activities=lambda: (),
        )
        validation_result = SimpleNamespace(
            issues=(),
            is_valid=True,
            error_count=0,
            warning_count=0,
        )
        score_result = SimpleNamespace(
            calculated_at=SimpleNamespace(),
            total_score=Decimal("12.5"),
            requirement_scores=(),
            warnings=(),
        )
        validation = self.ValidationSpy(validation_result)
        scoring = self.ScoringSpy(score_result)
        empty_documents = SimpleNamespace(get_document=lambda _id: None)
        empty_evidence = SimpleNamespace(list_by_activity=lambda _item: ())
        processes = self.ProcessStore(process)

        validated = ValidateProcessUseCase(
            processes, empty_documents, empty_evidence, validation
        ).execute(ValidateProcessCommand(process_id))
        scored = CalculateScoreUseCase(processes, scoring).execute(
            CalculateScoreCommand(process_id)
        )

        self.assertEqual(len(validation.calls), 1)
        self.assertEqual(scoring.calls, [process])
        self.assertIs(validated.validation, validation_result)
        self.assertIs(scored.score, score_result)
        self.assertEqual(scored.total_score, Decimal("12.5"))

    def test_pipeline_module_has_no_formula_catalog_or_severity_enum(self):
        path = (
            Path(__file__).parents[1]
            / "use_cases"
            / "validation_scoring_use_cases.py"
        )
        tree = ast.parse(path.read_text(encoding="utf-8"))

        self.assertFalse(
            any(
                isinstance(node, ast.BinOp)
                and isinstance(node.op, (ast.Mult, ast.Add))
                for node in ast.walk(tree)
            )
        )
        self.assertFalse(
            any(isinstance(node, ast.ClassDef) for node in ast.walk(tree))
            and any(
                isinstance(node, ast.ClassDef)
                and "Severity" in node.name
                for node in ast.walk(tree)
            )
        )
        self.assertNotIn("rsc.criterion.", path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
