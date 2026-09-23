"""Concurrency and Security Invariant Tests for Cognitia File Persistence P1.

Tests multithreaded concurrent ingestion, no secret leakage in persistence files,
and strict rejection on persistence failure (no silent fallback to memory).
"""

import concurrent.futures
import json
import shutil
import tempfile
import unittest
import uuid
from pathlib import Path

from runtime.gateway.epistemic_bridge import EpistemicBridge
from runtime.persistence.file_persistence import FilePersistenceService
from runtime.persistence.persistence_contract import (
    DurabilityMode,
    PersistenceStatus,
    PersistenceWriteError,
)


class TestPersistenceConcurrencyAndSecurity(unittest.TestCase):
    def setUp(self):
        self.temp_dir = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_concurrent_multithreaded_ingestion(self):
        ps = FilePersistenceService(self.temp_dir, durability_mode=DurabilityMode.SYNC)
        bridge = EpistemicBridge(persistence_service=ps)

        num_threads = 10
        ops_per_thread = 50
        total_ops = num_threads * ops_per_thread

        def worker(thread_idx: int):
            for i in range(ops_per_thread):
                obs_id = f"thread-{thread_idx}-obs-{i}"
                bridge.ingest_observation({
                    "id": obs_id,
                    "schema_version": "1.0.0",
                    "created_at": "2026-09-23T12:00:00Z",
                    "source_id": f"provider-{thread_idx}",
                    "payload": {"val": i},
                }, f"provider-{thread_idx}", "observe.generic")

        with concurrent.futures.ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [executor.submit(worker, t) for t in range(num_threads)]
            for f in futures:
                f.result()

        bridge.close()

        # Verify journal integrity
        ps_check = FilePersistenceService(self.temp_dir, durability_mode=DurabilityMode.SYNC)
        bridge_check = EpistemicBridge(persistence_service=ps_check)
        summary = bridge_check.get_status_summary()

        self.assertEqual(summary["total_ingested_observations"], total_ops)
        self.assertEqual(summary["active_nodes_count"], total_ops)
        self.assertEqual(summary["persistence"]["durable_sequence"], total_ops)
        self.assertTrue(summary["persistence"]["healthy"])
        bridge_check.close()

    def test_no_prohibited_secrets_persisted(self):
        ps = FilePersistenceService(self.temp_dir, durability_mode=DurabilityMode.SYNC)
        bridge = EpistemicBridge(persistence_service=ps)

        bridge.ingest_observation({
            "id": str(uuid.uuid4()),
            "schema_version": "1.0.0",
            "created_at": "2026-09-23T12:00:00Z",
            "source_id": "sensor",
            "payload": {"metric": "temperature", "temp": 24.5},
        }, "sensor", "observe.generic")
        bridge.close()

        # Audit journal contents
        journal_path = self.temp_dir / "journal.jsonl"
        with open(journal_path, "r", encoding="utf-8") as f:
            content = f.read()

        forbidden = ["password", "secret", "bearer", "authorization", "auth_token", "cookie"]
        for word in forbidden:
            self.assertNotIn(f'"{word}"', content.lower())

    def test_persistence_failure_rejects_writes_no_silent_memory_fallback(self):
        # Create service with an unwritable/uncreatable directory simulation
        bad_dir = self.temp_dir / "blocked_file"
        # Create a file where directory is expected
        with open(bad_dir, "w", encoding="utf-8") as f:
            f.write("I_AM_A_FILE_NOT_A_DIR")

        invalid_subpath = bad_dir / "sub" / "epistemic"

        with self.assertRaises(Exception):
            ps = FilePersistenceService(invalid_subpath, durability_mode=DurabilityMode.SYNC)
            bridge = EpistemicBridge(persistence_service=ps)
            bridge.ingest_observation({
                "id": "should_fail",
                "schema_version": "1.0.0",
                "source_id": "sensor",
                "payload": {},
            }, "sensor", "observe.generic")


if __name__ == "__main__":
    unittest.main()
