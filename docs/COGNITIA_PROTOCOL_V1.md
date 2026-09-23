# Cognitia ↔ Thorium Integration Protocol Specification (Protocol v1)

## Document Metadata
* **Protocol Version**: `1.0.0`
* **Status**: **FROZEN & ADVISORY**
* **Transport**: Local Windows Named Pipe (`\\.\pipe\cognitia_observation_v1`) / Streaming UTF-8 JSON Lines
* **Authority Level**: `Cognitia: authority = NONE` | `Thorium: Execution Authority & Observation Source`
* **Date**: 2026-09-23

---

## 1. Architectural Foundations & Authority Law

The Thorium ↔ Cognitia Integration Protocol establishes a strict, auditable, unidirectional observation and advisory intelligence loop between the **Thorium Browser** and the **Cognitia Epistemic Core**:

```text
[ Thorium Browser Host ]
        │
        │  1. Observation Stream (Inbound Advisory, authority = NONE)
        ▼
[ Named Pipe IPC Transport ]
        │
        │  2. Asynchronous Dispatch (< 0.05ms UI thread impact, Bounded Queue)
        ▼
[ Cognitia Epistemic Core / Daemon ]
        │
        │  3. Representation, Ingestion, Inference, & Learning Loop
        ▼
[ Directional Reasoning & Advisory Proposal ]
        │
        │  4. CandidateActionProposal (authority = NONE)
        ▼
[ External Governance / Human Authority / Host Browser Validation ]
        │
        │  5. External Approval (decision_source = EXTERNAL)
        ▼
[ Thorium Host Execution ]
        │
        │  6. Host Executes Action
        ▼
[ Execution Observation ]
        │
        │  7. ExecutionResultObserved
        ▼
[ Cognitia State Reconciliation ]
```

### The Inviolable Authority Invariant
1. **Cognitia is NEVER an execution authority for Thorium**: Cognitia observations, representations, learning updates, candidate models, and action proposals carry `authority = "NONE"`.
2. **Thorium and External Governance bear all execution authority**: Proposals are strictly data artifacts. They cannot trigger browser mutations, clicks, script execution, downloads, or navigation without explicit external domain host execution.
3. **Execution is Observed, Never Inferred**: Cognitia reconciles state only upon receiving verified `EXECUTION_RESULT_OBSERVED` events.

---

## 2. Base Envelope Specification

Every message transmitted over the transport boundary is wrapped in a standard **Base Envelope** serialized as a single-line UTF-8 JSON object terminated by `\n` (JSON Lines format).

### 2.1 Envelope Schema Definition

```json
{
  "$schema": "https://cognitia.radlab.dev/schemas/v1/envelope.json",
  "protocol_version": "1.0.0",
  "message_type": "OBSERVATION",
  "message_id": "msg_01J8G5R2N00000000000000001",
  "session_id": "sess_01J8G5R2M00000000000000001",
  "sequence_number": 1,
  "timestamp": "2026-09-23T19:45:00.000000Z",
  "source": {
    "application": "Thorium",
    "adapter": "LeanThoriumCognitiaAdapter",
    "adapter_version": "1.0.0",
    "browser_version": "138.0.7204.306"
  },
  "correlation_id": "corr_01J8G5R2N00000000000000001",
  "causation_id": null,
  "payload": {}
}
```

### 2.2 Envelope Fields Specification

| Field | Type | Required? | Description & Validation Rules |
| :--- | :--- | :--- | :--- |
| `protocol_version` | String | **YES** | Must match SemVer `1.0.x`. Messages with unsupported major versions are rejected immediately with `ERROR (UNSUPPORTED_PROTOCOL_VERSION)`. |
| `message_type` | String (Enum) | **YES** | Must be one of the defined 12 message types in Section 3. |
| `message_id` | String | **YES** | Globally unique identifier formatted as a TypeID, UUIDv7, or ULID. Unique within a session. |
| `session_id` | String | **YES** | Active IPC session identifier established during handshake. Resets upon reconnection. |
| `sequence_number` | Integer | **YES** | Monotonically increasing sequence number starting at 1 for each session. Gap or duplicate triggers sequence fault. |
| `timestamp` | String (ISO-8601) | **YES** | UTC timestamp with microsecond resolution (`YYYY-MM-DDTHH:MM:SS.ffffffZ`). |
| `source` | Object | **YES** | Identifies application identity, adapter version, and host browser version. |
| `correlation_id` | String | **YES** | Root causal trace identifier. Propagated unchanged across the entire causal graph from observation to reconciliation. |
| `causation_id` | String / Null | **YES** | `message_id` of the direct antecedent message that caused this message to be emitted. |
| `payload` | Object | **YES** | Typed payload dictionary adhering to the schema of `message_type`. |

