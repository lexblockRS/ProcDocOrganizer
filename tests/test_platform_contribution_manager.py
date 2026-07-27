import ast
from pathlib import Path
import unittest

from contracts import (
    ActionContribution,
    ApplicationDescriptor,
    ContributionCategory,
    ContributionRegistration,
    Version,
)
from core.contribution_manager import ContributionManager
from core.exceptions import ContributionError


def action(contribution_id):
    return ActionContribution(
        contribution_id=contribution_id,
        text=contribution_id,
        callback=lambda: None,
    )


def registration(
    contribution_id,
    *,
    application_id="alpha",
    category=ContributionCategory.ACTION,
    priority=0,
):
    return ContributionRegistration(
        category=category,
        application_id=application_id,
        priority=priority,
        contribution=action(contribution_id),
    )


class ModuleDouble:
    descriptor = ApplicationDescriptor(
        application_id="module",
        display_name="Module",
        version=Version(1, 0, 0),
        minimum_platform_version=Version(1, 0, 0),
        supported_project_schema_versions=(1,),
    )

    def prepare(self, context):
        pass

    def create_session(self, context):
        return object()

    def contributions(self, session):
        return ()

    def transition(self, transition):
        pass

    def dispose(self):
        pass


class LegacyDouble:
    application_id = "legacy"
    display_name = "Legacy"

    def can_open(self, project):
        return True

    def contributions(self):
        return ()


class HybridDouble(ModuleDouble):
    application_id = "hybrid"
    display_name = "Hybrid"
    descriptor = ApplicationDescriptor(
        application_id=application_id,
        display_name=display_name,
        version=Version(1, 0, 0),
        minimum_platform_version=Version(1, 0, 0),
        supported_project_schema_versions=(1,),
    )

    def can_open(self, project):
        return True


class PlatformContributionManagerTests(unittest.TestCase):
    def test_declares_every_required_category(self):
        self.assertEqual(
            set(ContributionCategory),
            {
                ContributionCategory.MENU,
                ContributionCategory.TOOLBAR,
                ContributionCategory.VIEW,
                ContributionCategory.PAGE,
                ContributionCategory.DASHBOARD,
                ContributionCategory.ACTION,
                ContributionCategory.COMMAND,
                ContributionCategory.SERVICE,
                ContributionCategory.OTHER,
            },
        )

    def test_registers_and_queries_by_category_and_application(self):
        manager = ContributionManager()
        alpha = registration("alpha.action", priority=10)
        beta = registration(
            "beta.view",
            application_id="beta",
            category=ContributionCategory.VIEW,
            priority=20,
        )

        manager.register_many((alpha, beta))

        self.assertEqual(manager.all_contributions(), (beta, alpha))
        self.assertEqual(
            manager.by_category(ContributionCategory.VIEW),
            (beta,),
        )
        self.assertEqual(manager.by_application("alpha"), (alpha,))
        self.assertEqual(
            manager.categories(),
            (ContributionCategory.ACTION, ContributionCategory.VIEW),
        )
        self.assertEqual(manager.applications(), ("alpha", "beta"))

    def test_higher_priority_precedes_lower_priority(self):
        manager = ContributionManager()
        low = registration("low", priority=-10)
        high = registration("high", priority=100)
        normal = registration("normal")

        manager.register_many((low, high, normal))

        self.assertEqual(
            manager.all_contributions(),
            (high, normal, low),
        )

    def test_ties_are_deterministic(self):
        manager = ContributionManager()
        second = registration("second", application_id="beta")
        first = registration("first", application_id="alpha")

        manager.register_many((second, first))

        expected = (first, second)
        self.assertEqual(manager.all_contributions(), expected)
        self.assertEqual(manager.all_contributions(), expected)

    def test_register_application_supports_module_legacy_and_hybrid(self):
        manager = ContributionManager()

        manager.register_application(ModuleDouble(), (action("module"),))
        manager.register_application(LegacyDouble(), (action("legacy"),))
        manager.register_application(HybridDouble(), (action("hybrid"),))

        self.assertEqual(
            manager.applications(),
            ("hybrid", "legacy", "module"),
        )
        self.assertEqual(
            tuple(
                item.application_id
                for item in manager.all_contributions()
            ),
            ("hybrid", "legacy", "module"),
        )

    def test_register_application_accepts_prepared_registration(self):
        manager = ContributionManager()
        prepared = registration(
            "module.service",
            application_id="module",
            category=ContributionCategory.SERVICE,
        )

        manager.register_application(ModuleDouble(), (prepared,))

        self.assertEqual(manager.all_contributions(), (prepared,))

    def test_duplicate_declared_id_is_rejected_atomically(self):
        manager = ContributionManager()
        first = registration("duplicate")
        manager.register(first)

        with self.assertRaisesRegex(
            ContributionError,
            "Contribuição duplicada",
        ):
            manager.register(registration(
                "duplicate",
                category=ContributionCategory.MENU,
            ))

        self.assertEqual(manager.all_contributions(), (first,))

    def test_same_declared_id_is_allowed_for_distinct_applications(self):
        manager = ContributionManager()
        alpha = registration("shared", application_id="alpha")
        beta = registration("shared", application_id="beta")

        manager.register_many((alpha, beta))

        self.assertEqual(len(manager.all_contributions()), 2)

    def test_rejects_unknown_category_invalid_priority_and_null(self):
        with self.assertRaises(TypeError):
            ContributionRegistration("unknown", "alpha", 0, object())
        with self.assertRaises(TypeError):
            ContributionRegistration(
                ContributionCategory.ACTION,
                "alpha",
                True,
                object(),
            )
        with self.assertRaises(ValueError):
            ContributionRegistration(
                ContributionCategory.ACTION,
                "alpha",
                0,
                None,
            )

    def test_rejects_null_registration_and_unknown_query_category(self):
        manager = ContributionManager()

        with self.assertRaises(ContributionError):
            manager.register(None)
        with self.assertRaisesRegex(
            ContributionError,
            "Categoria de contribuição desconhecida",
        ):
            manager.by_category("unknown")

    def test_clear_registered_does_not_change_legacy_snapshot(self):
        manager = ContributionManager()
        legacy_action = action("legacy-active")
        manager.activate((legacy_action,))
        manager.register(registration("catalog"))

        manager.clear_registered()

        self.assertEqual(manager.all_contributions(), ())
        self.assertEqual(manager.active(), (legacy_action,))

    def test_manager_has_no_forbidden_imports(self):
        path = (
            Path(__file__).parents[1]
            / "core"
            / "contribution_manager.py"
        )
        tree = ast.parse(path.read_text(encoding="utf-8"))
        imported = {
            alias.name
            for node in ast.walk(tree)
            if isinstance(node, ast.Import)
            for alias in node.names
        }
        imported.update(
            node.module or ""
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom)
        )

        for forbidden in (
            "PySide6",
            "applications",
            "presentation",
            "controllers",
            "views",
            "dialogs",
            "dashboard",
            "MainWindow",
            "sqlite",
            "repositories",
        ):
            with self.subTest(forbidden=forbidden):
                self.assertFalse(any(
                    forbidden.casefold() in item.casefold()
                    for item in imported
                ))


if __name__ == "__main__":
    unittest.main()
