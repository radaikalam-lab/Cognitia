"""Cognitia File Persistence P1 - State Recovery Engine.

Coordinates reading metadata, snapshot state, and replaying journal delta.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from .journal import JournalManager
from .persistence_contract import (
    PersistenceCorruptionError,
    PersistenceIntegrityError,
    PersistenceRecoveryError,
)
from .persistence_models import (
    GENESIS_PREVIOUS_HASH,
    PERSISTENCE_SCHEMA_VERSION,
    JournalRecord,
    PersistenceMetadata,
    SnapshotData,
    current_utc_iso,
)
from .snapshot import SnapshotManager

logger = logging.getLogger("cognitia.runtime.persistence.recovery")


class RecoveryEngine:
    """Reconstructs canonical working state from durable snapshot and journal records."""

    def __init__(
        self,
        metadata_path: Path,
        snapshot_manager: SnapshotManager,
        journal_manager: JournalManager,
    ) -> None:
        self.metadata_path = metadata_path
        self.snapshot_manager = snapshot_manager
        self.journal_manager = journal_manager

    def load_metadata(self) -> PersistenceMetadata:
        """Load metadata or initialize genesis metadata if none exists."""
        if not self.metadata_path.exists() or self.metadata_path.stat().st_size == 0:
            return PersistenceMetadata()

        try:
            with open(self.metadata_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return PersistenceMetadata.from_dict(data)
        except Exception as e:
            logger.warning(f"Metadata file corrupted or unreadable: {e}, falling back to derivation")
            return PersistenceMetadata()

    def save_metadata(self, meta: PersistenceMetadata) -> None:
        """Persist metadata to disk atomically."""
        self.metadata_path.parent.mkdir(parents=True, exist_ok=True)
        meta.last_updated_at = current_utc_iso()
        temp_path = self.metadata_path.with_suffix(".json.tmp")
        with open(temp_path, "w", encoding="utf-8") as f:
            json.dump(meta.to_dict(), f, indent=2, sort_keys=True)
            f.flush()
        temp_path.replace(self.metadata_path)

    def recover(self) -> tuple[PersistenceMetadata, SnapshotData | None, list[JournalRecord]]:
        """Execute deterministic recovery.

        Returns (metadata, snapshot, post_snapshot_records_to_replay).
        """
        logger.info("Starting Cognitia Persistence Recovery...")

        metadata = self.load_metadata()

        # 1. Load Snapshot if present
        snapshot = self.snapshot_manager.load_snapshot()
        snapshot_sequence = snapshot.snapshot_sequence if snapshot else 0
        snapshot_head_hash = snapshot.head_hash if snapshot else GENESIS_PREVIOUS_HASH

        # 2. Read and validate full journal
        journal_records, truncated_tail = self.journal_manager.read_all_records()
        if truncated_tail:
            logger.warning("Detected truncated tail during journal recovery. Repairing journal file...")
            self.journal_manager.repair_truncated_tail(journal_records)

        # 3. If snapshot exists, verify journal continuity from snapshot_sequence
        records_to_replay: list[JournalRecord] = []
        if snapshot:
            if journal_records:
                for rec in journal_records:
                    if rec.sequence > snapshot_sequence:
                        records_to_replay.append(rec)
                    elif rec.sequence == snapshot_sequence:
                        if rec.record_hash != snapshot_head_hash:
                            raise PersistenceIntegrityError(
                                f"Snapshot head hash ({snapshot_head_hash}) does not match journal record hash at sequence {snapshot_sequence} ({rec.record_hash})"
                            )
        else:
            records_to_replay = list(journal_records)

        # 4. Compute durable sequence and head hash
        if journal_records:
            durable_sequence = journal_records[-1].sequence
            head_hash = journal_records[-1].record_hash
            total_records = len(journal_records)
        elif snapshot:
            durable_sequence = snapshot.snapshot_sequence
            head_hash = snapshot.head_hash
            total_records = snapshot.snapshot_sequence
        else:
            durable_sequence = 0
            head_hash = GENESIS_PREVIOUS_HASH
            total_records = 0

        metadata.durable_sequence = durable_sequence
        metadata.snapshot_sequence = snapshot_sequence
        metadata.head_hash = head_hash
        metadata.total_records = total_records
        self.save_metadata(metadata)

        logger.info(
            f"Recovery completed successfully: snapshot_seq={snapshot_sequence}, durable_seq={durable_sequence}, records_to_replay={len(records_to_replay)}"
        )
        return metadata, snapshot, records_to_replay
