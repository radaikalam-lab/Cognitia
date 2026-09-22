# Contract: Distributed & Edge Cognition Contract

**Contract Status**: Authoritative  
**Contract Version**: 1.0.0  
**Phase**: Phase 8 Distributed & Edge Cognition

---

## 1. Purpose

The **Distributed & Edge Cognition Contract** establishes the semantic and runtime architecture for distributed Cognitia nodes. It ensures that cognitive artifacts retain identical meaning, identity, provenance, determinism, and authority semantics regardless of the node on which they are created or processed.

---

## 2. Core Invariant

> **Distribution changes where cognition executes, not what a cognitive artifact means.**

Central and edge runtimes share the same canonical cognitive substrate. A `DirectionalProposal` created at an edge node means the same thing as one created at a central node.

---

## 3. Node Identity

A `CognitiveNode` identifies a logical Cognitia execution location. It does not replace artifact identity.

```text
CognitiveNode
  ├── node_id: str
  ├── node_type: NodeType (CENTRAL, EDGE, EMBEDDED)
  ├── schema_version: str
  ├── runtime_version: str
  ├── capabilities: tuple[NodeCapability, ...]
  ├── created_at: str
  └── metadata: dict[str, Any]
```

### 3.1 Node Identity vs Artifact Identity

```text
node_id                ≠  observation_id
node_id                ≠  experience_id
node_id                ≠  proposal_id
```

Node identity identifies **where** an artifact originated or was processed. Artifact identity identifies the artifact itself. Both are preserved.

---

## 4. Node Types

```text
NodeType
  ├── CENTRAL   (Aggregated cognition, governance, consolidation)
  ├── EDGE      (Local observation, local cognition, disconnected operation)
  └── EMBEDDED  (In-process embedding inside a host application)
```

Node type does not imply authority. An edge node is not inherently less authoritative.

---

## 5. Capability Advertisement

```text
NodeCapability
  ├── capability_id: str
  ├── capability_type: str
  ├── version: str
  ├── is_available: bool
  └── metadata: dict[str, Any]
```

Capability advertisement describes what a node can do. It does not grant execution authority.

---

## 6. Cognitive Envelope

A `CognitiveEnvelope` is a transport-neutral wrapper for cognitive artifacts.

```text
CognitiveEnvelope
  ├── envelope_id: str
  ├── schema_version: str
  ├── artifact_type: str
  ├── artifact_id: str
  ├── source_node_id: str
  ├── origin_node_id: str
  ├── created_at: str
  ├── sequence_number: int | None
  ├── payload: CognitiveObject
  ├── provenance: ProvenanceRecord
  └── metadata: dict[str, Any]
```

### 6.1 Envelope Principles

1. The payload remains a canonical Cognitia artifact.
2. No `EdgeObservation`, `CentralObservation`, etc. are created.
3. Envelope serialization follows deterministic rules.
4. Transport metadata is distinct from provenance.

---

## 7. Synchronization

Synchronization is data/cognitive-state movement. It is not execution.

```text
SyncService (Protocol)
  ├── publish(envelope: CognitiveEnvelope) -> None
  ├── receive(node_id: str) -> CognitiveEnvelope | None
  ├── acknowledge(envelope_id: str) -> None
  ├── get_sync_state(source_node_id: str, target_node_id: str) -> SynchronizationState
  ├── reconcile(peer_id: str) -> list[CognitiveConflict]
  └── get_pending(node_id: str) -> list[CognitiveEnvelope]
```

### 7.1 Local-First Operation

An edge runtime MUST remain fully operational when central is unavailable.

### 7.2 Idempotency

Receiving the same envelope twice must NOT create two semantic artifacts. Canonical artifact identity is used for deduplication.

---

## 8. Conflict Representation

```text
CognitiveConflict
  ├── conflict_id: str
  ├── subject_id: str
  ├── artifact_ids: tuple[str, ...]
  ├── source_nodes: tuple[str, ...]
  ├── conflict_type: ConflictType
  ├── description: str
  ├── detected_at: str
  ├── provenance: ProvenanceRecord
  └── status: ConflictStatus
```

### 8.1 Conflict Types

```text
ConflictType
  ├── VERSION_CONFLICT
  ├── STATE_CONFLICT
  ├── EVIDENCE_CONFLICT
  ├── EPISTEMIC_CONFLICT
  ├── DIRECTION_CONFLICT
  └── PROVENANCE_CONFLICT
```

### 8.2 Conflict Status

```text
ConflictStatus
  ├── OPEN
  ├── RESOLVED
  └── ESCALATED
```

Conflicts must remain visible. Epistemic conflicts must not be silently resolved.

---

## 9. Synchronization State

```text
SynchronizationState
  ├── node_id: str
  ├── peer_id: str
  ├── last_sent: str | None
  ├── last_received: str | None
  ├── pending_count: int
  ├── acknowledged_count: int
  ├── failed_count: int
  └── metadata: dict[str, Any]
```

---

## 10. Runtimes

### 10.1 CentralCognitiveRuntime

A runtime composition boundary capable of hosting all Cognitia services. Conceptually identical to `LocalCognitiveRuntime` but designated for central deployment.

### 10.2 EdgeCognitiveRuntime

A local execution boundary capable of performing a useful subset of cognition without requiring continuous central availability. Exact capabilities are configurable.

### 10.3 Shared Substrate

Central and edge runtimes share the same cognitive substrate. They differ only in deployment topology and configured capabilities, not in semantic meaning.

---

## 11. Authority Boundary

Synchronization does not grant execution authority. An edge node receiving a `DirectionalProposal` does not acquire the authority to execute it. Authority remains with the domain application.

---

## 12. Determinism

Where deterministic behavior is promised:

```text
same input + same node configuration + same provider configuration = same cognitive result
```

Globally deterministic distributed execution is not promised when asynchronous arrival order can differ. Provenance and state are preserved to reconstruct what happened.

---

## 13. Zero Dependencies

Phase 8 maintains:
- 0 external runtime dependencies
- 0 network dependencies
- 0 AI/ML frameworks

The `InMemoryCognitiveTransport` provides a deterministic in-process transport for tests.

---

## 14. Integration Points

- **Persistence**: Local persistence remains valid while disconnected.
- **Provenance**: Origin node and processing node remain identifiable after synchronization.
- **Providers**: Provider execution locality does not change capability semantics.
- **Directional Programming**: Specifications and proposals cross node boundaries without semantic change.
- **Reasoning**: Traces preserve originating node, inputs, and provenance across nodes.
- **Plasticity**: Candidate artifacts synchronize without automatic activation or model mutation.
