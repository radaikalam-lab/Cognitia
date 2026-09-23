"""Integration Test using Reference Thorium Browser Payloads."""

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

from runtime.gateway.abi_validator import ABIValidator
from runtime.gateway.provider_registry import ProviderRegistry, ProviderRecord
from runtime.gateway.security import SecuritySanitizer
from runtime.gateway.epistemic_bridge import EpistemicBridge
from cognitia.epistemic.service import InMemoryEpistemicService


class TestThoriumReference(unittest.TestCase):
    def setUp(self):
        self.config_dir = RUNTIME_DIR / "config"
        self.registry = ProviderRegistry(self.config_dir / "provider_whitelist.json")
        self.epistemic = InMemoryEpistemicService()
        self.bridge = EpistemicBridge(self.epistemic)

    def test_thorium_phase3a_navigation_observation(self):
        nav_payload = {
            "id": str(uuid.uuid4()),
            "schema_version": "1.0.0",
            "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "source_id": "thorium.browser",
            "metadata": {
                "capability": "observe.navigation",
                "browser_version": "138.0.7204.306",
                "adapter_version": "1.0.0",
            },
            "payload": {
                "tab_id": 42,
                "url": "https://github.com/Alex313031/Thorium",
                "title": "GitHub - Alex313031/Thorium",
                "transition_type": "typed",
            },
        }

        # Validate against registry & capability
        self.assertTrue(self.registry.is_registered("thorium.browser"))
        self.assertTrue(
            self.registry.validate_capability("thorium.browser", "observe.navigation")
        )

        # Validate ABI
        ABIValidator.validate_observation_dict(nav_payload)

        # Sanitize
        sanitized = SecuritySanitizer.sanitize_observation_payload(
            nav_payload["payload"], "thorium.browser"
        )
        nav_payload["payload"] = sanitized

        # Ingest
        res = self.bridge.ingest_observation(
            nav_payload, "thorium.browser", "observe.navigation"
        )
        self.assertEqual(res["status"], "ingested")

    def test_thorium_phase3b_authorized_content_extraction(self):
        content_payload = {
            "id": str(uuid.uuid4()),
            "schema_version": "1.0.0",
            "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "source_id": "thorium.browser",
            "metadata": {
                "capability": "observe.authorized_content",
                "browser_version": "138.0.7204.306",
                "user_explicitly_authorized": True,
            },
            "payload": {
                "tab_id": 42,
                "url": "https://arxiv.org/abs/2301.00000",
                "title": "Quantum Epistemics Paper",
                "extracted_text": "This paper presents a formal analysis of epistemic closures...",
                "content_bytes": 1024,
            },
        }

        # Validate capability
        self.assertTrue(
            self.registry.validate_capability("thorium.browser", "observe.authorized_content")
        )

        # Validate ABI
        ABIValidator.validate_observation_dict(content_payload)

        # Sanitize
        sanitized = SecuritySanitizer.sanitize_observation_payload(
            content_payload["payload"], "thorium.browser"
        )
        content_payload["payload"] = sanitized

        # Verify untrusted tag is applied
        self.assertTrue(sanitized.get("is_untrusted_external_content"))

        # Ingest
        res = self.bridge.ingest_observation(
            content_payload, "thorium.browser", "observe.authorized_content"
        )
        self.assertEqual(res["status"], "ingested")


if __name__ == "__main__":
    unittest.main()