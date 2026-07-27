import unittest

from platform_sdk import ApplicationDescriptor, Version

from ..descriptor import (
    APPLICATION_ID,
    APPLICATION_NAME,
    ASSET_AUDIT_DESCRIPTOR,
)


class AssetAuditDescriptorTests(unittest.TestCase):
    def test_descriptor_has_stable_supported_identity(self):
        descriptor = ASSET_AUDIT_DESCRIPTOR

        self.assertIsInstance(descriptor, ApplicationDescriptor)
        self.assertEqual(descriptor.application_id, APPLICATION_ID)
        self.assertEqual(descriptor.display_name, APPLICATION_NAME)
        self.assertEqual(descriptor.version, Version(0, 1, 0))
        self.assertEqual(descriptor.minimum_platform_version, Version(1, 0, 0))
        self.assertEqual(descriptor.supported_project_schema_versions, (1,))
        self.assertIn("Platform SDK", descriptor.description)

    def test_descriptor_does_not_require_icon(self):
        self.assertFalse(hasattr(ASSET_AUDIT_DESCRIPTOR, "icon"))


if __name__ == "__main__":
    unittest.main()
