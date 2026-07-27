from dataclasses import dataclass
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from applications import RscApplication
from contracts import (
    ActionContribution,
    ApplicationDescriptor,
    ApplicationModule,
    Version,
)
from core.application_registry import ApplicationRegistry
from core.project_manager import ProjectManager
from core.project_session_factory import ProjectSessionFactory
from core.session_context import SessionContext


@dataclass(frozen=True)
class AssetAuditSession:
    marker: str


class AssetAuditModule:
    descriptor = ApplicationDescriptor(
        application_id="asset-audit",
        display_name="Asset Audit",
        version=Version(1, 0, 0),
        minimum_platform_version=Version(1, 0, 0),
        supported_project_schema_versions=(1,),
    )

    def __init__(self):
        self.created_contexts = []
        self.session = AssetAuditSession("asset-audit-session")

    def prepare(self, context):
        pass

    def create_session(self, context):
        self.created_contexts.append(context)
        return self.session

    def contributions(self, session):
        return (
            ActionContribution(
                contribution_id="asset-audit.inspect",
                text="Inspect assets",
                callback=lambda: None,
                menu_id="tools",
            ),
        )

    def transition(self, transition):
        pass

    def dispose(self):
        pass


class LegacyAuditApplication:
    application_id = "legacy-audit"
    display_name = "Legacy Audit"

    def can_open(self, project):
        return project.application == self.application_id

    def contributions(self):
        return ()


class Core10ArchitectureTests(unittest.TestCase):
    def test_registry_supports_rsc_asset_audit_and_legacy_together(self):
        rsc = RscApplication()
        asset_audit = AssetAuditModule()
        legacy = LegacyAuditApplication()
        registry = ApplicationRegistry(
            [rsc, asset_audit, legacy]
        )

        self.assertIsInstance(rsc, ApplicationModule)
        self.assertIsInstance(asset_audit, ApplicationModule)
        self.assertEqual(
            tuple(
                descriptor.application_id
                for descriptor in registry.descriptors
            ),
            ("asset-audit", "legacy-audit", "rsc"),
        )
        self.assertIs(
            registry.get_module("asset-audit"),
            asset_audit,
        )
        self.assertIs(registry.get("legacy-audit"), legacy)

    def test_asset_audit_uses_same_factory_without_rsc_dependency(self):
        with TemporaryDirectory() as temporary:
            asset_audit = AssetAuditModule()
            registry = ApplicationRegistry(
                [RscApplication(), asset_audit, LegacyAuditApplication()]
            )
            project = ProjectManager().create_project(
                "Asset Audit",
                Path(temporary),
                application_id="asset-audit",
            )

            session = ProjectSessionFactory(registry).create(project)
            runtime = session.platform_session.application_runtime

            self.assertEqual(len(asset_audit.created_contexts), 1)
            self.assertIsInstance(
                asset_audit.created_contexts[0],
                SessionContext,
            )
            self.assertIs(runtime.module, asset_audit)
            self.assertIs(
                runtime.application_session,
                asset_audit.session,
            )
            self.assertIsNone(session.rsc_session)
            self.assertEqual(
                asset_audit.contributions(runtime.application_session)[0]
                .contribution_id,
                "asset-audit.inspect",
            )

    def test_factory_source_has_no_concrete_application_knowledge(self):
        source = (
            Path(__file__).parents[1]
            / "core"
            / "project_session_factory.py"
        ).read_text(encoding="utf-8")

        for forbidden in (
            "applications.rsc",
            "RscApplication",
            "RscProjectSession",
            "RSC_APPLICATION_ID",
            "_create_rsc_session",
            "create_project_session",
        ):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, source)


if __name__ == "__main__":
    unittest.main()
