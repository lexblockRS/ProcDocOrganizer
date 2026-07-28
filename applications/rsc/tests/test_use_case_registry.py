from dataclasses import FrozenInstanceError
from datetime import datetime, timezone
import unittest

from applications.rsc.use_cases import (
    ActivityNotFoundError,
    CalculateScoreCommand,
    CreateActivityCommand,
    CreateActivityResult,
    CreateEvidenceCommand,
    CreateEvidenceResult,
    CreateProcessCommand,
    CreateProcessResult,
    DocumentNotFoundError,
    DomainValidationError,
    DuplicateEntityError,
    EvidenceNotFoundError,
    GenerateSummaryCommand,
    InvalidCommandError,
    ProcessNotFoundError,
    RegisterDocumentCommand,
    RegisterDocumentResult,
    RscUseCaseError,
    RscUseCaseRegistry,
    ScoreUseCaseResult,
    SessionDisposedError,
    SummaryUseCaseResult,
    ValidateProcessCommand,
    ValidationUseCaseResult,
)


class FirstUseCase:
    pass


class SecondUseCase:
    pass


class UseCaseRegistryTests(unittest.TestCase):
    def test_registry_starts_empty_registers_gets_and_iterates(self):
        registry = RscUseCaseRegistry()
        first = FirstUseCase()
        second = SecondUseCase()

        registry.register(first)
        registry.register(second)

        self.assertEqual(len(registry), 2)
        self.assertIs(registry.get(FirstUseCase), first)
        self.assertEqual(tuple(registry), (first, second))

    def test_registry_rejects_duplicate_concrete_type(self):
        registry = RscUseCaseRegistry()
        registry.register(FirstUseCase())

        with self.assertRaises(DuplicateEntityError):
            registry.register(FirstUseCase())

    def test_registry_reports_missing_type(self):
        with self.assertRaisesRegex(KeyError, "não registrado"):
            RscUseCaseRegistry().get(FirstUseCase)

    def test_dispose_is_idempotent_and_blocks_future_access(self):
        registry = RscUseCaseRegistry()
        registry.register(FirstUseCase())

        registry.dispose()
        registry.dispose()

        self.assertTrue(registry.is_disposed)
        self.assertEqual(len(registry), 0)
        with self.assertRaises(SessionDisposedError):
            registry.get(FirstUseCase)
        with self.assertRaises(SessionDisposedError):
            registry.register(SecondUseCase())
        with self.assertRaises(SessionDisposedError):
            tuple(registry)


class UseCaseContractTests(unittest.TestCase):
    def test_commands_are_frozen_data_only(self):
        commands = (
            CreateProcessCommand("Pessoa", "Instituição"),
            CreateActivityCommand("p1", "c1", "Atividade", "1"),
            RegisterDocumentCommand("p1", "ato.pdf"),
            CreateEvidenceCommand("p1", "a1", ("d1",), "Ato"),
            ValidateProcessCommand("p1"),
            CalculateScoreCommand("p1"),
            GenerateSummaryCommand("p1"),
        )

        for command in commands:
            with self.subTest(command=type(command).__name__):
                with self.assertRaises(FrozenInstanceError):
                    command.process_id = "outro"

    def test_results_are_frozen_structured_values(self):
        now = datetime.now(timezone.utc)
        results = (
            CreateProcessResult("p1", now),
            CreateActivityResult("p1", "a1", now),
            RegisterDocumentResult("p1", "d1", now),
            CreateEvidenceResult("p1", "a1", "e1", now),
            ValidationUseCaseResult("p1", now),
            ScoreUseCaseResult("p1", now),
            SummaryUseCaseResult("p1", now),
        )

        for result in results:
            with self.subTest(result=type(result).__name__):
                self.assertEqual(result.process_id, "p1")
                with self.assertRaises(FrozenInstanceError):
                    result.process_id = "outro"

    def test_specialized_errors_share_application_base(self):
        errors = (
            InvalidCommandError,
            ProcessNotFoundError,
            ActivityNotFoundError,
            DocumentNotFoundError,
            EvidenceNotFoundError,
            DuplicateEntityError,
            DomainValidationError,
            SessionDisposedError,
        )
        self.assertTrue(
            all(issubclass(error, RscUseCaseError) for error in errors)
        )
        self.assertEqual(str(ProcessNotFoundError("processo p1")), "processo p1")


if __name__ == "__main__":
    unittest.main()
