"""Cognitia File Persistence P1 - Primary Provider Implementation.

Implements PersistenceProvider interface using JSON metadata, atomic snapshots, and append-only JSONL journal.
"""

from __future__ import annotations

import logging
import os
import threading
from pathlib import Path
from typing import Any

from .journal import JournalManager
from .persistence_contract import (
    DurabilityMode,
    PersistenceError,
    PersistenceProvider,
    PersistenceStatus,
    PersistenceWriteError,
)
from .persistence_models import (
    GENESIS_PREVIOUS_HASH,
    JournalRecord,
    PersistenceMetadata,
    SnapshotData,
)
from .recovery import RecoveryEngine
from .snapshot import SnapshotManager

logger = logging.getLogger("cognitia.runtime.persistence.file")


class FilePersistenceService(PersistenceProvider):
    """Durable local file persistence service for Cognitia Epistemic runtime."""

    def __init__(
        self,
        data_dir: Path | str,
        durability_mode: DurabilityMode = DurabilityMode.SYNC,
        snapshot_interval_records: int = 1000,
        max_journal_bytes: int = 268435456,
        ephemeral_mode: bool = False,
    ) -> None:
        self.data_dir = Path(data_dir)
        self.durability_mode = durability_mode
        self.snapshot_interval_records = snapshot_interval_records
        self.max_journal_bytes = max_journal_bytes
        self.ephemeral_mode = ephemeral_mode

        self.metadata_path = self.data_dir / "metadata.json"
        self.snapshot_path = self.data_dir / "state.json"
        self.journal_path = self.data_dir / "journal.jsonl"

        self._lock = threading.RLock()
        self._status = PersistenceStatus.UNINITIALIZED
        self._metadata = PersistenceMetadata()
        self._records_since_last_snapshot = 0
        self._total_writes = 0
        self._total_snapshots = 0
        self._recovered = False

        self.journal_manager = JournalManager(
            self.journal_path,
            durability_mode=self.durability_mode,
            max_journal_bytes=self.max_journal_bytes,
        )
        self.snapshot_manager = SnapshotManager(self.snapshot_path)
        self.recovery_engine = RecoveryEngine(
            self.metadata_path,
            self.snapshot_manager,
            self.journal_manager,
        )

    @property
    def status(self) -> PersistenceStatus:
        return self._status

    @property
    def is_healthy(self) -> bool:
        return self._status == PersistenceStatus.HEALTHY

    def initialize_and_recover(self) -> tuple[SnapshotData | None, list[JournalRecord]]:
        """Initialize storage directories and recover state from disk."""
        with self._lock:
            if self.ephemeral_mode:
                logger.info("Persistence initialized in EPHEMERAL mode (no disk writes)")
                self._status = PersistenceStatus.HEALTHY
                self._recovered = True
                return None, []

            try:
                self._status = PersistenceStatus.RECOVERING
                self.data_dir.mkdir(parents=True, exist_ok=True)

                metadata, snapshot, records_to_replay = self.recovery_engine.recover()
                self._metadata = metadata

                self.journal_manager.open_for_append(
                    initial_sequence=metadata.durable_sequence,
                    initial_head_hash=metadata.head_hash,
                )

                self._status = PersistenceStatus.HEALTHY
                self._recovered = True
                return snapshot, records_to_replay
            except Exception as e:
                self._status = PersistenceStatus.FAILED
                logger.exception(f"Persistence initialization/recovery failed: {e}")
                raise PersistenceError(f"Persistence initialization failed: {e}") from e

    def append_record(self, record_type: str, record_id: str, payload: dict[str, Any]) -> JournalRecord:
        """Append a record to the durable journal."""
        with self._lock:
            if self.ephemeral_mode:
                self._total_writes += 1
                return JournalRecord.create(
                    sequence=self._total_writes,
                    record_type=record_type,
                    record_id=record_id,
                    payload=payload,
                    previous_hash=self._metadata.head_hash,
                )

            if self._status != PersistenceStatus.HEALTHY:
                raise PersistenceWriteError(f"Cannot append record: Persistence status is {self._status}")

            try:
                record = self.journal_manager.append(
                    record_type=record_type,
                    record_id=record_id,
                    payload=payload,
                )

                self._metadata.durable_sequence = record.sequence
                self._metadata.head_hash = record.record_hash
                self._metadata.total_records += 1
                self._records_since_last_snapshot += 1
                self._total_writes += 1

                if self._total_writes % 50 == 0:
                    self.recovery_engine.save_metadata(self._metadata)

                return record
            except Exception as e:
                self._status = PersistenceStatus.FAILED
                logger.exception(f"Failed to persist record {record_id}: {e}")
                raise PersistenceWriteError(f"Failed to persist record: {e}") from e

    def create_snapshot(self, state: dict[str, Any], sequence: int | None = None) -> SnapshotData:
        """Save an atomic snapshot of current working state."""
        with self._lock:
            if self.ephemeral_mode:
                return SnapshotData(
                    persistence_schema_version="1.0.0",
                    runtime_abi_version="1.0.0",
                    snapshot_sequence=sequence or self._total_writes,
                    created_at="now",
                    head_hash="none",
                    state=state,
                )

            if self._status != PersistenceStatus.HEALTHY:
                raise PersistenceWriteError(f"Cannot create snapshot: Persistence status is {self._status}")

            try:
                seq = sequence if sequence is not None else self._metadata.durable_sequence
                head_hash = self._metadata.head_hash
                snapshot = self.snapshot_manager.save_snapshot(
                    state=state,
                    snapshot_sequence=seq,
                    head_hash=head_hash,
                )
                self._metadata.snapshot_sequence = seq
                self.recovery_engine.save_metadata(self._metadata)
                self._records_since_last_snapshot = 0
                self._total_snapshots += 1
                return snapshot
            except Exception as e:
                self._status = PersistenceStatus.FAILED
                logger.exception(f"Failed to create snapshot: {e}")
                raise PersistenceWriteError(f"Failed to create snapshot: {e}") from e

    def should_take_snapshot(self) -> bool:
        """Check if record count threshold for automatic snapshot has been reached."""
        return self._records_since_last_snapshot >= self.snapshot_interval_records

    def get_health(self) -> dict[str, Any]:
        """Return sanitized logical health status suitable for GET /v1/health."""
        with self._lock:
            return {
                "enabled": not self.ephemeral_mode,
                "backend": "file",
                "healthy": self.is_healthy,
                "status": self._status.value,
                "recovered": self._recovered,
                "durability": self.durability_mode.value,
                "durable_sequence": self._metadata.durable_sequence,
                "snapshot_sequence": self._metadata.snapshot_sequence,
                "journal_bytes": self.journal_manager.get_size_bytes(),
                "total_writes": self._total_writes,
                "total_snapshots": self._total_snapshots,
            }

    def flush(self) -> None:
        with self._lock:
            if not self.ephemeral_mode:
                self.journal_manager.flush()
                self.recovery_engine.save_metadata(self._metadata)

    def close(self) -> None:
        with self._lock:
            if not self.ephemeral_mode:
                self.flush()
                self.journal_manager.close()
