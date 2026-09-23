"""Cognitia File Persistence P1 - Storage Contract and Status Definitions.

Defines the protocol interface for durable persistence providers.
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Protocol, runtime_checkable

from .persistence_models import (
    JournalRecord,
    PersistenceMetadata,
    SnapshotData,
)


class PersistenceStatus(str, Enum):
    """Operational status of the persistence layer."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    FAILED = "failed"
    RECOVERING = "recovering"
    UNINITIALIZED = "uninitialized"


class DurabilityMode(str, Enum):
    """Durability synchronization mode."""

    SYNC = "sync"      # Write + Flush + fsync before acknowledgment
    ASYNC = "async"    # Write + Flush without blocking fsync
    NONE = "none"      # Ephemeral in-memory (test/dev only)


class PersistenceError(Exception):
    """Base exception for all persistence failures."""
    pass


class PersistenceWriteError(PersistenceError):
    """Raised when a durable write operation fails."""
    pass


class PersistenceRecoveryError(PersistenceError):
    """Raised when recovering from persisted data fails."""
    pass


class PersistenceIntegrityError(PersistenceError):
    """Raised when hash chain or checksum verification fails."""
    pass


class PersistenceCorruptionError(PersistenceError):
    """Raised when non-recoverable corruption is detected in storage files."""
    pass


@runtime_checkable
class PersistenceProvider(Protocol):
    """Protocol defining the narrow storage contract for Cognitia durable backends."""

    def append_record(self, record_type: str, record_id: str, payload: dict[str, Any]) -> JournalRecord:
        """Persist one canonical immutable journal record."""
        ...

    def create_snapshot(self, state: dict[str, Any], sequence: int | None = None) -> SnapshotData:
        """Persist a consistent snapshot of recoverable working state."""
        ...

    def initialize_and_recover(self) -> tuple[SnapshotData | None, list[JournalRecord]]:
        """Reconstruct working state from snapshot + post-snapshot journal records."""
        ...

    def get_health(self) -> dict[str, Any]:
        """Return persistence health, metrics, and durability status."""
        ...

    def flush(self) -> None:
        """Flush pending writes to persistent storage."""
        ...

    def close(self) -> None:
        """Safely close open file handles."""
        ...
