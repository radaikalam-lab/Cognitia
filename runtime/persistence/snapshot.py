"""Cognitia File Persistence P1 - Atomic Snapshot Manager.

Handles consistent snapshot generation and atomic file replacement using temporary files.
"""

from __future__ import annotations

import json
import logging
import os
import threading
import uuid
from pathlib import Path
from typing import Any

from cognitia.abi.types import DeterministicSerializer

from .persistence_contract import (
    PersistenceCorruptionError,
    PersistenceIntegrityError,
    PersistenceWriteError,
)
from .persistence_models import (
    GENESIS_PREVIOUS_HASH,
    PERSISTENCE_SCHEMA_VERSION,
    RUNTIME_ABI_VERSION,
    SnapshotData,
    current_utc_iso,
)

logger = logging.getLogger("cognitia.runtime.persistence.snapshot")


class SnapshotManager:
    """Manages atomic writing and loading of consistent state snapshots."""

    def __init__(self, snapshot_path: Path) -> None:
        self.snapshot_path = snapshot_path
        self._lock = threading.RLock()

    def save_snapshot(
        self,
        state: dict[str, Any],
        snapshot_sequence: int,
        head_hash: str = GENESIS_PREVIOUS_HASH,
    ) -> SnapshotData:
        """Atomically write a snapshot using a temporary file and os.replace."""
        with self._lock:
            snapshot = SnapshotData(
                persistence_schema_version=PERSISTENCE_SCHEMA_VERSION,
                runtime_abi_version=RUNTIME_ABI_VERSION,
                snapshot_sequence=snapshot_sequence,
                created_at=current_utc_iso(),
                head_hash=head_hash,
                state=state,
            )

            self.snapshot_path.parent.mkdir(parents=True, exist_ok=True)
            temp_path = self.snapshot_path.with_name(f"{self.snapshot_path.name}.tmp.{uuid.uuid4().hex}")

            try:
                serialized_json = DeterministicSerializer.serialize(snapshot.to_dict())
                with open(temp_path, "w", encoding="utf-8") as f:
                    f.write(serialized_json)
                    f.flush()
                    try:
                        os.fsync(f.fileno())
                    except (AttributeError, OSError) as e:
                        logger.debug(f"fsync not supported or failed on temp snapshot: {e}")

                os.replace(temp_path, self.snapshot_path)
                logger.info(f"Saved atomic snapshot at sequence {snapshot_sequence}")
                return snapshot
            except Exception as e:
                if temp_path.exists():
                    try:
                        temp_path.unlink()
                    except OSError:
                        pass
                logger.exception(f"Failed to write snapshot: {e}")
                raise PersistenceWriteError(f"Failed to write snapshot: {e}") from e

    def load_snapshot(self) -> SnapshotData | None:
        """Load and validate the snapshot file from disk."""
        with self._lock:
            if not self.snapshot_path.exists() or self.snapshot_path.stat().st_size == 0:
                return None

            try:
                with open(self.snapshot_path, "r", encoding="utf-8") as f:
                    data = json.load(f)

                schema_ver = data.get("persistence_schema_version")
                if schema_ver != PERSISTENCE_SCHEMA_VERSION:
                    raise PersistenceIntegrityError(
                        f"Unsupported snapshot schema version: {schema_ver} (expected {PERSISTENCE_SCHEMA_VERSION})"
                    )

                return SnapshotData.from_dict(data)
            except json.JSONDecodeError as e:
                raise PersistenceCorruptionError(f"Corrupted snapshot JSON in {self.snapshot_path}: {e}") from e
            except Exception as e:
                if isinstance(e, (PersistenceIntegrityError, PersistenceCorruptionError)):
                    raise
                raise PersistenceCorruptionError(f"Failed to load snapshot: {e}") from e
