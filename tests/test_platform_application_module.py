from pathlib import Path
import unittest

from contracts.application_descriptor import (
    ApplicationDescriptor,
    Version,
)
from contracts.application_module import ApplicationModule
from contracts.lifecycle import (
    ApplicationLifecycleState,
    ApplicationLifecycleTransition,
)


class ExampleModule:
    descriptor = ApplicationDescriptor(
        application_id="example",
        display_name="Example",
        version=Version(1, 0, 0),
        minimum_platform_version=Version(1, 0, 0),
    )

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


class IncompleteModule:
    descriptor = ExampleModule.descriptor


class ApplicationModuleContractTests(unittest.TestCase):
    def test_is_structural_and_exposes_complete_future_boundary(self):
        module = ExampleModule()

        self.assertIsInstance(module, ApplicationModule)
        self.assertIs(module.descriptor, ExampleModule.descriptor)
        self.assertEqual(module.contributions(module.create_session(None)), ())
        module.prepare(None)
        module.transition(ApplicationLifecycleTransition(
            ApplicationLifecycleState.DISCOVERED,
            ApplicationLifecycleState.REGISTERED,
        ))
        module.dispose()

    def test_incomplete_implementation_does_not_satisfy_contract(self):
        self.assertNotIsInstance(IncompleteModule(), ApplicationModule)

    def test_contract_has_no_qt_rsc_session_or_factory_dependency(self):
        source = (
            Path(__file__).parents[1]
            / "contracts"
            / "application_module.py"
        ).read_text(encoding="utf-8")

        for forbidden in (
            "PySide6",
            "applications.rsc",
            "ProjectSession",
            "ProjectSessionFactory",
            "MainWindow",
            "ProjectController",
        ):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, source)


if __name__ == "__main__":
    unittest.main()
