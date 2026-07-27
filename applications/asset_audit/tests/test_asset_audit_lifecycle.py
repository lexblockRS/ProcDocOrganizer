import unittest

from platform_sdk import (
    ApplicationLifecycleState,
    ApplicationRuntime,
    SessionContext,
)

from ..application import AssetAuditApplication


class AssetAuditLifecycleTests(unittest.TestCase):
    def test_complete_lifecycle_creates_activates_and_disposes_once(self):
        application = AssetAuditApplication()
        runtime = ApplicationRuntime(
            descriptor=application.descriptor,
            module=application,
            lifecycle_state=ApplicationLifecycleState.REGISTERED,
        )
        context = SessionContext(object(), object())

        runtime.prepare(context)
        session = runtime.create_session(context)
        runtime.activate()

        self.assertTrue(session.is_active)
        self.assertEqual(
            runtime.lifecycle_state,
            ApplicationLifecycleState.ACTIVE,
        )
        self.assertEqual(
            application.hook_log,
            ["prepare", "create_session"],
        )

        runtime.dispose()
        runtime.dispose()

        self.assertTrue(session.is_disposed)
        self.assertEqual(
            runtime.lifecycle_state,
            ApplicationLifecycleState.DISPOSED,
        )
        self.assertEqual(
            application.hook_log,
            ["prepare", "create_session", "dispose"],
        )
        self.assertEqual(
            tuple(item.target for item in application.transitions),
            (
                ApplicationLifecycleState.PROJECT_PREPARED,
                ApplicationLifecycleState.SESSION_CREATED,
                ApplicationLifecycleState.PRESENTATION_MOUNTED,
                ApplicationLifecycleState.ACTIVE,
                ApplicationLifecycleState.DEACTIVATING,
                ApplicationLifecycleState.DISPOSED,
            ),
        )


if __name__ == "__main__":
    unittest.main()
