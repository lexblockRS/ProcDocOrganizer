import ast
from pathlib import Path
import unittest

import applications.rsc as public_package
from applications.rsc import api
from applications.rsc.commands import (
    CreateActivityCommand as LegacyCreateActivityCommand,
)
from applications.rsc.infrastructure import ProjectRepository
from applications.rsc.models import Activity
from applications.rsc.use_cases import (
    CreateActivityCommand as CanonicalCreateActivityCommand,
)


class PublicApiContractTests(unittest.TestCase):
    def test_root_package_mirrors_the_versioned_public_api(self):
        self.assertEqual(public_package.__all__, api.__all__)
        for name in api.__all__:
            with self.subTest(name=name):
                self.assertIs(
                    getattr(public_package, name),
                    getattr(api, name),
                )
        self.assertEqual(api.PUBLIC_API_VERSION, "1.5.1")

    def test_public_create_activity_command_is_the_canonical_command(self):
        self.assertIs(
            api.CreateActivityCommand,
            CanonicalCreateActivityCommand,
        )
        self.assertIsNot(
            api.CreateActivityCommand,
            LegacyCreateActivityCommand,
        )

    def test_legacy_surfaces_remain_importable_but_are_not_reexported(self):
        self.assertTrue(Activity)
        self.assertTrue(ProjectRepository)
        self.assertNotIn("Activity", api.__all__)
        self.assertNotIn("ProjectRepository", api.__all__)

    def test_public_surface_excludes_internal_implementation_types(self):
        forbidden_suffixes = (
            "UseCase",
            "Service",
            "Repository",
            "Serializer",
            "Registry",
            "Migration",
        )
        self.assertFalse(
            any(name.endswith(forbidden_suffixes) for name in api.__all__)
        )

    def test_api_module_does_not_import_internal_infrastructure(self):
        path = Path(api.__file__)
        tree = ast.parse(path.read_text(encoding="utf-8"))
        imports = {
            (node.module or "").lstrip(".")
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom)
        }
        self.assertNotIn("infrastructure", imports)
        self.assertNotIn("services", imports)
        self.assertNotIn("repositories", imports)


if __name__ == "__main__":
    unittest.main()
