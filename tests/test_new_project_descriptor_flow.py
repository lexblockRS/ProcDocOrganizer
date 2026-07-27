import ast
import os
from pathlib import Path
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from contracts import ApplicationDescriptor, Version
from core.application_registry import ApplicationRegistry
from ui.dialogs import NewProjectDialog


def descriptor(application_id, display_name, description=""):
    return ApplicationDescriptor(
        application_id=application_id,
        display_name=display_name,
        description=description,
        version=Version(1, 2, 3),
        minimum_platform_version=Version(1, 0, 0),
        supported_project_schema_versions=(1, 2),
    )


class PureModule:
    def __init__(self, module_descriptor):
        self.descriptor = module_descriptor

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


class HybridApplication(PureModule):
    def __init__(self, module_descriptor):
        super().__init__(module_descriptor)
        self.application_id = module_descriptor.application_id
        self.display_name = module_descriptor.display_name

    def can_open(self, project):
        return project.application == self.application_id


class LegacyApplication:
    application_id = "legacy.documents"
    display_name = "Gestão Documental"
    description = "Catálogo documental legado"
    version = Version(2, 0, 0)
    minimum_platform_version = Version(1, 0, 0)
    supported_project_schema_versions = (1,)

    def can_open(self, project):
        return project.application == self.application_id

    def contributions(self):
        return ()


class NewProjectDescriptorFlowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.asset_audit = PureModule(
            descriptor(
                "asset-audit",
                "Asset Audit",
                "Auditoria de ativos patrimoniais",
            )
        )
        self.hybrid = HybridApplication(
            descriptor("hybrid", "Aplicação Híbrida")
        )
        self.legacy = LegacyApplication()
        self.registry = ApplicationRegistry(
            (self.hybrid, self.legacy, self.asset_audit)
        )
        self.dialog = NewProjectDialog(
            descriptors=reversed(self.registry.descriptors)
        )

    def tearDown(self):
        self.dialog.close()

    def test_lists_pure_hybrid_and_legacy_entries_without_distinction(self):
        options = {
            self.dialog.application_selector.itemData(index):
            self.dialog.application_selector.itemText(index)
            for index in range(
                self.dialog.application_selector.count()
            )
        }

        self.assertEqual(
            options,
            {
                "asset-audit": "Asset Audit",
                "hybrid": "Aplicação Híbrida",
                "legacy.documents": "Gestão Documental",
            },
        )

    def test_orders_descriptors_deterministically_by_application_id(self):
        identifiers = tuple(
            self.dialog.application_selector.itemData(index)
            for index in range(
                self.dialog.application_selector.count()
            )
        )

        self.assertEqual(
            identifiers,
            ("asset-audit", "hybrid", "legacy.documents"),
        )

    def test_shows_available_descriptor_metadata(self):
        index = self.dialog.application_selector.findData("asset-audit")
        self.dialog.application_selector.setCurrentIndex(index)

        self.assertEqual(
            self.dialog.application_description.text(),
            "Auditoria de ativos patrimoniais",
        )
        self.assertEqual(self.dialog.application_version.text(), "1.2.3")
        self.assertEqual(
            self.dialog.application_compatibility.text(),
            "Plataforma 1.0.0 ou superior",
        )
        self.assertEqual(self.dialog.application_schema.text(), "1, 2")
        self.assertEqual(self.dialog.get_application_id(), "asset-audit")

    def test_rejects_objects_other_than_descriptors(self):
        with self.assertRaises(TypeError):
            NewProjectDialog(descriptors=(self.asset_audit,))

    def test_new_project_flow_has_no_concrete_application_dependencies(self):
        root = Path(__file__).parents[1]
        dialog_source = (
            root / "ui" / "dialogs" / "new_project_dialog.py"
        ).read_text(encoding="utf-8")
        controller_source = (
            root / "core" / "project_controller.py"
        ).read_text(encoding="utf-8")
        controller_tree = ast.parse(controller_source)
        new_project = next(
            node
            for node in ast.walk(controller_tree)
            if isinstance(node, ast.FunctionDef)
            and node.name == "new_project"
        )
        flow_source = ast.get_source_segment(
            controller_source, new_project
        )

        for forbidden in (
            "RscApplication",
            "ApplicationModule",
            "LEGACY_APPLICATION_ID",
            "registry.applications",
            ".applications",
        ):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, dialog_source)
                self.assertNotIn(forbidden, flow_source)


if __name__ == "__main__":
    unittest.main()
