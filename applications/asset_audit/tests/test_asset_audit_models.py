from datetime import datetime, timezone
import unittest

from ..models import Asset, Audit, Evidence, Finding, HistoryEntry


class AssetAuditModelTests(unittest.TestCase):
    def test_models_create_ids_and_timezone_aware_dates(self):
        asset = Asset("Notebook", "equipment", "IT")
        audit = Audit("Inventory", asset_ids=(asset.id,))
        finding = Finding(audit.id, "Missing tag", "medium")
        evidence = Evidence(finding.id, "Photo", "inventory")
        history = HistoryEntry("asset", asset.id, "created")

        self.assertTrue(asset.id)
        self.assertEqual(audit.asset_ids, (asset.id,))
        self.assertEqual(finding.audit_id, audit.id)
        self.assertEqual(evidence.finding_id, finding.id)
        self.assertEqual(history.entity_id, asset.id)
        for value in (
            asset.created_at,
            audit.started_at,
            evidence.created_at,
            history.occurred_at,
        ):
            self.assertIsNotNone(value.tzinfo)

    def test_rejects_naive_dates_and_empty_required_values(self):
        with self.assertRaises(ValueError):
            Asset("", "equipment", "IT")
        with self.assertRaises(ValueError):
            Audit("Audit", started_at=datetime.now())
        with self.assertRaises(ValueError):
            Evidence("finding", "Photo", "source", created_at=datetime.now())

    def test_explicit_timezone_aware_values_are_preserved(self):
        occurred_at = datetime(2026, 1, 1, tzinfo=timezone.utc)
        entry = HistoryEntry(
            "audit", "audit-1", "opened", occurred_at=occurred_at
        )

        self.assertIs(entry.occurred_at, occurred_at)


if __name__ == "__main__":
    unittest.main()