---

## 3. Message Types & Typed Schemas

Protocol v1 defines exactly **12 formal message types**:

```text
Session Management:
  1. SESSION_HELLO
  2. SESSION_ACCEPT
  3. SESSION_REJECT
  4. SESSION_CLOSE

Observation Stream:
  5. OBSERVATION
  6. OBSERVATION_BATCH

Directional & Advisory Intelligence:
  7. DIRECTIONAL_SPEC
  8. CANDIDATE_ACTION_PROPOSAL

External Governance & Execution:
  9. EXECUTION_AUTHORIZATION_OBSERVED
  10. EXECUTION_RESULT_OBSERVED

Diagnostic & Lifecycle:
  11. ERROR
  12. HEARTBEAT
```

---

### 3.1 Session Management Messages

#### `SESSION_HELLO` (Thorium $\rightarrow$ Cognitia)
Initiates a new IPC session over the Named Pipe.
```json
{
  "protocol_version": "1.0.0",
  "message_type": "SESSION_HELLO",
  "message_id": "msg_hello_01",
  "session_id": "sess_pending",
  "sequence_number": 1,
  "timestamp": "2026-09-23T19:45:00.000Z",
  "source": { "application": "Thorium", "adapter": "LeanThoriumCognitiaAdapter", "adapter_version": "1.0.0", "browser_version": "138.0.7204.306" },
  "correlation_id": "corr_hello_01",
  "causation_id": null,
  "payload": {
    "client_nonce": "c98f82a17b0e4392",
    "requested_protocol_version": "1.0.0",
    "declared_capabilities": ["observe.navigation", "observe.tab", "observe.content_selected", "observe.content_metadata"],
    "transport_mode": "NAMED_PIPE_WIN_ASYNC",
    "queue_capacity": 100
  }
}
```

#### `SESSION_ACCEPT` (Cognitia $\rightarrow$ Thorium)
Confirms successful session negotiation and assigns the permanent `session_id`.
```json
{
  "protocol_version": "1.0.0",
  "message_type": "SESSION_ACCEPT",
  "message_id": "msg_accept_01",
  "session_id": "sess_20260923_001",
  "sequence_number": 1,
  "timestamp": "2026-09-23T19:45:00.005Z",
  "source": { "application": "CognitiaDaemon", "adapter": "EpistemicBridge", "adapter_version": "1.0.0", "browser_version": "N/A" },
  "correlation_id": "corr_hello_01",
  "causation_id": "msg_hello_01",
  "payload": {
    "accepted_protocol_version": "1.0.0",
    "session_id": "sess_20260923_001",
    "session_token": "tok_991823abce8812",
    "granted_capabilities": ["observe.navigation", "observe.tab", "observe.content_selected", "observe.content_metadata"],
    "heartbeat_interval_ms": 5000,
    "max_payload_bytes": 524288
  }
}
```

#### `SESSION_REJECT` (Cognitia $\rightarrow$ Thorium)
Rejects incompatible protocol version or invalid client.
```json
{
  "protocol_version": "1.0.0",
  "message_type": "SESSION_REJECT",
  "message_id": "msg_reject_01",
  "session_id": "sess_rejected",
  "sequence_number": 1,
  "timestamp": "2026-09-23T19:45:00.005Z",
  "source": { "application": "CognitiaDaemon", "adapter": "EpistemicBridge", "adapter_version": "1.0.0", "browser_version": "N/A" },
  "correlation_id": "corr_hello_01",
  "causation_id": "msg_hello_01",
  "payload": {
    "error_code": "INCOMPATIBLE_PROTOCOL_VERSION",
    "reason": "Requested protocol version '2.0.0' is not supported by daemon (supported: '1.0.0')",
    "supported_versions": ["1.0.0"]
  }
}
```

#### `SESSION_CLOSE` (Bidirectional)
Gracefully closes an active session.

---

### 3.2 Observation Messages

