"""Cognitia File Persistence P1 - Data Models and Integrity Structures.

Defines the canonical journal record, metadata, and snapshot models.
Uses deterministic SHA-256 hash chaining for tamper/corruption detection.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any

from cognitia.abi.types import DeterministicSerializer

PERSISTENCE_SCHEMA_VERSION = "1.0.0"
RUNTIME_ABI_VERSION = "1.0.0"
GENESIS_PREVIOUS_HASH = "0" * 64


def current_utc_iso() -> str:
    """Return current UTC timestamp in ISO-8601 format."""
    return datetime.now(timezone.utc).isoformat()


@dataclass(frozen=True)
class JournalRecord:
    """Immutable journal entry recording a single canonical epistemic event."""

    sequence: int
    record_type: str
    record_id: str
    created_at: str
    payload: dict[str, Any]
    previous_hash: str
    record_hash: str
    schema_version: str = PERSISTENCE_SCHEMA_VERSION

    @classmethod
    def create(
        cls,
        sequence: int,
        record_type: str,
        record_id: str,
        payload: dict[str, Any],
        previous_hash: str,
        created_at: str | None = None,
    ) -> JournalRecord:
        """Create and compute hash for a new journal record."""
        ts = created_at or current_utc_iso()
        canonical_content = {
            "schema_version": PERSISTENCE_SCHEMA_VERSION,
            "sequence": sequence,
            "record_type": record_type,
            "record_id": record_id,
            "created_at": ts,
            "payload": payload,
            "previous_hash": previous_hash,
        }
        serialized_bytes = DeterministicSerializer.serialize(canonical_content).encode("utf-8")
        record_hash = hashlib.sha256(serialized_bytes).hexdigest()

        return cls(
            schema_version=PERSISTENCE_SCHEMA_VERSION,
            sequence=sequence,
            record_type=record_type,
            record_id=record_id,
            created_at=ts,
            payload=payload,
            previous_hash=previous_hash,
            record_hash=record_hash,
        )

    def verify_integrity(self) -> bool:
        """Verify that record_hash matches the canonical content calculation."""
        canonical_content = {
            "schema_version": self.schema_version,
            "sequence": self.sequence,
            "record_type": self.record_type,
            "record_id": self.record_id,
            "created_at": self.created_at,
            "payload": self.payload,
            "previous_hash": self.previous_hash,
        }
        serialized_bytes = DeterministicSerializer.serialize(canonical_content).encode("utf-8")
        expected_hash = hashlib.sha256(serialized_bytes).hexdigest()
        return self.record_hash == expected_hash

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def to_json_line(self) -> str:
        return DeterministicSerializer.serialize(self.to_dict()) + "\n"

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> JournalRecord:
        return cls(
            schema_version=data.get("schema_version", PERSISTENCE_SCHEMA_VERSION),
            sequence=int(data["sequence"]),
            record_type=str(data["record_type"]),
            record_id=str(data["record_id"]),
            created_at=str(data["created_at"]),
            payload=dict(data.get("payload", {})),
            previous_hash=str(data.get("previous_hash", GENESIS_PREVIOUS_HASH)),
            record_hash=str(data["record_hash"]),
        )


@dataclass
class PersistenceMetadata:
    """Persistent metadata describing the database state and sequence counters."""

    persistence_schema_version: str = PERSISTENCE_SCHEMA_VERSION
    runtime_abi_version: str = RUNTIME_ABI_VERSION
    created_at: str = field(default_factory=current_utc_iso)
    last_updated_at: str = field(default_factory=current_utc_iso)
    durable_sequence: int = 0
    snapshot_sequence: int = 0
    genesis_hash: str = GENESIS_PREVIOUS_HASH
    head_hash: str = GENESIS_PREVIOUS_HASH
    total_records: int = 0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> PersistenceMetadata:
        return cls(
            persistence_schema_version=data.get("persistence_schema_version", PERSISTENCE_SCHEMA_VERSION),
            runtime_abi_version=data.get("runtime_abi_version", RUNTIME_ABI_VERSION),
            created_at=data.get("created_at", current_utc_iso()),
            last_updated_at=data.get("last_updated_at", current_utc_iso()),
            durable_sequence=int(data.get("durable_sequence", 0)),
            snapshot_sequence=int(data.get("snapshot_sequence", 0)),
            genesis_hash=data.get("genesis_hash", GENESIS_PREVIOUS_HASH),
            head_hash=data.get("head_hash", GENESIS_PREVIOUS_HASH),
            total_records=int(data.get("total_records", 0)),
        )


@dataclass(frozen=True)
class SnapshotData:
    """Durable consistent snapshot containing the full working epistemic state."""

    persistence_schema_version: str
    runtime_abi_version: str
    snapshot_sequence: int
    created_at: str
    head_hash: str
    state: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> SnapshotData:
        return cls(
            persistence_schema_version=data.get("persistence_schema_version", PERSISTENCE_SCHEMA_VERSION),
            runtime_abi_version=data.get("runtime_abi_version", RUNTIME_ABI_VERSION),
            snapshot_sequence=int(data.get("snapshot_sequence", 0)),
            created_at=str(data.get("created_at", current_utc_iso())),
            head_hash=str(data.get("head_hash", GENESIS_PREVIOUS_HASH)),
            state=dict(data.get("state", {})),
        )
