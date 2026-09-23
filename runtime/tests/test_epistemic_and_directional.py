"""Test Suite for Epistemic Ingestion, Provenance Preservation, and Directional Specs."""

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

from runtime.gateway.epistemic_bridge import EpistemicBridge
from cognitia.epistemic.service import InMemoryEpistemicService
from cognitia.abi.types import DeterministicSerializer


class TestEpistemicDirectional(unittest.TestCase):
    def setUp(self):
        self.service = InMemoryEpistemicService()
        self.bridge = EpistemicBridge(self.service)

    def test_observation_ingestion_and_provenance(self):
        obs_id = str(uuid.uuid4())
        created_at = datetime.datetime.now(datetime.timezone.utc).isoformat()
        obs_dict = {
            "id": obs_id,
            "schema_version": "1.0.0",
            "created_at": created_at,
            "source_id": "thorium.browser",
            "metadata": {"capability": "observe.navigation"},
            "payload": {
                "url": "https://example.com/test",
                "title": "Test Page",
                "http_status": 200,
            },
        }

        res = self.bridge.ingest_observation(
            obs_dict, provider_id="thorium.browser", capability="observe.navigation"
        )
        self.assertEqual(res["status"], "ingested")
        self.assertEqual(res["entity_id"], obs_id)
        self.assertIsNotNone(res["provenance_id"])

        # Validate node in epistemic service
        node = self.service.get_node(res["node_id"])
        self.assertIsNotNone(node)
        self.assertEqual(node.node_id, obs_id)
        self.assertEqual(node.content.metadata["provenance_producer"], "thorium.browser")

    def test_evidence_ingestion_canonical(self):
        ev_id = str(uuid.uuid4())
        created_at = datetime.datetime.now(datetime.timezone.utc).isoformat()
        ev_dict = {
            "id": ev_id,
            "schema_version": "1.0.0",
            "created_at": created_at,
            "target_id": "hypo-12345",
            "direction": "SUPPORT",
            "confidence": 0.95,
            "weight": 1.0,
            "observation_ids": ["obs-1", "obs-2"],
            "metadata": {"source": "thorium"},
        }

        res = self.bridge.ingest_evidence(
            ev_dict, provider_id="thorium.browser", capability="observe.authorized_content"
        )
        self.assertEqual(res["status"], "ingested")
        self.assertEqual(res["entity_type"], "evidence")
        self.assertEqual(res["entity_id"], ev_id)
        self.assertEqual(res["target_id"], "hypo-12345")

        node = self.service.get_node(res["node_id"])
        self.assertIsNotNone(node)
        self.assertEqual(node.entity_type, "evidence")

    def test_directional_specification_is_strictly_advisory(self):
        spec_id = str(uuid.uuid4())
        spec_dict = {
            "id": spec_id,
            "schema_version": "1.0.0",
            "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "objectives": [{"description": "Investigate acoustic resonance damping"}],
            "constraints": [{"description": "No direct file modification"}],
            "success_criteria": [{"metric": "residual_reduction", "threshold": 0.05}],
        }

        proposal = self.bridge.ingest_directional_specification(
            spec_dict, provider_id="acoustiforge.adapter"
        )
        self.assertEqual(proposal["proposal_status"], "proposed")
        self.assertEqual(proposal["authority"], "NONE")
        self.assertIn("Epistemic Novelty != Production Authority", proposal["message"])

    def test_deterministic_serialization(self):
        data = {"z": 10, "a": 20, "nested": {"b": 2, "a": 1}}
        ser1 = DeterministicSerializer.serialize(data)
        ser2 = DeterministicSerializer.serialize(data)
        self.assertEqual(ser1, ser2)
        self.assertIn('{"a":20', ser1)


if __name__ == "__main__":
    unittest.main()