#### `OBSERVATION` (Thorium $\rightarrow$ Cognitia)
Transmits a single sanitized telemetry or content event.
```json
{
  "protocol_version": "1.0.0",
  "message_type": "OBSERVATION",
  "message_id": "msg_obs_02",
  "session_id": "sess_20260923_001",
  "sequence_number": 2,
  "timestamp": "2026-09-23T19:45:01.120Z",
  "source": { "application": "Thorium", "adapter": "LeanThoriumCognitiaAdapter", "adapter_version": "1.0.0", "browser_version": "138.0.7204.306" },
  "correlation_id": "corr_nav_1001",
  "causation_id": null,
  "payload": {
    "observation_type": "navigation_committed",
    "window_id": 1,
    "tab_id": 4,
    "is_active_tab": true,
    "is_incognito": false,
    "profile_id": "profile_default",
    "page": {
      "url": "https://docs.radlab.dev/architecture?doc_id=901",
      "origin": "https://docs.radlab.dev",
      "title": "Cognitia Architecture Overview",
      "transition_type": "LINK"
    },
    "extracted_content": {
      "mode": "selected_text",
      "text": "Cognitia operates as an advisory epistemic layer with zero production execution authority.",
      "byte_size": 91,
      "is_truncated": false
    },
    "provenance": {
      "source_type": "sensor",
      "producer_id": "thorium:browser_observation_collector",
      "capability_id": "observe.navigation"
    }
  }
}
```

#### `OBSERVATION_BATCH` (Thorium $\rightarrow$ Cognitia)
Transmits a contiguous list of observations.

---

### 3.3 Directional & Advisory Messages

#### `DIRECTIONAL_SPEC` (Cognitia Internal / Client $\rightarrow$ Cognitia Core)
Defines an advisory goal or directional search space without procedural steps.
```json
{
  "protocol_version": "1.0.0",
  "message_type": "DIRECTIONAL_SPEC",
  "message_id": "msg_dir_03",
  "session_id": "sess_20260923_001",
  "sequence_number": 3,
  "timestamp": "2026-09-23T19:45:01.200Z",
  "source": { "application": "CognitiaDaemon", "adapter": "DirectionalEngine", "adapter_version": "1.0.0", "browser_version": "N/A" },
  "correlation_id": "corr_nav_1001",
  "causation_id": "msg_obs_02",
  "payload": {
    "domain_id": "browser_research",
    "intent": "Extract relevant reference links from technical architecture document",
    "desired_direction": "Explore documentation citations",
    "constraints": ["no_external_navigation", "read_only_dom"],
    "allowed_capabilities": ["observe.content_metadata", "observe.content_selected"],
    "authority": "NONE"
  }
}
```

#### `CANDIDATE_ACTION_PROPOSAL` (Cognitia $\rightarrow$ External Governance / Host)
Advisory candidate proposal generated by Cognitia machine learning/reasoning.
```json
{
  "protocol_version": "1.0.0",
  "message_type": "CANDIDATE_ACTION_PROPOSAL",
  "message_id": "msg_prop_04",
  "session_id": "sess_20260923_001",
  "sequence_number": 4,
  "timestamp": "2026-09-23T19:45:01.350Z",
  "source": { "application": "CognitiaDaemon", "adapter": "AdaptiveLearningService", "adapter_version": "1.0.0", "browser_version": "N/A" },
  "correlation_id": "corr_nav_1001",
  "causation_id": "msg_dir_03",
  "payload": {
    "proposal_id": "prop_20260923_001",
    "domain_id": "browser_research",
    "source_model_id": "laya_acoustic_v1",
    "source_model_version": "1.0.0",
    "intent": "Propose bookmarking canonical architecture overview",
    "target": { "url": "https://docs.radlab.dev/architecture?doc_id=901", "tab_id": 4 },
    "candidate_action": {
      "action_type": "create_reading_list_entry",
      "title": "Cognitia Architecture Overview",
      "url": "https://docs.radlab.dev/architecture?doc_id=901"
    },
    "rationale": "High relevance score (0.94) based on directional intent",
    "risk_classification": "LOW_READ_ONLY",
    "authority": "NONE",
    "status": "PROPOSED"
  }
}
```

---

### 3.4 Governance & Execution Messages

