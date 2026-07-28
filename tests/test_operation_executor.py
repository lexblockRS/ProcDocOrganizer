import ast
from dataclasses import FrozenInstanceError
from pathlib import Path
import unittest
from unittest.mock import patch

import presentation
from presentation import (
    ApplicationState,
    ApplicationStateStore,
    CancellationToken,
    InvalidApplicationStateTransition,
    OperationCancelled,
    OperationContext,
    OperationExecutor,
    OperationId,
)


class OperationIdTests(unittest.TestCase):
    def test_normalizes_compares_hashes_and_serializes(self):
        left = OperationId(" load ")
        right = OperationId("load")
        self.assertEqual(left, right)
        self.assertEqual(hash(left), hash(right))
        self.assertEqual(left.to_dict(), {"value": "load"})

    def test_is_frozen_and_slotted(self):
        operation_id = OperationId("load")
        self.assertFalse(hasattr(operation_id, "__dict__"))
        with self.assertRaises(FrozenInstanceError):
            operation_id.value = "save"

    def test_rejects_invalid_value(self):
        for value, error in (("", ValueError), ("  ", ValueError), (None, TypeError)):
            with self.subTest(value=value):
                with self.assertRaises(error):
                    OperationId(value)


class CancellationTokenTests(unittest.TestCase):
    def test_initial_state_and_idempotent_cancellation(self):
        token = CancellationToken()
        self.assertFalse(token.is_cancellation_requested)
        token.request_cancellation()
        token.request_cancellation()
        self.assertTrue(token.is_cancellation_requested)

    def test_throws_specific_exception_only_when_requested(self):
        token = CancellationToken()
        token.throw_if_cancellation_requested()
        token.request_cancellation()
        with self.assertRaises(OperationCancelled):
            token.throw_if_cancellation_requested()

    def test_does_not_expose_forced_interruption(self):
        token = CancellationToken()
        for name in ("abort", "kill", "terminate", "interrupt"):
            self.assertFalse(hasattr(token, name))


class OperationContextTests(unittest.TestCase):
    def test_is_frozen_slotted_and_preserves_references(self):
        operation_id = OperationId("load")
        token = CancellationToken()
        context = OperationContext(operation_id, token)
        self.assertIs(context.operation_id, operation_id)
        self.assertIs(context.cancellation_token, token)
        self.assertFalse(hasattr(context, "__dict__"))
        with self.assertRaises(FrozenInstanceError):
            context.operation_id = OperationId("other")

    def test_rejects_invalid_components(self):
        with self.assertRaises(TypeError):
            OperationContext(object(), CancellationToken())
        with self.assertRaises(TypeError):
            OperationContext(OperationId("load"), object())


