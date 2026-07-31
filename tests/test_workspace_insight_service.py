import ast
from pathlib import Path
import unittest

from presentation import (
    DuplicateInsightIdentity,
    DuplicateInsightProvider,
    Insight,
    InsightAction,
    InsightCategory,
    InsightIdentity,
    InsightSeverity,
    InvalidInsightProviderResult,
    ProjectEvaluationInsightProvider,
    WorkspaceInsightProvider,
    WorkspaceInsightService,
    WorkspaceSnapshot,
)


def make_insight(provider_id, code, revision, severity=InsightSeverity.INFO):
    return Insight(
        InsightIdentity(provider_id, code),
        InsightCategory.INFORMATION,
        severity,
        "Título",
        "Mensagem.",
        "Explicação da condição observada.",
        (),
        (),
        revision,
    )


class Provider:
    def __init__(self, provider_id, factory):
        self.provider_id = provider_id
        self._factory = factory

    def provide(self, workspace_snapshot):
        return self._factory(workspace_snapshot)


class WorkspaceInsightServiceTests(unittest.TestCase):
    def test_provider_contract_and_initial_provider(self):
        provider = ProjectEvaluationInsightProvider()
        self.assertIsInstance(provider, WorkspaceInsightProvider)
        self.assertEqual(provider.provide(WorkspaceSnapshot()), ())

        workspace = WorkspaceSnapshot(
            revision=4,
            project_id="project-1",
        )
        produced = provider.provide(workspace)

        self.assertEqual(len(produced), 1)
        self.assertEqual(produced[0].message, "Projeto ainda não avaliado.")
        self.assertEqual(produced[0].source_revision, 4)
        self.assertEqual(
            produced[0].available_actions,
            (InsightAction.EXECUTE_EVALUATION,),
        )
        self.assertEqual(
            provider.provide(WorkspaceSnapshot(
                revision=5,
                project_id="project-1",
                current_evaluation="evaluation-1",
            )),
            (),
        )

    def test_service_executes_consolidates_and_orders_providers(self):
        first = Provider("info", lambda snapshot: (
            make_insight("info", "z.info", snapshot.revision),
        ))
        second = Provider("error", lambda snapshot: (
            make_insight(
                "error", "a.error", snapshot.revision, InsightSeverity.ERROR
            ),
        ))
        workspace = WorkspaceSnapshot(revision=7, project_id="project-1")

        collection = WorkspaceInsightService((first, second)).collect(workspace)

        self.assertEqual(collection.total, 2)
        self.assertEqual(collection.workspace_revision, 7)
        self.assertEqual(
            tuple(item.severity for item in collection.insights),
            (InsightSeverity.ERROR, InsightSeverity.INFO),
        )

    def test_service_rejects_duplicate_providers_and_insights(self):
        provider = Provider("same", lambda snapshot: ())
        with self.assertRaises(DuplicateInsightProvider):
            WorkspaceInsightService((provider, provider))

        duplicate = Provider("duplicates", lambda snapshot: (
            make_insight("duplicates", "same", snapshot.revision),
            make_insight("duplicates", "same", snapshot.revision),
        ))
        with self.assertRaises(DuplicateInsightIdentity):
            WorkspaceInsightService((duplicate,)).collect(
                WorkspaceSnapshot()
            )

    def test_service_rejects_invalid_result_origin_and_revision(self):
        invalid_tuple = Provider("invalid", lambda _snapshot: ["invalid"])
        wrong_origin = Provider("expected", lambda snapshot: (
            make_insight("other", "code", snapshot.revision),
        ))
        wrong_revision = Provider("revision", lambda snapshot: (
            make_insight("revision", "code", snapshot.revision + 1),
        ))
        for provider in (invalid_tuple, wrong_origin, wrong_revision):
            with self.subTest(provider=provider.provider_id):
                with self.assertRaises(InvalidInsightProviderResult):
                    WorkspaceInsightService((provider,)).collect(
                        WorkspaceSnapshot()
                    )


class WorkspaceInsightArchitectureTests(unittest.TestCase):
    def test_modules_have_no_domain_toolkit_or_persistence_dependencies(self):
        forbidden = (
            "pyside", "pyqt", "domain", "database", "sqlite",
            "infrastructure", "platform_sdk", "kernel", "validation",
            "compatibility",
        )
        for path in (
            Path("presentation/insights.py"),
            Path("presentation/workspace_insights.py"),
        ):
            tree = ast.parse(path.read_text(encoding="utf-8"))
            modules = {
                node.module or ""
                for node in ast.walk(tree)
                if isinstance(node, ast.ImportFrom)
            } | {
                alias.name
                for node in ast.walk(tree)
                if isinstance(node, ast.Import)
                for alias in node.names
            }
            for module in modules:
                self.assertFalse(
                    any(item in module.casefold() for item in forbidden),
                    (path, module),
                )

    def test_insight_dto_has_only_structural_validation(self):
        tree = ast.parse(Path("presentation/insights.py").read_text(
            encoding="utf-8"
        ))
        insight_class = next(
            node for node in tree.body
            if isinstance(node, ast.ClassDef) and node.name == "Insight"
        )
        methods = {
            node.name for node in insight_class.body
            if isinstance(node, ast.FunctionDef)
        }
        self.assertEqual(methods, {"__post_init__"})


if __name__ == "__main__":
    unittest.main()
