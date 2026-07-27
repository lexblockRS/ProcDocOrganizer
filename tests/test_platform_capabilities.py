from datetime import datetime, timezone
from pathlib import Path
import unittest

from contracts.capabilities import (
    CLOCK_CAPABILITY,
    DOCUMENT_ENGINE_CAPABILITY,
    ID_GENERATOR_CAPABILITY,
    KNOWLEDGE_ENGINE_CAPABILITY,
    LOGGING_CAPABILITY,
    NAVIGATION_CAPABILITY,
    Capability,
    CapabilityProvider,
    ClockCapability,
    DocumentEngineCapability,
    IdGeneratorCapability,
    KnowledgeEngineCapability,
    LoggingCapability,
    NavigationCapability,
)


class Clock:
    capability_id = CLOCK_CAPABILITY

    def now(self):
        return datetime(2026, 7, 27, tzinfo=timezone.utc)


class IdentifierGenerator:
    capability_id = ID_GENERATOR_CAPABILITY

    def new_id(self):
        return "opaque-id"


class Navigator:
    capability_id = NAVIGATION_CAPABILITY

    def navigate(self, destination, parameters=None):
        return bool(destination)


class Logger:
    capability_id = LOGGING_CAPABILITY

    def debug(self, message):
        pass

    def info(self, message):
        pass

    def warning(self, message):
        pass

    def error(self, message, exception=None):
        pass


class Engine:
    def __init__(self, capability_id):
        self.capability_id = capability_id


class Provider:
    def __init__(self, capabilities):
        self._capabilities = {
            capability.capability_id: capability
            for capability in capabilities
        }

    @property
    def capability_ids(self):
        return frozenset(self._capabilities)

    def get_capability(self, capability_id):
        return self._capabilities[capability_id]


class PlatformCapabilitiesContractTests(unittest.TestCase):
    def test_declares_stable_unique_capability_identities(self):
        identities = {
            DOCUMENT_ENGINE_CAPABILITY,
            KNOWLEDGE_ENGINE_CAPABILITY,
            NAVIGATION_CAPABILITY,
            LOGGING_CAPABILITY,
            CLOCK_CAPABILITY,
            ID_GENERATOR_CAPABILITY,
        }

        self.assertEqual(len(identities), 6)
        self.assertTrue(
            all(identity.startswith("platform.") for identity in identities)
        )

    def test_behavioral_capabilities_are_structural(self):
        for instance, contract in (
            (Clock(), ClockCapability),
            (IdentifierGenerator(), IdGeneratorCapability),
            (Navigator(), NavigationCapability),
            (Logger(), LoggingCapability),
        ):
            with self.subTest(contract=contract.__name__):
                self.assertIsInstance(instance, Capability)
                self.assertIsInstance(instance, contract)

    def test_engine_capabilities_are_neutral_nominal_boundaries(self):
        document_engine = Engine(DOCUMENT_ENGINE_CAPABILITY)
        knowledge_engine = Engine(KNOWLEDGE_ENGINE_CAPABILITY)

        self.assertIsInstance(document_engine, DocumentEngineCapability)
        self.assertIsInstance(knowledge_engine, KnowledgeEngineCapability)

    def test_provider_exposes_capabilities_without_implementations(self):
        clock = Clock()
        provider = Provider((clock, Navigator()))

        self.assertIsInstance(provider, CapabilityProvider)
        self.assertEqual(
            provider.capability_ids,
            frozenset({CLOCK_CAPABILITY, NAVIGATION_CAPABILITY}),
        )
        self.assertIs(provider.get_capability(CLOCK_CAPABILITY), clock)

    def test_contract_has_no_qt_rsc_or_concrete_service_dependency(self):
        source = (
            Path(__file__).parents[1] / "contracts" / "capabilities.py"
        ).read_text(encoding="utf-8")

        for forbidden in (
            "PySide6",
            "applications.rsc",
            "services.",
            "database",
            "sqlite",
        ):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, source)


if __name__ == "__main__":
    unittest.main()
