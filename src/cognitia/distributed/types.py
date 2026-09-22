"""Cognitia Distributed & Edge Cognition Types.

Defines node identity, capability advertisement, cognitive envelopes,
conflict representation, synchronization state, and topology.
"""

from __future__ import annotations

import enum
from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable

from cognitia.abi.types import (
    CognitiveObject,
    SCHEMA_VERSION_V1,
    current_utc_timestamp,
    generate_entity_id,
)
from cognitia.provenance.record import ProvenanceRecord, SourceType


class NodeType(str, enum.Enum):
    """Logical execution location of a Cognitia runtime."""

    CENTRAL = "central"
    EDGE = "edge"
    EMBEDDED = "embedded"


class ConflictType(str, enum.Enum):
    """Categories of cognitive conflicts detectable during synchronization."""

    VERSION_CONFLICT = "version_conflict"
    STATE_CONFLICT = "state_conflict"
    EVIDENCE_CONFLICT = "evidence_conflict"
    EPISTEMIC_CONFLICT = "epistemic_conflict"
    DIRECTION_CONFLICT = "direction_conflict"
    PROVENANCE_CONFLICT = "provenance_conflict"


class ConflictStatus(str, enum.Enum):
    """Lifecycle status of a detected cognitive conflict."""

    OPEN = "open"
    RESOLVED = "resolved"
    ESCALATED = "escalated"


@dataclass(frozen=True)
class NodeCapability:
    """Advertisement of a single capability available on a node."""

    capability_id: str
    capability_type: str
    version: str = "1.0.0"
    is_available: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class CognitiveNode(CognitiveObject):
    """Immutable identity of a logical Cognitia execution location."""

    node_type: NodeType = NodeType.EMBEDDED
    runtime_version: str = "0.1.0"
    capabilities: tuple[NodeCapability, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)
    provenance: ProvenanceRecord = field(
        default_factory=lambda: ProvenanceRecord(source_type=SourceType.DETERMINISTIC_RULE)
    )

    def __init__(
        self,
        node_id: str,
        node_type: NodeType | str = NodeType.EMBEDDED,
        runtime_version: str = "0.1.0",
        capabilities: Sequence[NodeCapability] = (),
        metadata: Mapping[str, Any] | None = None,
        provenance: ProvenanceRecord | None = None,
    ) -> None:
        object.__setattr__(self, "id", str(node_id))
        object.__setattr__(self, "schema_version", SCHEMA_VERSION_V1)
        object.__setattr__(self, "created_at", current_utc_timestamp())
        if isinstance(node_type, str):
            node_type = NodeType(node_type)
        object.__setattr__(self, "node_type", node_type)
        object.__setattr__(self, "runtime_version", str(runtime_version))
        object.__setattr__(self, "capabilities", tuple(capabilities))
        object.__setattr__(self, "metadata", dict(metadata or {}))

        prov = provenance or ProvenanceRecord(
            source_type=SourceType.DETERMINISTIC_RULE,
            producer_id="cognitive_node_builder",
            is_deterministic=True,
        )
        object.__setattr__(self, "provenance", prov)


@dataclass(frozen=True)
class CognitiveEnvelope(CognitiveObject):
    """Transport-neutral wrapper for a cognitive artifact.

    INVARIANTS:
    1. The payload remains a canonical Cognitia artifact.
    2. No domain-specific envelope variants (e.g., EdgeObservation) are created.
    3. Envelope serialization follows deterministic rules.
    """

    artifact_type: str = ""
    artifact_id: str = ""
    source_node_id: str = ""
    origin_node_id: str = ""
    sequence_number: int | None = None
    payload: CognitiveObject = field(default_factory=CognitiveObject)
    provenance: ProvenanceRecord = field(
        default_factory=lambda: ProvenanceRecord(source_type=SourceType.DETERMINISTIC_RULE)
    )

    def __init__(
        self,
        artifact_type: str = "",
        artifact_id: str = "",
        source_node_id: str = "",
        origin_node_id: str = "",
        sequence_number: int | None = None,
        payload: CognitiveObject | None = None,
        provenance: ProvenanceRecord | None = None,
        metadata: Mapping[str, Any] | None = None,
    ) -> None:
        object.__setattr__(self, "id", generate_entity_id())
        object.__setattr__(self, "schema_version", SCHEMA_VERSION_V1)
        object.__setattr__(self, "created_at", current_utc_timestamp())
        object.__setattr__(self, "artifact_type", str(artifact_type))
        object.__setattr__(self, "artifact_id", str(artifact_id))
        object.__setattr__(self, "source_node_id", str(source_node_id))
        object.__setattr__(self, "origin_node_id", str(origin_node_id))
        object.__setattr__(self, "sequence_number", sequence_number)
        object.__setattr__(self, "payload", payload or CognitiveObject())

        prov = provenance or ProvenanceRecord(
            source_type=SourceType.DETERMINISTIC_RULE,
            producer_id="cognitive_envelope_builder",
            parent_ids=[artifact_id],
            is_deterministic=True,
        )
        object.__setattr__(self, "provenance", prov)
        object.__setattr__(self, "metadata", dict(metadata or {}))


