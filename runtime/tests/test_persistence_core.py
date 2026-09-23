"""Unit tests for Cognitia File Persistence P1 Core Mechanisms.

Tests JournalManager, Hash Chaining, SnapshotManager, and Truncated Tail Repair.
"""

import json
import shutil
import tempfile
import unittest
from pathlib import Path

from runtime.persistence.journal import JournalManager
from runtime.persistence.persistence_contract import (
    DurabilityMode,
    PersistenceCorruptionError,
    PersistenceIntegrityError,
    PersistenceWriteError,
)
from runtime.persistence.persistence_models import (
    GENESIS_PREVIOUS_HASH,
    PERSISTENCE_SCHEMA_VERSION,
    JournalRecord,
    PersistenceMetadata,
)
from runtime.persistence.snapshot import SnapshotManager


class TestPersistenceCore(unittest.TestCase):
    def setUp(self):
        self.temp_dir = Path(tempfile.mkdtemp())
        self.journal_path = self.temp_dir / "journal.jsonl"
        self.snapshot_path = self.temp_dir / "state.json"

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_journal_append_and_hash_chain(self):
        jm = JournalManager(self.journal_path, durability_mode=DurabilityMode.SYNC)
        jm.open_for_append()

        rec1 = jm.append("observation", "obs-001", {"value": 42})
        self.assertEqual(rec1.sequence, 1)
        self.assertEqual(rec1.previous_hash, GENESIS_PREVIOUS_HASH)
        self.assertTrue(rec1.verify_integrity())

        rec2 = jm.append("observation", "obs-002", {"value": 84})
        self.assertEqual(rec2.sequence, 2)
        self.assertEqual(rec2.previous_hash, rec1.record_hash)
        self.assertTrue(rec2.verify_integrity())

        jm.close()

        # Reopen and read back
        jm_reader = JournalManager(self.journal_path)
        records, truncated = jm_reader.read_all_records()
        self.assertFalse(truncated)
        self.assertEqual(len(records), 2)
        self.assertEqual(records[0].record_id, "obs-001")
        self.assertEqual(records[1].record_id, "obs-002")

    def test_hash_chain_tamper_detection(self):
        jm = JournalManager(self.journal_path, durability_mode=DurabilityMode.SYNC)
        jm.open_for_append()
        jm.append("observation", "obs-001", {"data": "clean"})
        jm.append("observation", "obs-002", {"data": "clean"})
        jm.close()

        # Tamper with the first line in the journal
        with open(self.journal_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        tampered_data = json.loads(lines[0])
        tampered_data["payload"]["data"] = "tampered_by_attacker"
        lines[0] = json.dumps(tampered_data) + "\n"

        with open(self.journal_path, "w", encoding="utf-8") as f:
            f.writelines(lines)

        jm_reader = JournalManager(self.journal_path)
        with self.assertRaises(PersistenceIntegrityError):
            jm_reader.read_all_records()

    def test_broken_hash_chain_detection(self):
        jm = JournalManager(self.journal_path, durability_mode=DurabilityMode.SYNC)
        jm.open_for_append()
        rec1 = jm.append("observation", "obs-001", {"data": "1"})
        rec2 = jm.append("observation", "obs-002", {"data": "2"})
        jm.close()

        # Modify previous_hash of second record
        with open(self.journal_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        tampered_data = json.loads(lines[1])
        tampered_data["previous_hash"] = "0" * 64
        lines[1] = json.dumps(tampered_data) + "\n"

        with open(self.journal_path, "w", encoding="utf-8") as f:
            f.writelines(lines)

        jm_reader = JournalManager(self.journal_path)
        with self.assertRaises((PersistenceIntegrityError, PersistenceCorruptionError)):
            jm_reader.read_all_records()

    def test_truncated_tail_recovery(self):
        jm = JournalManager(self.journal_path, durability_mode=DurabilityMode.SYNC)
        jm.open_for_append()
        rec1 = jm.append("observation", "obs-001", {"data": "complete1"})
        rec2 = jm.append("observation", "obs-002", {"data": "complete2"})
        jm.close()

        # Append corrupted/incomplete line simulating power cut during write
        with open(self.journal_path, "a", encoding="utf-8") as f:
            f.write('{"sequence": 3, "record_type": "observation", "record_id": "incomplete')

        jm_reader = JournalManager(self.journal_path)
        records, truncated = jm_reader.read_all_records()
        self.assertTrue(truncated)
        self.assertEqual(len(records), 2)

        # Repair journal
        jm_reader.repair_truncated_tail(records)
        clean_records, clean_truncated = jm_reader.read_all_records()
        self.assertFalse(clean_truncated)
        self.assertEqual(len(clean_records), 2)

    def test_snapshot_atomic_write_and_load(self):
        sm = SnapshotManager(self.snapshot_path)
        test_state = {
            "observations": [{"id": "obs-1", "source": "sensor"}],
            "evidence": [{"id": "ev-1", "target": "obs-1"}],
        }

        snap = sm.save_snapshot(test_state, snapshot_sequence=50, head_hash="abc123hash")
        self.assertEqual(snap.snapshot_sequence, 50)
        self.assertTrue(self.snapshot_path.exists())

        loaded = sm.load_snapshot()
        self.assertIsNotNone(loaded)
        self.assertEqual(loaded.snapshot_sequence, 50)
        self.assertEqual(loaded.head_hash, "abc123hash")
        self.assertEqual(loaded.state["observations"][0]["id"], "obs-1")

    def test_corrupted_snapshot_handling(self):
        sm = SnapshotManager(self.snapshot_path)
        sm.save_snapshot({"key": "val"}, snapshot_sequence=10)

        # Corrupt snapshot file with garbage
        with open(self.snapshot_path, "w", encoding="utf-8") as f:
            f.write("CORRUPTED_NON_JSON_DATA")

        with self.assertRaises(PersistenceCorruptionError):
            sm.load_snapshot()


if __name__ == "__main__":
    unittest.main()
