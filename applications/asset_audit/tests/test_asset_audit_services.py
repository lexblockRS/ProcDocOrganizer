import unittest

from ..models import Asset, Audit, Finding
from ..services import AssetService, AuditService, FindingService


class AssetAuditServiceTests(unittest.TestCase):
    def test_asset_service_adds_lists_gets_and_counts(self):
        service = AssetService()
        asset = service.add_asset(Asset("Asset", "equipment", "Owner"))

        self.assertEqual(service.list_assets(), (asset,))
        self.assertIs(service.get_asset(asset.id), asset)
        self.assertEqual(service.count_assets(), 1)
        with self.assertRaises(KeyError):
            service.get_asset("missing")
        with self.assertRaises(ValueError):
            service.add_asset(asset)

    def test_audit_service_counts_all_and_open(self):
        service = AuditService()
        opened = service.add_audit(Audit("Open"))
        completed = service.add_audit(Audit("Done", status="completed"))

        self.assertEqual(service.list_audits(), (opened, completed))
        self.assertEqual(service.count_audits(), 2)
        self.assertEqual(service.count_open_audits(), 1)
        self.assertIs(service.get_audit(opened.id), opened)
        with self.assertRaises(KeyError):
            service.get_audit("missing")

    def test_finding_service_counts_all_and_pending(self):
        service = FindingService()
        pending = service.add_finding(
            Finding("audit", "Pending", "high")
        )
        resolved = service.add_finding(
            Finding("audit", "Done", "low", status="resolved")
        )

        self.assertEqual(service.list_findings(), (pending, resolved))
        self.assertEqual(service.count_findings(), 2)
        self.assertEqual(service.count_pending_findings(), 1)
        self.assertIs(service.get_finding(pending.id), pending)
        with self.assertRaises(KeyError):
            service.get_finding("missing")


if __name__ == "__main__":
    unittest.main()
