"""Cognitia Provenance Module.

Implements immutable provenance tracking, lineage graph queries,
and cryptographic checksumming.
"""

from __future__ import annotations

import enum
import hashlib
from dataclasses import dataclass, field
from typing import Any

from cognitia.abi.types import (
    SCHEMA_VERSION_V1,
    CognitiveObject,
    DeterministicSerializer,
    current_utc_timestamp,
    generate_entity_id,
)


class SourceType(str, enum.Enum):
    """Categorization of the entity/process producing a cognitive artifact."""

    HUMAN = "human"
    DETERMINISTIC_RULE = "deterministic_rule"
    ML_MODEL = "ml_model"
    NEURAL_MODEL = "neural_model"
    REASONING_ENGINE = "reasoning_engine"
    SENSOR = "sensor"
    COMPOSITE = "composite"


def compute_checksum(data: Any) -> str:
    """Compute deterministic SHA-256 checksum over serialized data representation."""
    canonical_json = DeterministicSerializer.serialize(data)
    return hashlib.sha256(canonical_json.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class ProvenanceRecord(CognitiveObject):
    """Immutable provenance record tracking lineage, producer, model, and checksums."""

    source_type: SourceType = SourceType.DETERMINISTIC_RULE
    producer_id: str = "cognitia_core"
    capability_id: str | None = None
    model_id: str | None = None
    model_version: str | None = None
    parent_ids: list[str] = field(default_factory=list)
    input_checksums: dict[str, str] = field(default_factory=dict)
    artifact_checksum: str | None = None
    is_deterministic: bool = True


class LineageChain:
    """Provides lineage traversal and dependency resolution across provenance records."""

    def __init__(self, records: dict[str, ProvenanceRecord] | None = None) -> None:
        self._records: dict[str, ProvenanceRecord] = dict(records or {})

    def add_record(self, record: ProvenanceRecord) -> None:
        """Register a provenance record into the lineage chain."""
        self._records[record.id] = record

    def get_record(self, record_id: str) -> ProvenanceRecord | None:
        return self._records.get(record_id)

    def get_ancestors(self, record_id: str) -> list[ProvenanceRecord]:
        """Traverse and return all upstream ancestor records in topological order (no cycles)."""
        visited: set[str] = set()
        ancestors: list[ProvenanceRecord] = []

        def _traverse(current_id: str) -> None:
            if current_id in visited:
                return
            visited.add(current_id)
            record = self._records.get(current_id)
            if not record:
                return
            for parent_id in record.parent_ids:
                _traverse(parent_id)
            if current_id != record_id:
                ancestors.append(record)

        _traverse(record_id)
        return ancestors