@dataclass(frozen=True)
class CognitiveConflict(CognitiveObject):
    """Explicit representation of a conflict between cognitive artifacts."""

    subject_id: str = ""
    artifact_ids: tuple[str, ...] = ()
    source_nodes: tuple[str, ...] = ()
    conflict_type: ConflictType = ConflictType.STATE_CONFLICT
    description: str = ""
    status: ConflictStatus = ConflictStatus.OPEN
    detected_at: str = field(default_factory=current_utc_timestamp)
    provenance: ProvenanceRecord = field(
        default_factory=lambda: ProvenanceRecord(source_type=SourceType.DETERMINISTIC_RULE)
    )

    def __init__(
        self,
        subject_id: str = "",
        artifact_ids: Sequence[str] = (),
        source_nodes: Sequence[str] = (),
        conflict_type: ConflictType | str = ConflictType.STATE_CONFLICT,
        description: str = "",
        status: ConflictStatus | str = ConflictStatus.OPEN,
        detected_at: str | None = None,
        provenance: ProvenanceRecord | None = None,
        metadata: Mapping[str, Any] | None = None,
    ) -> None:
        object.__setattr__(self, "id", generate_entity_id())
        object.__setattr__(self, "schema_version", SCHEMA_VERSION_V1)
        object.__setattr__(self, "created_at", current_utc_timestamp())
        object.__setattr__(self, "subject_id", str(subject_id))
        object.__setattr__(self, "artifact_ids", tuple(artifact_ids))
        object.__setattr__(self, "source_nodes", tuple(source_nodes))
        if isinstance(conflict_type, str):
            conflict_type = ConflictType(conflict_type)
        object.__setattr__(self, "conflict_type", conflict_type)
        object.__setattr__(self, "description", str(description))
        if isinstance(status, str):
            status = ConflictStatus(status)
        object.__setattr__(self, "status", status)
        object.__setattr__(self, "detected_at", detected_at or current_utc_timestamp())

        prov = provenance or ProvenanceRecord(
            source_type=SourceType.DETERMINISTIC_RULE,
            producer_id="cognitive_conflict_builder",
            is_deterministic=True,
        )
        object.__setattr__(self, "provenance", prov)
        object.__setattr__(self, "metadata", dict(metadata or {}))


@dataclass(frozen=True)
class SynchronizationState(CognitiveObject):
    """Minimal state tracking for synchronization between two nodes."""

    node_id: str = ""
    peer_id: str = ""
    last_sent: str | None = None
    last_received: str | None = None
    pending_count: int = 0
    acknowledged_count: int = 0
    failed_count: int = 0
    provenance: ProvenanceRecord = field(
        default_factory=lambda: ProvenanceRecord(source_type=SourceType.DETERMINISTIC_RULE)
    )

    def __init__(
        self,
        node_id: str = "",
        peer_id: str = "",
        last_sent: str | None = None,
        last_received: str | None = None,
        pending_count: int = 0,
        acknowledged_count: int = 0,
        failed_count: int = 0,
        provenance: ProvenanceRecord | None = None,
        metadata: Mapping[str, Any] | None = None,
    ) -> None:
        object.__setattr__(self, "id", generate_entity_id())
        object.__setattr__(self, "schema_version", SCHEMA_VERSION_V1)
        object.__setattr__(self, "created_at", current_utc_timestamp())
        object.__setattr__(self, "node_id", str(node_id))
        object.__setattr__(self, "peer_id", str(peer_id))
        object.__setattr__(self, "last_sent", last_sent)
        object.__setattr__(self, "last_received", last_received)
        object.__setattr__(self, "pending_count", int(pending_count))
        object.__setattr__(self, "acknowledged_count", int(acknowledged_count))
        object.__setattr__(self, "failed_count", int(failed_count))

        prov = provenance or ProvenanceRecord(
            source_type=SourceType.DETERMINISTIC_RULE,
            producer_id="synchronization_state_builder",
            is_deterministic=True,
        )
        object.__setattr__(self, "provenance", prov)
        object.__setattr__(self, "metadata", dict(metadata or {}))


class CognitiveTopology:
    """Describes connectivity/relationships between cognitive nodes without granting authority."""

    def __init__(self, nodes: list[CognitiveNode] | None = None) -> None:
        self._nodes: dict[str, CognitiveNode] = {n.id: n for n in (nodes or [])}
        self._edges: list[tuple[str, str]] = []

    def add_node(self, node: CognitiveNode) -> None:
        self._nodes[node.id] = node

    def add_edge(self, source_id: str, target_id: str) -> None:
        self._edges.append((source_id, target_id))

    def get_node(self, node_id: str) -> CognitiveNode | None:
        return self._nodes.get(node_id)

    def list_nodes(self) -> list[CognitiveNode]:
        return list(self._nodes.values())

    def list_edges(self) -> list[tuple[str, str]]:
        return list(self._edges)