#### `EXECUTION_AUTHORIZATION_OBSERVED` (Host / Governance $\rightarrow$ Cognitia)
External domain authority records approval or rejection of a proposal.
```json
{
  "protocol_version": "1.0.0",
  "message_type": "EXECUTION_AUTHORIZATION_OBSERVED",
  "message_id": "msg_auth_05",
  "session_id": "sess_20260923_001",
  "sequence_number": 5,
  "timestamp": "2026-09-23T19:45:02.000Z",
  "source": { "application": "ThoriumGovernanceUI", "adapter": "HumanReviewBoundary", "adapter_version": "1.0.0", "browser_version": "138.0.7204.306" },
  "correlation_id": "corr_nav_1001",
  "causation_id": "msg_prop_04",
  "payload": {
    "authorization_id": "auth_20260923_001",
    "proposal_id": "prop_20260923_001",
    "decision": "APPROVED",
    "decision_source": "EXTERNAL",
    "external_actor_id": "operator_alice",
    "external_authority_domain": "user_ui_prompt",
    "rationale": "User clicked 'Approve Bookmark' in prompt dialog",
    "cognitia_authority": "NONE"
  }
}
```

#### `EXECUTION_RESULT_OBSERVED` (Thorium $\rightarrow$ Cognitia)
Factual telemetry observation capturing the actual result of the host-side action.
```json
{
  "protocol_version": "1.0.0",
  "message_type": "EXECUTION_RESULT_OBSERVED",
  "message_id": "msg_exec_06",
  "session_id": "sess_20260923_001",
  "sequence_number": 6,
  "timestamp": "2026-09-23T19:45:02.150Z",
  "source": { "application": "Thorium", "adapter": "LeanThoriumCognitiaAdapter", "adapter_version": "1.0.0", "browser_version": "138.0.7204.306" },
  "correlation_id": "corr_nav_1001",
  "causation_id": "msg_auth_05",
  "payload": {
    "execution_id": "exec_20260923_001",
    "proposal_id": "prop_20260923_001",
    "authorization_id": "auth_20260923_001",
    "execution_status": "EXECUTED",
    "executed_action": "create_reading_list_entry",
    "actual_outcome": {
      "success": true,
      "entry_id": "read_list_8819",
      "created_at": "2026-09-23T19:45:02.145Z"
    },
    "authority": "NONE"
  }
}
```

---

## 4. Message Ordering & Correlation Rules

1. **Monotonic Sequence Enforcement**:
   - `sequence_number` starts at 1 and increments by 1 on every message within a session.
   - If `incoming_sequence != last_sequence + 1`, the receiver immediately raises `SEQUENCE_FAULT` and rejects the message.
2. **Deterministic Causal Lineage**:
   - `correlation_id` matches the originating `message_id` of the initial `OBSERVATION` or request and remains immutable throughout the downstream lifecycle.
   - `causation_id` strictly references the immediate parent `message_id`.
   - Any DAG audit traversal reconstructs the full chain: `OBSERVATION` $\rightarrow$ `DIRECTIONAL_SPEC` $\rightarrow$ `CANDIDATE_ACTION_PROPOSAL` $\rightarrow$ `EXECUTION_AUTHORIZATION_OBSERVED` $\rightarrow$ `EXECUTION_RESULT_OBSERVED`.

---

## 5. Backpressure & Congestion Control

1. **Chromium UI Thread Isolation**:
   - Browser UI callbacks in `BrowserObservationCollector` must complete formatting and dispatch in `< 0.05ms`.
   - No synchronous IPC, blocking named pipe operations, or disk I/O are permitted on the UI thread.
2. **Bounded Queue Contract**:
   - Outbound queue (`BoundedEventQueue`) has a fixed capacity of **100 messages**.
   - If the Cognitia daemon is slow or disconnected, the queue buffers events up to capacity.
   - Upon overflow, the oldest uncommitted observation is dropped (`kDropOldest`), emitting a local diagnostic warning without blocking the browser.

---

## 6. Daemon Lifecycle, Reconnection, & Stale Proposal Invalidation

1. **Session Replacement**:
   - If the IPC connection is lost, Thorium transitions to `kDisconnected` and retries on background thread.
   - When reconnected, a new `SESSION_HELLO` creates a brand new `session_id`.
2. **Stale Proposal Invalidation**:
   - All `CandidateActionProposal` records generated under a prior `session_id` are permanently invalidated upon session replacement.
   - Any attempt to authorize a stale proposal is rejected with `STALE_PROPOSAL_SESSION_MISMATCH`.