class OperationExecutorTests(unittest.TestCase):
    def setUp(self):
        self.store = ApplicationStateStore()
        self.executor = OperationExecutor(self.store)
        self.operation_id = OperationId("operation-1")

    def test_success_orders_calls_and_preserves_result(self):
        calls = []
        result = object()
        original_begin = self.store.begin_operation
        original_complete = self.store.complete_operation

        def begin(value):
            calls.append("begin")
            return original_begin(value)

        def work(context):
            calls.append("work")
            self.assertIsInstance(context, OperationContext)
            self.assertEqual(context.operation_id, self.operation_id)
            return result

        def complete(value):
            calls.append("complete")
            return original_complete(value)

        with (
            patch.object(self.store, "begin_operation", side_effect=begin),
            patch.object(
                self.store, "complete_operation", side_effect=complete
            ) as completed,
            patch.object(self.store, "cancel_operation") as cancelled,
            patch.object(self.store, "fail_operation") as failed,
        ):
            returned = self.executor.execute(self.operation_id, work)
        self.assertIs(returned, result)
        self.assertEqual(calls, ["begin", "work", "complete"])
        completed.assert_called_once_with("operation-1")
        cancelled.assert_not_called()
        failed.assert_not_called()

    def test_pre_cancelled_token_cancels_before_work(self):
        token = CancellationToken()
        token.request_cancellation()
        work_calls = []
        with self.assertRaises(OperationCancelled) as raised:
            self.executor.execute(
                self.operation_id,
                lambda context: work_calls.append(context),
                token,
            )
        self.assertIsInstance(raised.exception, OperationCancelled)
        self.assertEqual(work_calls, [])
        self.assertIs(self.store.snapshot.state, ApplicationState.NO_PROJECT)
        self.assertEqual(self.store.snapshot.revision, 2)

    def test_cancellation_during_work_is_checked_after_return(self):
        token = CancellationToken()

        def work(context):
            context.cancellation_token.request_cancellation()
            return "ignored"

        with self.assertRaises(OperationCancelled):
            self.executor.execute(self.operation_id, work, token)
        self.assertIs(self.store.snapshot.state, ApplicationState.NO_PROJECT)

    def test_explicit_cancellation_is_preserved_and_exclusive(self):
        error = OperationCancelled("stop")
        with (
            patch.object(
                self.store,
                "cancel_operation",
                wraps=self.store.cancel_operation,
            ) as cancelled,
            patch.object(self.store, "complete_operation") as completed,
            patch.object(self.store, "fail_operation") as failed,
        ):
            with self.assertRaises(OperationCancelled) as raised:
                self.executor.execute(
                    self.operation_id,
                    lambda _context: (_ for _ in ()).throw(error),
                )
        self.assertIs(raised.exception, error)
        cancelled.assert_called_once_with("operation-1")
        completed.assert_not_called()
        failed.assert_not_called()

    def test_failure_is_recorded_and_original_exception_preserved(self):
        error = LookupError("failure")
        with (
            patch.object(
                self.store,
                "fail_operation",
                wraps=self.store.fail_operation,
            ) as failed,
            patch.object(self.store, "complete_operation") as completed,
            patch.object(self.store, "cancel_operation") as cancelled,
            self.assertLogs("presentation.operations", level="ERROR"),
        ):
            try:
                self.executor.execute(
                    self.operation_id,
                    lambda _context: (_ for _ in ()).throw(error),
                )
            except LookupError as raised:
                self.assertIs(raised, error)
                self.assertIsNotNone(raised.__traceback__)
            else:
                self.fail("LookupError não foi propagada.")
        failed.assert_called_once_with("operation-1", "failure")
        completed.assert_not_called()
        cancelled.assert_not_called()
        self.assertIs(self.store.snapshot.state, ApplicationState.ERROR)

    def test_empty_exception_message_uses_exception_type(self):
        with self.assertRaises(RuntimeError):
            self.executor.execute(
                self.operation_id,
                lambda _context: (_ for _ in ()).throw(RuntimeError()),
            )
        self.assertEqual(self.store.snapshot.error, "RuntimeError")

    def test_secondary_store_failure_does_not_mask_work_failure(self):
        original = LookupError("original")
        with (
            patch.object(
                self.store,
                "fail_operation",
                side_effect=RuntimeError("secondary"),
            ),
            self.assertLogs("presentation.operations", level="ERROR") as logs,
        ):
            with self.assertRaises(LookupError) as raised:
                self.executor.execute(
                    self.operation_id,
                    lambda _context: (_ for _ in ()).throw(original),
                )
        self.assertIs(raised.exception, original)
        self.assertTrue(
            any("Falha secundária" in message for message in logs.output)
        )

    def test_secondary_cancel_failure_preserves_cancellation(self):
        original = OperationCancelled("cancel")
        with (
            patch.object(
                self.store,
                "cancel_operation",
                side_effect=RuntimeError("secondary"),
            ),
            self.assertLogs("presentation.operations", level="ERROR"),
        ):
            with self.assertRaises(OperationCancelled) as raised:
                self.executor.execute(
                    self.operation_id,
                    lambda _context: (_ for _ in ()).throw(original),
                )
        self.assertIs(raised.exception, original)

    def test_begin_failure_does_not_run_or_finalize(self):
        self.store.begin_operation("already-running")
        work = unittest.mock.Mock()
        with (
            patch.object(self.store, "complete_operation") as completed,
            patch.object(self.store, "cancel_operation") as cancelled,
            patch.object(self.store, "fail_operation") as failed,
        ):
            with self.assertRaises(InvalidApplicationStateTransition):
                self.executor.execute(self.operation_id, work)
        work.assert_not_called()
        completed.assert_not_called()
        cancelled.assert_not_called()
        failed.assert_not_called()

    def test_validates_all_arguments_before_begin(self):
        with patch.object(self.store, "begin_operation") as begin:
            invalid_calls = (
                ("operation", lambda _context: None, None),
                (self.operation_id, None, None),
                (self.operation_id, lambda _context: None, object()),
            )
            for operation_id, work, token in invalid_calls:
                with self.subTest(
                    operation_id=operation_id, work=work, token=token
                ):
                    with self.assertRaises(TypeError):
                        self.executor.execute(operation_id, work, token)
            begin.assert_not_called()

    def test_rejects_invalid_store_and_has_no_store_api(self):
        with self.assertRaises(TypeError):
            OperationExecutor(object())
        self.assertFalse(hasattr(self.executor, "snapshot"))
        self.assertFalse(hasattr(self.executor, "revision"))
        self.assertFalse(hasattr(self.executor, "subscribe"))
        self.assertFalse(hasattr(self.executor, "__dict__"))


class OperationArchitectureTests(unittest.TestCase):
    def test_dependencies_and_public_api_are_restricted(self):
        path = Path("presentation/operations.py")
        tree = ast.parse(path.read_text(encoding="utf-8"))
        imported = {
            node.module or ""
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom)
        } | {
            alias.name
            for node in ast.walk(tree)
            if isinstance(node, ast.Import)
            for alias in node.names
        }
        forbidden = (
            "asyncio",
            "concurrent",
            "pyside",
            "pyqt",
            "selection",
            "perspective",
            "workspace",
            "presentation_context",
            "navigation",
            "facade",
            "domain",
            "infrastructure",
        )
        for name in imported:
            self.assertFalse(
                any(value in name.casefold() for value in forbidden),
                name,
            )
        public_methods = {
            node.name
            for node in ast.walk(tree)
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            and not node.name.startswith("_")
        }
        self.assertFalse(
            {"subscribe", "start_async", "run_in_background"}
            & public_methods
        )
        self.assertFalse(
            any(
                isinstance(node, (ast.AsyncFunctionDef, ast.Await))
                for node in ast.walk(tree)
            )
        )

    def test_no_thread_is_created(self):
        source = Path("presentation/operations.py").read_text(
            encoding="utf-8"
        )
        self.assertNotIn("Thread(", source)
        self.assertNotIn("ThreadPoolExecutor", source)
        self.assertNotIn("QThread", source)

    def test_public_exports_are_intentional(self):
        module = __import__(
            "presentation.operations",
            fromlist=["__all__"],
        )
        expected = {
            "CancellationToken",
            "OperationCancelled",
            "OperationContext",
            "OperationExecutor",
            "OperationId",
            "OperationWork",
        }
        self.assertEqual(set(module.__all__), expected)
        self.assertTrue(expected.issubset(set(presentation.__all__)))


if __name__ == "__main__":
    unittest.main()
