"""Cognitia File Persistence P1 Package.

Provides durable, deterministic, and auditable file storage for the Cognitia Epistemic runtime.
"""

from .file_persistence import FilePersistenceService
from .journal import JournalManager
from .persistence_contract import (
    DurabilityMode,
    PersistenceCorruptionError,
    PersistenceError,
    PersistenceIntegrityError,
    PersistenceProvider,
    PersistenceRecoveryError,
    PersistenceStatus,
    PersistenceWriteError,
)
from .persistence_models import (
    GENESIS_PREVIOUS_HASH,
    PERSISTENCE_SCHEMA_VERSION,
    RUNTIME_ABI_VERSION,
    JournalRecord,
    PersistenceMetadata,
    SnapshotData,
)
from .recovery import RecoveryEngine
from .snapshot import SnapshotManager

__all__ = [
    "FilePersistenceService",
    "JournalManager",
    "SnapshotManager",
    "RecoveryEngine",
    "PersistenceProvider",
    "PersistenceStatus",
    "DurabilityMode",
    "JournalRecord",
    "PersistenceMetadata",
    "SnapshotData",
    "PERSISTENCE_SCHEMA_VERSION",
    "RUNTIME_ABI_VERSION",
    "GENESIS_PREVIOUS_HASH",
    "PersistenceError",
    "PersistenceWriteError",
    "PersistenceRecoveryError",
    "PersistenceIntegrityError",
    "PersistenceCorruptionError",
]
