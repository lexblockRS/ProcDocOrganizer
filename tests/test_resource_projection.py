import ast
from pathlib import Path
import unittest

from presentation import (
    DocumentResourceProjector,
    EvidenceResourceProjector,
    PresentationAction,
    ProjectionService,
    RequirementResourceProjector,
    ResourceContractError,
    ResourceIdentity,
    ResourceType,
    WorkspaceSnapshot,
)


class ResourceProjectionTests(unittest.TestCase):
    def test_initial_projectors_implement_common_contract(self):
        cases = (
            (DocumentResourceProjector(), ResourceType.DOCUMENT, "doc-1"),
            (EvidenceResourceProjector(), ResourceType.EVIDENCE, "ev-1"),
            (
                RequirementResourceProjector(),
                ResourceType.REQUIREMENT,
                "req-1",
            ),
        )
        workspace = WorkspaceSnapshot(project_id="project-1")

        for projector, resource_type, identifier in cases:
            with self.subTest(resource_type=resource_type):
                self.assertIsInstance(projector, ProjectionService)
                identity = ResourceIdentity(resource_type, identifier)
                resource = projector.project(identity, workspace)
                self.assertIs(resource.identity, identity)
                self.assertEqual(resource.display.display_name, identifier)
                self.assertEqual(
                    resource.available_actions,
                    (PresentationAction.OPEN,),
                )

    def test_projectors_reject_other_resource_types(self):
        with self.assertRaises(ResourceContractError):
            DocumentResourceProjector().project(
                ResourceIdentity(ResourceType.EVIDENCE, "ev-1"),
                WorkspaceSnapshot(),
            )

    def test_projectors_validate_workspace_contract(self):
        identity = ResourceIdentity(ResourceType.DOCUMENT, "doc-1")
        with self.assertRaises(TypeError):
            DocumentResourceProjector().project(identity, object())


class ResourceArchitectureTests(unittest.TestCase):
    def test_infrastructure_has_no_domain_toolkit_or_database_dependency(self):
        forbidden = (
            "pyside",
            "pyqt",
            "domain",
            "database",
            "sqlite",
            "infrastructure",
            "platform_sdk",
        )
        for path in (
            Path("presentation/resources.py"),
            Path("presentation/resource_projection.py"),
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

    def test_resource_dto_has_no_service_or_action_methods(self):
        tree = ast.parse(
            Path("presentation/resources.py").read_text(encoding="utf-8")
        )
        resource = next(
            node
            for node in tree.body
            if isinstance(node, ast.ClassDef) and node.name == "Resource"
        )
        methods = {
            node.name
            for node in resource.body
            if isinstance(node, ast.FunctionDef)
        }
        self.assertEqual(methods, {"__post_init__"})


if __name__ == "__main__":
    unittest.main()
