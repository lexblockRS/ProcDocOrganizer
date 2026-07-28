import ast
from dataclasses import FrozenInstanceError
from pathlib import Path
import unittest

import presentation
from presentation import (
    Notification,
    NotificationCenter,
    NotificationLevel,
)


def notification():
    return Notification(
        NotificationLevel.INFO,
        "Projeto",
        "Projeto carregado.",
        3,
    )


class NotificationTests(unittest.TestCase):
    def test_level_has_exact_contract_values(self):
        self.assertEqual(
            set(NotificationLevel),
            {
                NotificationLevel.INFO,
                NotificationLevel.SUCCESS,
                NotificationLevel.WARNING,
                NotificationLevel.ERROR,
            },
        )

    def test_is_frozen_slotted_hashable_and_serializable(self):
        item = notification()
        self.assertEqual(item.timeout, 3.0)
        self.assertEqual(item, notification())
        self.assertEqual(hash(item), hash(notification()))
        self.assertEqual(
            item.to_dict(),
            {
                "level": "info",
                "title": "Projeto",
                "message": "Projeto carregado.",
                "timeout": 3.0,
            },
        )
        self.assertFalse(hasattr(item, "__dict__"))
        with self.assertRaises(FrozenInstanceError):
            item.message = "Outro"

    def test_normalizes_text_and_accepts_optional_timeout(self):
        item = Notification(
            NotificationLevel.SUCCESS,
            " Concluído ",
            " Operação concluída. ",
        )
        self.assertEqual(item.title, "Concluído")
        self.assertEqual(item.message, "Operação concluída.")
        self.assertIsNone(item.timeout)

    def test_rejects_invalid_fields(self):
        invalid = (
            ("info", "Título", "Mensagem", None, TypeError),
            (NotificationLevel.INFO, "", "Mensagem", None, ValueError),
            (NotificationLevel.INFO, "Título", " ", None, ValueError),
            (
                NotificationLevel.INFO,
                "Título",
                "Mensagem",
                True,
                TypeError,
            ),
            (
                NotificationLevel.INFO,
                "Título",
                "Mensagem",
                -1,
                ValueError,
            ),
        )
        for level, title, message, timeout, error in invalid:
            with self.subTest(
                level=level,
                title=title,
                message=message,
                timeout=timeout,
            ):
                with self.assertRaises(error):
                    Notification(level, title, message, timeout)


class NotificationCenterTests(unittest.TestCase):
    def setUp(self):
        self.center = NotificationCenter()
        self.item = notification()

    def test_publish_delivers_same_instance(self):
        received = []
        self.center.subscribe(received.append)
        result = self.center.publish(self.item)
        self.assertIsNone(result)
        self.assertEqual(received, [self.item])
        self.assertIs(received[0], self.item)

    def test_delivery_preserves_subscription_order(self):
        calls = []
        self.center.subscribe(lambda _item: calls.append("first"))
        self.center.subscribe(lambda _item: calls.append("second"))
        self.center.subscribe(lambda _item: calls.append("third"))
        self.center.publish(self.item)
        self.assertEqual(calls, ["first", "second", "third"])

    def test_unsubscribe_is_idempotent(self):
        received = []
        unsubscribe = self.center.subscribe(received.append)
        unsubscribe()
        unsubscribe()
        self.center.publish(self.item)
        self.assertEqual(received, [])

    def test_duplicate_subscription_is_not_repeated(self):
        received = []
        self.center.subscribe(received.append)
        self.center.subscribe(received.append)
        self.center.publish(self.item)
        self.assertEqual(received, [self.item])

    def test_observer_failure_is_logged_and_isolated(self):
        received = []

        def broken(_item):
            raise RuntimeError("observer failure")

        self.center.subscribe(broken)
        self.center.subscribe(received.append)
        with self.assertLogs(
            "presentation.notifications", level="ERROR"
        ):
            self.center.publish(self.item)
        self.assertEqual(received, [self.item])

    def test_publish_rejects_invalid_value_without_delivery(self):
        received = []
        self.center.subscribe(received.append)
        with self.assertRaises(TypeError):
            self.center.publish(object())
        self.assertEqual(received, [])

    def test_does_not_expose_store_or_history_api(self):
        for name in (
            "snapshot",
            "revision",
            "history",
            "notifications",
            "queue",
        ):
            self.assertFalse(hasattr(self.center, name))
        self.assertFalse(hasattr(self.center, "__dict__"))


class NotificationArchitectureTests(unittest.TestCase):
    def test_dependencies_are_restricted(self):
        path = Path("presentation/notifications.py")
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
            "pyside",
            "pyqt",
            "main_window",
            "statusbar",
            "dialog",
            "store",
            "domain",
            "infrastructure",
            "persistence",
        )
        for name in imported:
            self.assertFalse(
                any(value in name.casefold() for value in forbidden),
                name,
            )

    def test_ast_has_no_store_state_or_retention(self):
        tree = ast.parse(
            Path("presentation/notifications.py").read_text(
                encoding="utf-8"
            )
        )
        attributes = {
            node.attr
            for node in ast.walk(tree)
            if isinstance(node, ast.Attribute)
        }
        names = {
            node.id
            for node in ast.walk(tree)
            if isinstance(node, ast.Name)
        }
        forbidden = {
            "snapshot",
            "revision",
            "history",
            "queue",
            "_notifications",
        }
        self.assertFalse(forbidden & (attributes | names))

    def test_public_exports_are_intentional(self):
        module = __import__(
            "presentation.notifications",
            fromlist=["__all__"],
        )
        expected = {
            "Notification",
            "NotificationCenter",
            "NotificationLevel",
        }
        self.assertEqual(set(module.__all__), expected)
        self.assertTrue(expected.issubset(set(presentation.__all__)))


if __name__ == "__main__":
    unittest.main()
