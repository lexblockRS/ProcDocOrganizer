import ast
import os
from pathlib import Path
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from PySide6.QtWidgets import QApplication

from presentation import (
    NavigationIntentType,
    PresentationAction,
    RelationshipType,
    Resource,
    ResourceDisplay,
    ResourceIdentity,
    ResourceInspectorViewModel,
    ResourceRelationship,
    ResourceType,
)
from ui.resource_inspector import ResourceInspectorView


class ResourceInspectorViewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_renders_resource_and_emits_relationship_intent(self):
        resource = Resource(
            ResourceIdentity(ResourceType.DOCUMENT, "doc-1"),
            ResourceDisplay("Portaria", "available", {"pages": 2}),
            (ResourceRelationship(
                RelationshipType.USED_BY,
                ResourceIdentity(ResourceType.EVIDENCE, "ev-1"),
            ),),
            (PresentationAction.OPEN,),
        )
        view = ResourceInspectorView(
            ResourceInspectorViewModel.from_resource(resource).data
        )
        emitted = []
        view.navigation_requested.connect(emitted.append)

        view.relationships_tree.setCurrentItem(
            view.relationships_tree.topLevelItem(0)
        )
        view.relationship_button.click()

        self.assertEqual(view.type_value.text(), "document")
        self.assertEqual(view.name_value.text(), "Portaria")
        self.assertEqual(view.metadata_table.rowCount(), 1)
        self.assertEqual(len(emitted), 1)
        self.assertIs(
            emitted[0].intent_type, NavigationIntentType.OPEN_EVIDENCE
        )

    def test_emits_declared_action_without_executing_it(self):
        resource = Resource(
            ResourceIdentity(ResourceType.REQUIREMENT, "req-1"),
            ResourceDisplay("Requirement"),
            available_actions=(PresentationAction.INSPECT,),
        )
        view = ResourceInspectorView(
            ResourceInspectorViewModel.from_resource(resource).data
        )
        emitted = []
        view.navigation_requested.connect(emitted.append)

        view._action_buttons[0].click()

        self.assertEqual(len(emitted), 1)
        self.assertIs(
            emitted[0].intent_type,
            NavigationIntentType.OPEN_REQUIREMENT,
        )
        self.assertEqual(emitted[0].metadata["action"], "inspect")

    def test_consistent_empty_sections_and_unavailable_state(self):
        view = ResourceInspectorView(
            ResourceInspectorViewModel.empty().data
        )
        self.assertIn("Nenhum", view.message_value.text())
        self.assertEqual(view.metadata_table.rowCount(), 1)
        self.assertEqual(view.relationships_tree.topLevelItemCount(), 1)
        self.assertFalse(view.relationship_button.isEnabled())

        view.set_data(ResourceInspectorViewModel.unavailable().data)
        self.assertIn("indisponível", view.message_value.text())


class ResourceInspectorArchitectureTests(unittest.TestCase):
    def test_view_depends_only_on_inspector_presentation_dtos(self):
        tree = ast.parse(
            Path("ui/resource_inspector.py").read_text(encoding="utf-8")
        )
        modules = {
            node.module or ""
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom)
        }
        forbidden = (
            "domain", "database", "sqlite", "stores", "platform_sdk",
            "resource_projection", "main_window", "views",
        )
        for module in modules:
            self.assertFalse(
                any(item in module.casefold() for item in forbidden), module
            )
        self.assertEqual(
            {
                module
                for module in modules
                if module.startswith("presentation")
            },
            {"presentation.resource_inspector_view_model"},
        )

    def test_view_model_has_no_qt_domain_or_persistence_dependency(self):
        tree = ast.parse(Path(
            "presentation/resource_inspector_view_model.py"
        ).read_text(encoding="utf-8"))
        modules = {
            node.module or ""
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom)
        }
        self.assertFalse(any(
            any(item in module.casefold() for item in (
                "pyside", "pyqt", "domain", "database", "sqlite",
                "infrastructure", "platform_sdk",
            ))
            for module in modules
        ))


if __name__ == "__main__":
    unittest.main()
