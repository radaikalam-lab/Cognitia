"""End-to-End Recovery and Durability Tests for Cognitia File Persistence P1.

Tests full restart recovery, snapshot delta replay, provenance preservation,
and advisory directional proposal durability.
"""

import shutil
import tempfile
import unittest
import uuid
from pathlib import Path

from runtime.gateway.epistemic_bridge import EpistemicBridge
from runtime.persistence.file_persistence import FilePersistenceService
from runtime.persistence.persistence_contract import DurabilityMode


class TestPersistenceRecoveryE2E(unittest.TestCase):
    def setUp(self):
        self.temp_dir = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_observation_and_provenance_survives_restart(self):
        # 1. Start Initial Runtime Bridge
        ps1 = FilePersistenceService(self.temp_dir, durability_mode=DurabilityMode.SYNC)
        bridge1 = EpistemicBridge(persistence_service=ps1)

        obs_id_1 = str(uuid.uuid4())
        obs_dict_1 = {
            "id": obs_id_1,
            "schema_version": "1.0.0",
            "created_at": "2026-09-23T12:00:00Z",
            "source_id": "thorium.browser",
            "metadata": {"browser_version": "138.0"},
            "payload": {"url": "https://example.com", "title": "Example"},
        }
        res1 = bridge1.ingest_observation(obs_dict_1, "thorium.browser", "observe.navigation")
        self.assertEqual(res1["status"], "ingested")
        prov_id_1 = res1["provenance_id"]

        obs_id_2 = str(uuid.uuid4())
        obs_dict_2 = {
            "id": obs_id_2,
            "schema_version": "1.0.0",
            "created_at": "2026-09-23T12:01:00Z",
            "source_id": "thorium.browser",
            "metadata": {"user_authorized": True},
            "payload": {"extracted_text": "Sample text", "content_bytes": 11},
        }
        res2 = bridge1.ingest_observation(obs_dict_2, "thorium.browser", "observe.authorized_content")
        prov_id_2 = res2["provenance_id"]

        bridge1.close()

        # 2. Simulate Process Restart: Recreate Bridge against same directory
        ps2 = FilePersistenceService(self.temp_dir, durability_mode=DurabilityMode.SYNC)
        bridge2 = EpistemicBridge(persistence_service=ps2)

        summary = bridge2.get_status_summary()
        self.assertEqual(summary["total_ingested_observations"], 2)
        self.assertEqual(summary["active_nodes_count"], 2)

        # Verify Node 1
        node1 = bridge2.epistemic_service.get_node(obs_id_1)
        self.assertIsNotNone(node1)
        self.assertEqual(node1.content.source_id, "thorium.browser")
        self.assertEqual(node1.content.payload["title"], "Example")
        self.assertEqual(bridge2._provenance_store[prov_id_1].capability_id, "observe.navigation")

        # Verify Node 2
        node2 = bridge2.epistemic_service.get_node(obs_id_2)
        self.assertIsNotNone(node2)
        self.assertEqual(node2.content.payload["extracted_text"], "Sample text")
        self.assertEqual(bridge2._provenance_store[prov_id_2].capability_id, "observe.authorized_content")

        bridge2.close()

    def test_evidence_and_linkage_survives_restart(self):
        ps1 = FilePersistenceService(self.temp_dir, durability_mode=DurabilityMode.SYNC)
        bridge1 = EpistemicBridge(persistence_service=ps1)

        obs_id = str(uuid.uuid4())
        bridge1.ingest_observation({
            "id": obs_id,
            "schema_version": "1.0.0",
            "created_at": "2026-09-23T12:00:00Z",
            "source_id": "sensor.cam",
            "payload": {"status": "ok"},
        }, "sensor.cam", "observe.generic")

        ev_id = str(uuid.uuid4())
        bridge1.ingest_evidence({
            "id": ev_id,
            "schema_version": "1.0.0",
            "created_at": "2026-09-23T12:01:00Z",
            "target_id": obs_id,
            "direction": "SUPPORT",
            "confidence": 0.95,
            "weight": 1.0,
            "observation_ids": [obs_id],
        }, "sensor.cam", "observe.generic")

        bridge1.close()

        # Restart
        ps2 = FilePersistenceService(self.temp_dir, durability_mode=DurabilityMode.SYNC)
        bridge2 = EpistemicBridge(persistence_service=ps2)

        ev_node = bridge2.epistemic_service.get_node(ev_id)
        self.assertIsNotNone(ev_node)
        self.assertEqual(ev_node.entity_type, "evidence")
        self.assertEqual(ev_node.confidence, 0.95)

        # Target node should have associated evidence link
        target_node = bridge2.epistemic_service.get_node(obs_id)
        self.assertIn(ev_id, target_node.associated_evidence_ids)

        bridge2.close()

    def test_snapshot_plus_journal_delta_recovery(self):
        ps1 = FilePersistenceService(
            self.temp_dir,
            durability_mode=DurabilityMode.SYNC,
            snapshot_interval_records=3,  # Snapshot every 3 records
        )
        bridge1 = EpistemicBridge(persistence_service=ps1)

        # Ingest 3 records -> Triggers automatic snapshot
        ids = []
        for i in range(3):
            oid = f"obs-{i}"
            ids.append(oid)
            bridge1.ingest_observation({
                "id": oid,
                "schema_version": "1.0.0",
                "created_at": "2026-09-23T12:00:00Z",
                "source_id": "sensor",
                "payload": {"idx": i},
            }, "sensor", "observe.generic")

        # Ingest 2 more records after snapshot into journal
        for i in range(3, 5):
            oid = f"obs-{i}"
            ids.append(oid)
            bridge1.ingest_observation({
                "id": oid,
                "schema_version": "1.0.0",
                "created_at": "2026-09-23T12:00:00Z",
                "source_id": "sensor",
                "payload": {"idx": i},
            }, "sensor", "observe.generic")

        bridge1.close()

        # Restart and verify recovery of snapshot (0,1,2) + journal delta (3,4)
        ps2 = FilePersistenceService(self.temp_dir, durability_mode=DurabilityMode.SYNC)
        bridge2 = EpistemicBridge(persistence_service=ps2)

        summary = bridge2.get_status_summary()
        self.assertEqual(summary["total_ingested_observations"], 5)
        for oid in ids:
            self.assertIsNotNone(bridge2.epistemic_service.get_node(oid))

        bridge2.close()

    def test_directional_proposal_persistence_and_authority_invariant(self):
        ps1 = FilePersistenceService(self.temp_dir, durability_mode=DurabilityMode.SYNC)
        bridge1 = EpistemicBridge(persistence_service=ps1)

        spec_id = str(uuid.uuid4())
        dir_res = bridge1.ingest_directional_specification({
            "id": spec_id,
            "schema_version": "1.0.0",
            "created_at": "2026-09-23T12:00:00Z",
            "objectives": [{"description": "Damp cavity resonance"}],
        }, "acoustiforge.adapter")

        prop_id = dir_res["proposal_id"]
        self.assertEqual(dir_res["authority"], "NONE")
        bridge1.close()

        # Restart
        ps2 = FilePersistenceService(self.temp_dir, durability_mode=DurabilityMode.SYNC)
        bridge2 = EpistemicBridge(persistence_service=ps2)

        self.assertIn(prop_id, bridge2._proposals_store)
        prop = bridge2._proposals_store[prop_id]
        self.assertEqual(prop.specification_id, spec_id)
        self.assertEqual(prop.metadata.get("authority"), "NONE")

        bridge2.close()


if __name__ == "__main__":
    unittest.main()
