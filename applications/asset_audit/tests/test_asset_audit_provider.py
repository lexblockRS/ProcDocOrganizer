from pathlib import Path
import unittest

from platform_sdk import ApplicationCatalog, ApplicationProvider

from ..descriptor import APPLICATION_ID
from ..provider import APPLICATION_PROVIDER


class AssetAuditProviderTests(unittest.TestCase):
    def test_provider_implements_public_contract(self):
        self.assertIsInstance(APPLICATION_PROVIDER, ApplicationProvider)

    def test_discovery_finds_asset_audit_and_rsc_deterministically(self):
        catalog = ApplicationCatalog.discover()
        identifiers = tuple(
            item.descriptor.application_id
            for item in catalog.applications
        )

        self.assertEqual(identifiers, tuple(sorted(identifiers)))
        self.assertIn(APPLICATION_ID, identifiers)
        self.assertIn("rsc", identifiers)
        self.assertEqual(len(identifiers), len(set(identifiers)))

    def test_composition_root_has_no_asset_audit_registration(self):
        source = (
            Path(__file__).parents[3] / "core" / "application.py"
        ).read_text(encoding="utf-8")

        self.assertNotIn("AssetAuditApplication", source)
        self.assertNotIn("asset_audit", source)


if __name__ == "__main__":
    unittest.main()
