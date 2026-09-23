"""Cognitia File Persistence P1 - Append-Only Journal Engine.

Manages sequential append, flush/fsync durability, and hash-chain validation.
Handles truncated tail recovery from ungraceful process termination.
"""

from __future__ import annotations

import json
import logging
import os
import threading
from pathlib import Path
from typing import Any

from .persistence_contract import (
    DurabilityMode,
    PersistenceCorruptionError,
    PersistenceIntegrityError,
    PersistenceWriteError,
)
from .persistence_models import (
    GENESIS_PREVIOUS_HASH,
    JournalRecord,
    PersistenceMetadata,
)

logger = logging.getLogger("cognitia.runtime.persistence.journal")


class JournalManager:
    """Thread-safe, append-only journal manager enforcing sequential hash chaining."""

    def __init__(
        self,
        journal_path: Path,
        durability_mode: DurabilityMode = DurabilityMode.SYNC,
        max_journal_bytes: int = 268435456,  # 256 MB
    ) -> None:
        self.journal_path = journal_path
        self.durability_mode = durability_mode
        self.max_journal_bytes = max_journal_bytes
        self._lock = threading.RLock()
        self._file_handle: Any = None
        self._current_sequence: int = 0
        self._head_hash: str = GENESIS_PREVIOUS_HASH

    def open_for_append(self, initial_sequence: int = 0, initial_head_hash: str = GENESIS_PREVIOUS_HASH) -> None:
        """Open the journal file in append mode and initialize sequence/hash state."""
        with self._lock:
            self.journal_path.parent.mkdir(parents=True, exist_ok=True)
            self._current_sequence = initial_sequence
            self._head_hash = initial_head_hash
            self._file_handle = open(self.journal_path, "a", encoding="utf-8")

    def append(self, record_type: str, record_id: str, payload: dict[str, Any]) -> JournalRecord:
        """Create, hash, and persist a new journal record according to durability mode."""
        with self._lock:
            if not self._file_handle or self._file_handle.closed:
                raise PersistenceWriteError("Journal file handle is closed or unavailable")

            next_sequence = self._current_sequence + 1
            record = JournalRecord.create(
                sequence=next_sequence,
                record_type=record_type,
                record_id=record_id,
                payload=payload,
                previous_hash=self._head_hash,
            )

            try:
                line = record.to_json_line()
                self._file_handle.write(line)
                self._file_handle.flush()
                if self.durability_mode == DurabilityMode.SYNC:
                    try:
                        os.fsync(self._file_handle.fileno())
                    except (AttributeError, OSError) as e:
                        logger.debug(f"fsync not supported or failed on platform: {e}")

                self._current_sequence = next_sequence
                self._head_hash = record.record_hash
                return record
            except Exception as e:
                logger.exception(f"Failed to write journal record {next_sequence}: {e}")
                raise PersistenceWriteError(f"Failed to write journal record: {e}") from e

    def read_all_records(self) -> tuple[list[JournalRecord], bool]:
        """Read and validate all journal records from disk.

        Returns (records, truncated_tail_detected).
        Raises PersistenceCorruptionError if middle-record corruption is found.
        """
        with self._lock:
            if not self.journal_path.exists() or self.journal_path.stat().st_size == 0:
                return [], False

            records: list[JournalRecord] = []
            expected_sequence = 1
            expected_prev_hash = GENESIS_PREVIOUS_HASH
            truncated_tail_detected = False

            with open(self.journal_path, "r", encoding="utf-8", errors="replace") as f:
                lines = f.readlines()

            total_lines = len(lines)
            for idx, line in enumerate(lines):
                line_str = line.strip()
                if not line_str:
                    continue

                try:
                    data = json.loads(line_str)
                except Exception as e:
                    if idx == total_lines - 1:
                        logger.warning(f"Truncated/incomplete final journal record detected on line {idx + 1}: {e}")
                        truncated_tail_detected = True
                        break
                    else:
                        raise PersistenceCorruptionError(
                            f"Corrupted journal record at line {idx + 1}: Invalid JSON ({e})"
                        )

                record = JournalRecord.from_dict(data)

                # Validate sequence monotonicity
                if record.sequence != expected_sequence:
                    if idx == total_lines - 1:
                        logger.warning(f"Sequence mismatch on final line ({record.sequence} != {expected_sequence})")
                        truncated_tail_detected = True
                        break
                    raise PersistenceCorruptionError(
                        f"Sequence gap/mismatch at line {idx + 1}: expected {expected_sequence}, got {record.sequence}"
                    )

                # Validate hash chain
                if record.previous_hash != expected_prev_hash:
                    raise PersistenceIntegrityError(
                        f"Broken hash chain at sequence {record.sequence}: expected prev {expected_prev_hash}, got {record.previous_hash}"
                    )

                # Validate record self-hash integrity
                if not record.verify_integrity():
                    raise PersistenceIntegrityError(
                        f"Record integrity check failed for sequence {record.sequence} (hash mismatch)"
                    )

                records.append(record)
                expected_sequence += 1
                expected_prev_hash = record.record_hash

            return records, truncated_tail_detected

    def repair_truncated_tail(self, valid_records: list[JournalRecord]) -> None:
        """Rewrite journal file with only validated records after truncated tail detection."""
        with self._lock:
            if self._file_handle and not self._file_handle.closed:
                self._file_handle.close()

            temp_path = self.journal_path.with_suffix(".jsonl.repair_tmp")
            with open(temp_path, "w", encoding="utf-8") as f:
                for rec in valid_records:
                    f.write(rec.to_json_line())
                f.flush()
                try:
                    os.fsync(f.fileno())
                except (AttributeError, OSError):
                    pass

            os.replace(temp_path, self.journal_path)
            logger.info(f"Repaired journal file with {len(valid_records)} valid records")

    def get_size_bytes(self) -> int:
        """Return current journal file size in bytes."""
        if self.journal_path.exists():
            return self.journal_path.stat().st_size
        return 0

    def flush(self) -> None:
        with self._lock:
            if self._file_handle and not self._file_handle.closed:
                self._file_handle.flush()

    def close(self) -> None:
        with self._lock:
            if self._file_handle and not self._file_handle.closed:
                self._file_handle.flush()
                self._file_handle.close()
                self._file_handle = None
