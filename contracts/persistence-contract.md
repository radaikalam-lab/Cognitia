# Contract: Persistence Contract

**Contract Status**: Authoritative  
**Contract Version**: 1.0.0  
**Phase**: Phase 0 Foundation  

---

## 1. Purpose & Core Principle

The **Persistence Contract** defines the durable substrate for recording, indexing, and reconstructing the cognitive history of Cognitia. It establishes provider-agnostic abstractions for an **Event Journal** (what happened) and an **Object Store** (what cognitive artifacts exist).

### Fundamental Invariant
> **Persistence records what happened; it is not the source of authority or truth.**
>
> $$\text{Persistence} \neq \text{Memory} \neq \text{Reasoning} \neq \text{Authority}$$

Persistence is an append-oriented, auditable substrate. Higher-level cognitive memory and retrospective learning may be built on top of persistent history, but the consuming domain retains final authority over physical reality and actuation.

---

## 2. Real-Time Authority Invariant

> **Persistence is non-authoritative and MUST NEVER be in the hard real-time safety or physical control path.**

Physical controllers, safety interlocks, and local deterministic actuators MUST operate independently and safely even if persistence is delayed, unavailable, or undergoing synchronization. Persistence is typically asynchronous and non-blocking relative to hard real-time domain safety.

---

## 3. Dual Persistence Architecture

Cognitia distinguishes two complementary persistence concepts:

```text
┌────────────────────────────────────────────────────────────────────────┐
│                          PERSISTENCE PLANE                             │
├───────────────────────────────────┬────────────────────────────────────┤
│ 1. EVENT JOURNAL (Append-Only)    │ 2. OBJECT STORE (Durable Entity)   │
│ • What cognitive event happened   │ • What cognitive artifact exists   │
│ • Temporal sequence of operations │ • Canonical UUIDv4 addressable     │
│ • State transitions & lifecycle   │ • Schema-versioned & typed         │
│ • Immutable past events           │ • Immutable artifact state         │
└───────────────────────────────────┴────────────────────────────────────┘
```

---

## 4. Event Journal Specification

### 4.1 Canonical CognitiveEvent Schema
```text
CognitiveEvent
 ├── id: UUID (Unique event identifier)
 ├── schema_version: SemVer (e.g., "1.0.0")
 ├── created_at: ISO-8601 UTC timestamp
 ├── event_type: str (e.g., "ObservationRecorded", "DecisionProposed")
 ├── source_type: SourceType (SENSOR, DETERMINISTIC_RULE, REASONING_ENGINE, etc.)
 ├── source_id: str (Identifier of the producing component/node)
 ├── subject_id: Optional[str] (Target entity ID, e.g., observation ID, decision ID)
 ├── payload: dict[str, Any] (Event context, parameters, or summary data)
 ├── provenance: ProvenanceRecord (Audit lineage of the event generator)
 └── metadata: dict[str, Any]
```

### 4.2 Standard Cognitive Event Types
* `ObservationRecorded`
* `EvidenceRegistered`
* `ExperienceRecorded`
* `HypothesisRegistered`
* `ClaimRegistered`
* `ChallengeIssued`
* `ResidualRecorded`
* `EpistemicTransitionRecorded`
* `ReasoningStarted`
* `ReasoningCompleted`
* `DecisionProposed`
* `ActionRecorded`
* `OutcomeRecorded`
* `ModelRegistered`
* `ModelStatusChanged`
* `CapabilityRegistered`

### 4.3 Event Immutability & Ordering
* Events are strictly append-only.
* Once committed, an event cannot be mutated or deleted.
* Re-registering an event with an existing `event_id` MUST be rejected with an error.
* Events carry `created_at` timestamps; local stores preserve deterministic insertion sequence.

---

## 5. Cognitive Object Store Specification

### 5.1 Persistable Canonical Objects
The Object Store persists all canonical Cognitia ABI objects under their stable UUIDv4 identities:
* `Observation`
* `Evidence`
* `ExperienceRecord`
* `Hypothesis`
* `Claim`
* `Challenge`
* `Residual`
* `ReasoningTrace`
* `Decision`
* `Action`
* `Outcome`
* `ProvenanceRecord`
* `ModelRecord`

### 5.2 Deterministic Serialization
Objects MUST be stored and retrieved using the canonical `DeterministicSerializer` (lexicographically sorted JSON keys, IEEE 754 float representation, no extraneous whitespace).

---

## 6. Persistence Service Provider Interface (SPI)

```python
class PersistenceStore(Protocol):
    """Protocol for provider-agnostic durable cognitive persistence."""

    def append_event(self, event: CognitiveEvent) -> None:
        """Append an immutable event to the journal."""
        ...

    def get_event(self, event_id: str) -> CognitiveEvent | None:
        """Retrieve an event by ID."""
        ...

    def query_events(self, query: EventQuery) -> list[CognitiveEvent]:
        """Query events matching filter criteria."""
        ...

    def get_timeline(self, subject_id: str | None = None) -> list[CognitiveEvent]:
        """Retrieve an ordered sequence of events representing the cognitive timeline."""
        ...

    def save_object(self, obj: CognitiveObject) -> None:
        """Persist a canonical cognitive object."""
        ...

    def get_object(self, object_id: str) -> CognitiveObject | None:
        """Retrieve a canonical cognitive object by ID."""
        ...

    def query_objects(self, query: ObjectQuery) -> list[CognitiveObject]:
        """Query objects matching filter criteria."""
        ...
```

---

## 7. Reconstructable Cognitive Timeline

Persistence guarantees full retrospective reconstruction of cognitive histories:

$$\text{Observation } O_1 \xrightarrow{\text{Event}} \text{Evidence } E_1 \xrightarrow{\text{Event}} \text{Hypothesis } H_1 \xrightarrow{\text{Event}} \text{Trace } T_1 \xrightarrow{\text{Event}} \text{Decision } D_1 \xrightarrow{\text{Domain}} \text{Action } A_1 \xrightarrow{\text{Result}} \text{Outcome } O_2$$

Both temporal order ($E_1 \rightarrow E_2 \rightarrow \dots$) and structural provenance lineage ($D_1 \rightarrow T_1 \rightarrow H_1 \rightarrow E_1 \rightarrow O_1$) remain queryable long after the producing process has terminated.

---

## 8. Provider Boundary & Decoupling

The Persistence SPI supports swappable backend providers:
* `InMemoryPersistenceStore` (Phase 0 reference implementation)
* `SQLitePersistenceStore` (Future local embedded file backend)
* `PostgreSQLPersistenceStore` (Future central database backend)
* `EventStorePersistenceStore` (Future event-sourcing backend)

Cognitia Core contains zero dependencies on any database driver or external storage engine.
