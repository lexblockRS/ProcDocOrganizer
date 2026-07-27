import unittest

from platform_sdk import SessionContext

from ..session import create_demo_session


def context():
    return SessionContext(
        document_engine=object(),
        knowledge_engine=object(),
    )


class AssetAuditSessionTests(unittest.TestCase):
    def test_demo_session_exposes_isolated_services_and_expected_data(self):
        session_context = context()
        session = create_demo_session(session_context)

        self.assertIs(session.context, session_context)
        self.assertEqual(session.asset_service.count_assets(), 12)
        self.assertEqual(session.audit_service.count_audits(), 4)
        self.assertEqual(session.audit_service.count_open_audits(), 2)
        self.assertEqual(session.finding_service.count_findings(), 7)
        self.assertEqual(
            session.finding_service.count_pending_findings(), 2
        )
        self.assertEqual(session.settings, {"storage": "memory"})

    def test_activation_and_disposal_are_idempotent(self):
        session = create_demo_session(context())
        session.cache["key"] = "value"

        session.activate()
        self.assertTrue(session.is_active)
        session.dispose()
        session.dispose()

        self.assertTrue(session.is_disposed)
        self.assertEqual(session.cache, {})
        with self.assertRaises(RuntimeError):
            _ = session.asset_service


if __name__ == "__main__":
    unittest.main()
