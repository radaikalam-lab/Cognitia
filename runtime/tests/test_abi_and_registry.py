"""Test Suite for ABI Validation, Provider Registry, and Capability Checks."""

import unittest
import uuid
import datetime
from pathlib import Path
import sys

COGNITIA_SRC = Path(__file__).resolve().parent.parent.parent / "src"
if str(COGNITIA_SRC) not in sys.path:
    sys.path.insert(0, str(COGNITIA_SRC))
RUNTIME_DIR = Path(__file__).resolve().parent.parent
if str(RUNTIME_DIR.parent) not in sys.path:
    sys.path.insert(0, str(RUNTIME_DIR.parent))

from runtime.gateway.abi_validator import ABIValidator, ABIValidationError
from runtime.gateway.provider_registry import ProviderRegistry, ProviderRecord


class TestABIRegistry(unittest.TestCase):
    def setUp(self):
        self.registry = ProviderRegistry()
        self.sample_provider = ProviderRecord(
            provider_id="thorium.browser",
            provider_name="Lean Thorium Reference Browser",
            provider_version="138.0.7204.306",
            adapter_version="1.0.0",
            supported_abi_versions=["1.0.0"],
            capabilities=[
                "observe.navigation",
                "observe.tab",
                "observe.page_metadata",
                "observe.authorized_content",
            ],
            authority_level="NONE",
            transport="local_http",
        )
        self.registry.register_provider(self.sample_provider)

    def test_valid_observation_passes(self):
        obs = {
            "id": str(uuid.uuid4()),
            "schema_version": "1.0.0",
            "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "source_id": "thorium.browser",
            "metadata": {"test": "value"},
            "payload": {"url": "https://example.com", "title": "Example"},
        }
        res = ABIValidator.validate_observation_dict(obs)
        self.assertEqual(res["id"], obs["id"])

    def test_invalid_uuid_rejected(self):
        obs = {
            "id": "not-a-uuid",
            "schema_version": "1.0.0",
            "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "source_id": "thorium.browser",
            "payload": {},
        }
        with self.assertRaises(ABIValidationError):
            ABIValidator.validate_observation_dict(obs)

    def test_invalid_schema_version_rejected(self):
        obs = {
            "id": str(uuid.uuid4()),
            "schema_version": "2.0.0",  # incompatible
            "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "source_id": "thorium.browser",
            "payload": {},
        }
        with self.assertRaises(ABIValidationError):
            ABIValidator.validate_observation_dict(obs)

    def test_invalid_timestamp_rejected(self):
        obs = {
            "id": str(uuid.uuid4()),
            "schema_version": "1.0.0",
            "created_at": "invalid-time",
            "source_id": "thorium.browser",
            "payload": {},
        }
        with self.assertRaises(ABIValidationError):
            ABIValidator.validate_observation_dict(obs)

    def test_provider_registration_and_capability_query(self):
        self.assertTrue(self.registry.is_registered("thorium.browser"))
        self.assertFalse(self.registry.is_registered("unknown.provider"))

        self.assertTrue(
            self.registry.validate_capability("thorium.browser", "observe.navigation")
        )
        self.assertTrue(
            self.registry.validate_capability("thorium.browser", "observe.authorized_content")
        )
        self.assertFalse(
            self.registry.validate_capability("thorium.browser", "execute.command")
        )
        self.assertFalse(
            self.registry.validate_capability("thorium.browser", "control.browser")
        )


if __name__ == "__main__":
    unittest.main()