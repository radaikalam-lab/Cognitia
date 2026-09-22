# Cognitia Architecture

## 1. Architectural Overview & Four-Plane Architecture

Cognitia provides domain-neutral, reusable cognitive and epistemic infrastructure across diverse consuming applications without domain coupling or authority overstepping.

```text
┌────────────────────────────────────────────────────────────────────────┐
│                          APPLICATION PLANE                             │
│       AcoustiForge · CellForge · Robotics · Swarms · Science           │
│       Owns: Domain Semantics, Domain Workflows, Scientific Models      │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ Domain Adapters
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                           COGNITIVE PLANE                              │
│       Cognitia Core (ABI, Types, Serialization, Immutability)          │
│       Cognitive Services (Epistemics, Experience, Reasoning, Models)   │
│       Cognitive Memory Layer · Consolidation Pipeline                  │
│       Cognitive Attention Layer · Cognitive Reasoning Engine           │
│       CognitiveService Facade · LocalCognitiveRuntime                  │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ Historical Substrate (Async)
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                          PERSISTENCE PLANE                             │
│       Event Journal (Append-only record of what happened)              │
│       Object Store (Durable canonical cognitive artifacts)             │
│       History Query · Provenance Lineage · Cognitive Timeline          │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ Cognitive Proposals (Advisory)
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                           AUTHORITY PLANE                              │
│       Consuming Devices, Real-Time Controllers, Safety Interlocks       │
│       Owns: Physics, Safety, Constraint Verification, Actuators        │
└────────────────────────────────────────────────────────────────────────┘
```

> **Constitutional Rule**: The Persistence Plane and Memory Layer are durable/retrieval substrates, NOT mandatory real-time execution paths. Persistence and memory are non-authoritative and are NEVER in the hard real-time safety path.

---

## 2. Four-Tier Separation of Concerns

Cognitia enforces a strict 4-tier conceptual separation:

```text
┌────────────────────────────────────────────────────────────────────────┐
│ 1. SERVICE   = WHAT Cognitia provides (Epistemics, Experience,         │
│                Reasoning, Capabilities, Provenance, Model Registry)     │
├────────────────────────────────────────────────────────────────────────┤
│ 2. PERSISTENCE/MEMORY = HOW cognitive history and contextual memory    │
│                are durably stored and selectively retrieved            │
├────────────────────────────────────────────────────────────────────────┤
│ 3. RUNTIME   = WHERE and HOW those services execute                    │
│                (e.g., LocalCognitiveRuntime in Phase 0-4)              │
├────────────────────────────────────────────────────────────────────────┤
│ 4. ADAPTER   = HOW an external domain connects and translates          │
│                (Bidirectional transformation, outside Cognitia core)   │
├────────────────────────────────────────────────────────────────────────┤
│ 5. APPLICATION = WHO owns domain semantics and production authority    │
│                (External client, real-time safety, physical actuators) │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Cognitive Service, Memory & Persistence Composition

```text
                   ┌───────────────────────────────┐
                   │       CognitiveService        │
                   │        (Unified Facade)       │
                   └───────────────┬───────────────┘
                                   │
         ┌───────────────┬─────────┴─────┬────────────────┬──────────────┐
         ▼               ▼               ▼                ▼              ▼
 ┌───────────────┐┌──────────────┐┌──────────────┐┌──────────────┐┌──────────────┐
 │  Experience   ││  Epistemic   ││  Reasoning   ││  Capability  ││    Model     │
 │    Service    ││   Service    ││   Engine     ││   Registry   ││   Registry   │
 └───────┬───────┘└──────┬───────┘└──────┬───────┘└──────┬───────┘└──────┬───────┘
         │               │               │               │               │
         └───────────────┼───────────────┼───────────────┼───────────────┘
                         │               │               │
                         ▼               ▼               ▼
                   ┌───────────────────────────────────────────┐
                   │               MemoryStore                 │
                   │      (Selective Context Retrieval)        │
                   └─────────────────────┬─────────────────────┘
                                         │
                                         ▼
                   ┌───────────────────────────────────────────┐
                   │             PersistenceStore              │
                   │        (Event Journal & Object Store)     │
                   └───────────────────────────────────────────┘
```

---

## 4. Plasticity-Inspired Cognitive Adaptation Loop

```text
                       ┌───────────────────────────────┐
                       │     Consuming Application     │
                       │   (AcoustiForge, FJH, etc.)   │
                       └───────────────┬───────────────┘
                                       │ 1. Telemetry / Observation
                                       ▼
                       ┌───────────────────────────────┐
                       │       Event Journal           │
                       │    (Durable Substrate)        │
                       └───────────────┬───────────────┘
                                       │ 2. Asynchronous History
                                       ▼
                       ┌───────────────────────────────┐
                       │     Episodic Experience       │
                       │           Model               │
                       └───────────────┬───────────────┘
                                       │ 3. Selective Memory Query
                                       ▼
                       ┌───────────────────────────────┐
                       │       Cognitive Memory        │
                       │           Subsystem           │
                       └───────────────┬───────────────┘
                                       │ 4. Memory Context
                                       ▼
                       ┌───────────────────────────────┐
                       │      Plasticity Operator      │
                       │   (Heuristics, Tiny ML, etc.) │
                       └───────────────┬───────────────┘
                                       │ 5. Candidate Learning Artifact
                                       ▼
                       ┌───────────────────────────────┐
                       │       Epistemic Service       │
                       │   (Evaluation & Challenge)    │
                       └───────────────┬───────────────┘
                                       │ 6. Validation / Refutation
                                       ▼
                       ┌───────────────────────────────┐
                       │     Consolidation Service     │
                       │  (Promotion into Model $N+1$) │
                       └───────────────┬───────────────┘
                                       │ 7. Register Model Version
                                       ▼
                       ┌───────────────────────────────┐
                       │        Model Registry         │
                       │ (Versioned Cognitive Memory)  │
                       └───────────────────────────────┘
```

---

## 5. End-to-End Cognitive Pipeline

```text
                 ┌───────────────┐
                 │  Observation  │
                 └───────┬───────┘
                         ↓
                 ┌───────────────┐
                 │  Persistence  │
                 └───────┬───────┘
                         ↓
                 ┌───────────────┐
                 │    Memory     │
                 └───────┬───────┘
                         ↓
                 ┌───────────────┐
                 │    Context    │
                 └───────┬───────┘
                         ↓
                 ┌───────────────┐
                 │  Enrichment   │
                 └───────┬───────┘
                         ↓
                 ┌───────────────┐
                 │   Attention   │
                 └───────┬───────┘
                         ↓
           ╔═══════════════════════════╗
           ║ IMMUTABLE COGNITIVE       ║
           ║ SNAPSHOT (ReasoningInput) ║
           ╚═════════════╤═════════════╝
                         ↓
                 ┌───────────────┐
                 │   Reasoning   │
                 │   Engine      │
                 └───────┬───────┘
                         ↓
              ┌─────────────────────┐
              │ ReasoningTrace      │
              │ Candidate Results   │
              │ Residuals           │
              └──────────┬──────────┘
                         ↓
                 ┌───────────────┐
                 │   Epistemic   │
                 │   Evaluation  │
                 └───────┬───────┘
                         ↓
                 ┌───────────────┐
                 │   Advisory    │
                 │   Cognition   │
                 └───────────────┘

                         ║
                         ║  HARD AUTHORITY BOUNDARY
                         ║
                         ↓

                 ┌───────────────┐
                 │    Domain     │
                 │   Authority   │
                 └───────────────┘
```

---

## 6. Phase 3A: Cognitive Context Enrichment

Phase 3A enriches `CognitiveContext` with structural and descriptive intelligence without turning Context into Reasoning.

```text
Context
├── temporal neighbourhood (BEFORE, AFTER, CONCURRENT, INTERVAL)
├── entity / context neighbourhood (SAME_SUBJECT, SAME_EPISODE, SAME_SOURCE, SHARED_PROVENANCE)
├── state reconstruction (latest, previous, first, unknown, conflicted)
├── observed sequences (chronological order, relative positions, deltas)
├── recurrence (count, intervals, median interval)
├── deterministic aggregates (count, min, max, mean, median, range, sample std dev)
├── historical baselines (baseline ranges)
├── contextual deviations (ABOVE_HISTORICAL_RANGE, BELOW_HISTORICAL_RANGE, RAPID_CHANGE)
├── cross-source correlations (TEMPORAL_PROXIMITY, SHARED_SUBJECT, SHARED_EPISODE)
├── provenance neighbourhood (bounded DAG ancestry)
├── epistemic tension (support/refute evidence distributions)
├── conflict preservation (concurrent observational divergence)
└── structural compression (summary statistics without prioritization)
```

---

## 7. Phase 3: Cognitive Attention Layer

$$\text{Context} = \text{What information is relevant around the current observation}$$
$$\text{Attention} = \text{What information deserves cognitive focus for the current task}$$

1. **Non-Duplication**: Attention prioritizes Context items via immutable references (`item_id`).
2. **Prioritization, NOT Truth Estimation**: `attention_score` is strictly a deterministic prioritization value used to allocate attention budget.
3. **Preservation of Epistemic Tension**: Attention does NOT eliminate contradictory evidence (`SUPPORT` vs `REFUTE`).
4. **Deterministic Budget & Stable Tie-Breaking**: $(\text{attention\_score} \downarrow, \text{time\_delta} \downarrow, \text{timestamp} \downarrow, \text{item\_id} \uparrow)$.

---

## 8. Phase 4: Cognitive Reasoning Layer

Phase 4 introduces a deterministic, explainable, provenance-preserving, provider-agnostic cognitive reasoning layer.

### 8.1 Absolute Invariant
$$\text{Reasoning Output} \neq \text{Truth} \neq \text{Epistemic Status} \neq \text{Decision} \neq \text{Authority}$$

Reasoning produces candidate conclusions, hypotheses, explanatory alternatives, structural analogies, causal hypotheses, counterfactual scenarios, and explicit residuals. It does NOT declare truth, directly alter epistemic status, mutate production state, or execute actions.

### 8.2 Snapshot Principle
> **Reasoning is a transformation of an immutable cognitive snapshot (`ReasoningInput`), not a query against live mutable stores.**

Once `ReasoningInput` is created, mutations to underlying stores (persistence, memory, rules, models) do NOT alter the reasoning input or output.

### 8.3 Modular Reasoning Strategies
```text
ReasoningStrategy (Protocol)
 ├── DeductiveReasoner        (Rule matching, explicit derivation steps, missing premise residuals)
 ├── AbductiveReasoner        (Candidate explanation generation, competing hypotheses, deterministic ranking)
 ├── AnalogicalReasoner       (Structural correspondence mapping, explicit limitations, Non-Equivalence)
 ├── CausalReasoner           (Evaluates explicit causal graphs/mechanisms; strict non-inference guardrails)
 └── CounterfactualReasoner   (Deterministic transition rules under intervention; non-observed hypothetical)
```

### 8.4 Strict Causal Guardrails
$$\text{Temporal Order } (A \text{ BEFORE } B) \neq \text{Causality}$$
$$\text{Correlation } (A \text{ CORRELATES\_WITH } B) \neq \text{Causality}$$

Causal reasoning operates strictly and only on explicitly supplied causal graphs, mechanisms, or causal rules. In the absence of an explicit causal model, causality inference is rejected and recorded as a missing model residual.

---

## 9. Phase 4A: Advanced Reasoning Provider Scaffold

Phase 4A establishes provider-neutral scaffolding for future advanced cognitive capabilities without implementing autonomous AI. The deterministic Cognitia substrate must remain fully functional when every advanced provider is absent or disabled.

### 9.1 Capability Classes

```text
AdvancedCapabilityType
 ├── LLM_REASONING             (Scaffold only)
 ├── TINYML_REASONING          (Scaffold only)
 ├── HYPOTHESIS_GENERATION     (Scaffold only)
 ├── CAUSAL_INFERENCE          (Scaffold only)
 ├── SEMANTIC_GRAPH            (Scaffold only)
 ├── VECTOR_RETRIEVAL          (Scaffold only)
 ├── REINFORCEMENT_LEARNING    (Scaffold only)
 └── SELF_MODIFYING_REASONING  (Scaffold only)
```

### 9.2 Provider Lifecycle

```text
ProviderLifecycleStatus
 ├── DECLARED    (Known, no implementation present)
 ├── REGISTERED  (Metadata registered)
 ├── VALIDATED   (Contract/version passed validation)
 ├── AVAILABLE   (Implementation and resources present)
 ├── ENABLED     (Explicitly permitted to execute)
 ├── DISABLED    (Exists but execution prohibited)
 ├── SUSPENDED   (Previously enabled, temporarily prohibited)
 └── RETIRED     (Permanently inactive)
```

Critical distinction:

```text
AVAILABLE ≠ ENABLED
```

### 9.3 Core Invariant

```text
Provider Output  ≠  Truth  ≠  Epistemic Acceptance  ≠  Decision  ≠  Authority
```

### 9.4 Advanced Provider Architecture

```text
                         COGNITIA CORE
                              │
             ┌────────────────┴────────────────┐
             │                                 │
     Deterministic Cognition           Advanced Provider Layer
             │                                 │
 Observation / Persistence              ┌──────┼──────────┐
 Memory / Context                       │      │          │
 Enrichment / Attention               LLM   TinyML    Similarity
 Snapshot / Reasoning                   │      │          │
             │                          ├──────┼──────────┤
             │                       Hypothesis  Causal
             │                          │         │
             │                          ├─────────┤
             │                         Graph      RL
             │                          │         │
             │                          └────┬────┘
             │                               │
             │                         Evolution
             │                               │
             └───────────────┬───────────────┘
                             ↓
                  Candidate Reasoning Artifact
                             ↓
                    Epistemic Evaluation
                             ↓
                       Governance
                             ↓
                       Consolidation
                             ↓
                  Versioned Cognition
                             ↓
                       Advisory Output
                             ↓
                    Domain Authority
```

### 9.5 Provider Gateway

The `ProviderGateway` enforces execution authorization:

```text
Gateway
  ├── provider exists?         → REJECT if missing
  ├── version exists?          → REJECT if missing
  ├── status == ENABLED?       → REJECT otherwise
  ├── capability supported?    → REJECT if not declared
  ├── resources satisfied?     → REJECT if unavailable
  ├── input snapshot valid?    → REJECT if mismatch
  └── execute provider         → CandidateReasoningArtifact
```

The Gateway does NOT perform epistemic evaluation. Epistemic evaluation is an explicit, separate downstream step.

### 9.6 Proposal vs Activation

```text
ProposalLifecycleStatus
 ├── PROPOSED     (Candidate generated by provider)
 ├── VALIDATED    (Contract/format validated)
 ├── APPROVED     (Governance approved)
 ├── ACTIVATABLE  (Ready for explicit activation)
 ├── ACTIVATED    (Explicitly activated)
 ├── REJECTED     (Explicitly rejected)
 └── RETIRED      (Permanently inactive)
```

Activation must be an explicit governance operation. A candidate never becomes active merely because a provider generated it.

### 9.7 Snapshot Boundary

Providers receive only a bounded immutable `ReasoningInput`. Providers must NOT receive unrestricted references to:

- `PersistenceStore`
- `MemoryStore`
- `RuleStore`
- `ModelRegistry`
- `EpistemicService`
- `LocalCognitiveRuntime`
- Authority Plane
- Domain Application
- Actuators

### 9.8 Zero Dependencies

Phase 4A maintains:
- Python >= 3.12
- 0 external runtime dependencies
- 0 network dependencies
- 0 AI/ML frameworks

All mock providers are deterministic reference implementations with no AI/ML runtime.

---

## 10. Phase 6: Cognitive Pattern Discovery & Governed Plasticity

Phase 6 introduces deterministic, read-only candidate pattern discovery without autonomous learning or production mutation.

### 10.1 Core Invariant

```text
Operator Output  ≠  Truth  ≠  Epistemic Acceptance  ≠  Decision  ≠  Authority  ≠  Production Mutation
```

All plasticity operators are strictly advisory. They examine historical cognitive experience and propose `CandidateLearningArtifact` structures. They MUST NOT:
- mutate persistence,
- mutate memory,
- mutate models,
- mutate rules,
- mutate epistemic state,
- or alter any production cognitive structures.

### 10.2 Plasticity Operator Contract

```text
PlasticityOperator (Protocol)
  ├── propose(context: MemoryContext) -> CandidateLearningArtifact
```

Operators receive a bounded `MemoryContext` snapshot and return a single `CandidateLearningArtifact`. The artifact carries:
- `candidate_type`: PATTERN, ASSOCIATION, etc.
- `proposed_change`: descriptive dictionary of observed structure
- `rationale`: human-readable explanation
- `confidence`: bounded in [0.0, 1.0]
- `provenance`: deterministic provenance record

### 10.3 Deterministic Operators

```text
DeterministicPatternOperator
  ├── Identifies recurring event/subject patterns
  ├── Groups experiences by event_type + subject_id
  ├── Reports recurrence_count
  └── NEVER infers causality, intent, meaning, or truth

DeterministicAssociationOperator
  ├── Detects repeated co-occurrence of distinct event types within episodes
  ├── Explicitly represents ASSOCIATION, never CAUSATION
  └── Example: BoostHigh co-occurs with HighLoad → does NOT become BoostHigh causes HighLoad

DeterministicRecurrenceOperator
  ├── Identifies repeated temporal patterns across experiences
  ├── Reports occurrence_count, episode_count, median interval
  └── Remains strictly descriptive. No prediction. No causal inference.
```

### 10.4 Operator Registry

```text
PlasticityOperatorRegistry (Protocol)
  ├── register(record: OperatorRecord) -> None
  ├── get(operator_id, version?) -> OperatorRecord | None
  ├── list_operators(status?, operator_type?) -> list[OperatorRecord]
  ├── list_versions(operator_id) -> list[OperatorRecord]
  ├── set_lifecycle_status(operator_id, version, status) -> None
  └── is_enabled(operator_id, version?) -> bool
```

Operators follow the same lifecycle as advanced providers:
`DECLARED → REGISTERED → VALIDATED → AVAILABLE → ENABLED → DISABLED → SUSPENDED → RETIRED`

### 10.5 Synthetic Domains

Phase 6 validates plasticity across four synthetic domains:
- **ERP**: InvoiceCreated, PaymentReceived co-occurrence
- **Automotive**: BoostHigh, HighLoad, LowFlow temporal patterns
- **Acoustics**: NoiseDetected, SilenceDetected associations
- **Scientific**: MeasurementTaken recurrence, CalibrationPerformed

### 10.6 Read-Only Guarantee

```text
Operator.propose(context)
  ├── Reads: context.experiences, context.observations
  ├── Returns: CandidateLearningArtifact
  └── MUST NOT modify: context, MemoryStore, PersistenceStore, any production structure
```

### 10.7 Acceptance Criteria

- 28 tests under `tests/plasticity/` (4 test files)
- All tests pass with 0 external dependencies
- No regressions in existing test suite (430 total passing)
- Operators remain read-only and advisory-only
- Deterministic outputs are reproducible

---

## 11. Phase 7: Directional Programming

Phase 7 introduces goal-directed cognitive programming where objectives, constraints, and success criteria are expressed as first-class cognitive specifications rather than imperative instructions.

### 11.1 Core Invariant

```text
Directional Specification  ≠  Imperative Program  ≠  Execution Authority  ≠  Guaranteed Outcome
```

Directional programming defines what cognitive state is desired, not how to achieve it. Execution remains the responsibility of the Authority Plane.

### 11.2 Directional Programming Contract

```text
DirectionalSpecification
  ├── objectives: list[DirectionalObjective]
  ├── constraints: list[DirectionalConstraint]
  └── success_criteria: list[SuccessCriterion]

DirectionalObjective
  ├── description: str
  ├── target_state: dict
  └── priority: int

DirectionalConstraint
  ├── constraint_type: str
  ├── expression: str
  └── severity: str

SuccessCriterion
  ├── criterion_type: str
  ├── expression: str
  └── threshold: float
```

### 11.3 Directional Provider

```text
DirectionalProvider (Protocol)
  ├── propose(specification: DirectionalSpecification) -> DirectionalProposal
  └── capabilities: list[str]

DirectionalProposal
  ├── specification_id: str
  ├── provider_id: str
  ├── proposed_actions: list[ProposedAction]
  ├── residuals: list[DirectionalResidual]
  ├── confidence: float
  └── epistemic_status: EpistemicStatus
```

### 11.4 Residual Semantics

Residuals are explicit declarations of unknowns, missing capabilities, unsatisfiable constraints, or unmodeled dynamics. A proposal with residuals is not a failure - it is a complete and honest accounting of what the provider can and cannot achieve.

### 11.5 Authority Boundary

- Directional proposals are advisory cognitive artifacts
- Proposals do NOT execute actions
- Proposals do NOT mutate production state
- Proposals do NOT alter epistemic state automatically
- Activation requires explicit governance and authority-plane decision

---

## 12. Phase 8: Distributed & Edge Cognition

Phase 8 extends Cognitia to distributed and edge deployment topologies while preserving all existing cognitive semantics, identity, provenance, and authority boundaries.

### 12.1 Core Invariant

```text
Distribution changes WHERE cognition executes, not WHAT a cognitive artifact means.
Node identity (CognitiveNode) does NOT replace artifact identity.
Synchronization is data/cognitive-state movement, NOT execution.
```

### 12.2 Node Identity

```text
CognitiveNode
  ├── node_id: str (unique node identity)
  ├── node_type: NodeType (CENTRAL | EDGE | EMBEDDED)
  ├── runtime_version: str
  ├── capabilities: tuple[NodeCapability, ...]
  └── provenance: ProvenanceRecord

NodeCapability
  ├── capability_id: str
  ├── capability_type: str
  ├── version: str
  └── is_available: bool
```

Critical distinction:
```text
Node Capability Advertisement ≠ Execution Authority
```

### 12.3 Cognitive Envelope

The `CognitiveEnvelope` is a transport-neutral wrapper for cognitive artifacts. The payload remains a canonical Cognitia artifact.

```text
CognitiveEnvelope
  ├── artifact_type: str
  ├── artifact_id: str
  ├── source_node_id: str
  ├── origin_node_id: str
  ├── sequence_number: int | None
  ├── payload: CognitiveObject
  └── provenance: ProvenanceRecord
```

Invariants:
1. The payload remains a canonical Cognitia artifact
2. No domain-specific envelope variants are created
3. Envelope serialization follows deterministic rules

### 12.4 Cognitive Conflict

Conflicts between cognitive artifacts from different nodes are explicitly represented and remain visible.

```text
CognitiveConflict
  ├── subject_id: str
  ├── artifact_ids: tuple[str, ...]
  ├── source_nodes: tuple[str, ...]
  ├── conflict_type: ConflictType
  ├── description: str
  ├── status: ConflictStatus (OPEN | RESOLVED | ESCALATED)
  └── provenance: ProvenanceRecord

ConflictType
  ├── VERSION_CONFLICT
  ├── STATE_CONFLICT
  ├── EVIDENCE_CONFLICT
  ├── EPISTEMIC_CONFLICT
  ├── DIRECTION_CONFLICT
  └── PROVENANCE_CONFLICT
```

### 12.5 Runtime Topology

```text
LocalCognitiveRuntime (base)
  ├── CentralCognitiveRuntime (inherits local substrate)
  └── EdgeCognitiveRuntime (inherits local substrate)
```

All runtimes share the same cognitive substrate (ABI, Persistence, Memory, Reasoning, Attention, etc.). Distribution changes execution location, not cognitive semantics.

### 12.6 Synchronization

```text
SyncService (Protocol)
  ├── publish(envelope: CognitiveEnvelope) -> None
  ├── receive(node_id: str) -> CognitiveEnvelope | None
  ├── acknowledge(envelope_id: str) -> None
  ├── get_sync_state(source, target) -> SynchronizationState
  ├── reconcile(peer_id: str) -> list[CognitiveConflict]
  └── get_pending(node_id: str) -> list[CognitiveEnvelope]

InMemoryCognitiveTransport
  ├── send(envelope, target_node_id)
  ├── receive(node_id) -> idempotent
  ├── acknowledge(envelope_id)
  ├── simulate_duplicate(envelope)
  └── clear()
```

Synchronization properties:
- **Idempotent**: receiving the same envelope twice produces no duplicate effect
- **Local-first**: edge nodes operate fully without central connectivity
- **Offline-capable**: disconnected edge operation preserves all local history
- **Replayable**: offline artifacts remain traceable and reconcilable

### 12.7 Authority & Failure Isolation

```text
Central Unavailable
  └── Edge continues local cognition (Persistence, Memory, Reasoning, Attention)

Edge Unavailable
  └── Central continues unaffected

Sync Unavailable
  └── Local history preserved; reconciliation occurs on reconnection
```

### 12.8 Zero Dependencies

Phase 8 maintains:
- Python >= 3.12
- 0 external runtime dependencies
- 0 network dependencies
- 0 distributed databases or message brokers

All distribution semantics are implemented via deterministic in-process abstractions suitable for testing and local-first operation.

---

## 13. Phase 9: Dynamic Cognitive Documents

Phase 9 introduces deterministic, provider-neutral cognitive document projection. Documents are human-facing projections of existing structured cognitive state, never source of truth, authority, memory, persistence, or execution mechanisms.

### 13.1 Core Invariant

```text
Document  ≠  Source of Truth  ≠  Authority  ≠  Memory  ≠  Execution
```

Cognitive documents are read-only projections. They carry no epistemic weight, carry no decision authority, and never alter underlying cognitive structures. Document generation is advisory-only and side-effect free.

### 13.2 Document Layer Position

```text
                     ┌───────────────────────────────┐
                     │  Structured Cognitive State   │
                     │  (Artifacts, Observations,    │
                     │   Claims, Evidence, Reasoning) │
                     └───────────────┬───────────────┘
                                     │ 13.2.1 Read-only access
                                     ▼
                     ┌───────────────────────────────┐
                     │  Deterministic Document       │
                     │  Projection Layer             │
                     │  (project(), refresh(), diff)  │
                     └───────────────┬───────────────┘
                                     │ 13.2.2 Human-facing output
                                     ▼
                     ┌───────────────────────────────┐
                     │  Dynamic Cognitive Document   │
                     │  (sections, references,       │
                     │   versions, provenance)       │
                     └───────────────────────────────┘
```

The document layer has no write path into structured cognitive state.

### 13.3 Document Specification

A `DocumentSpecification` declares the structure and intent of a document without prescribing implementation details.

```text
DocumentSpecification
  ├── specification_id: str
  ├── schema_version: str
  ├── created_at: str
  ├── document_type: str
  ├── title: str
  ├── requested_artifacts: tuple[DocumentReference, ...]
  ├── requested_sections: tuple[SectionSpecification, ...]
  ├── filters: dict[str, Any] | None
  ├── ordering: tuple[str, ...] | None
  ├── context_scope: dict[str, Any] | None
  ├── attention_scope: dict[str, Any] | None
  ├── provenance_visibility: bool
  ├── epistemic_visibility: bool
  ├── conflict_visibility: bool
  ├── residual_visibility: bool
  └── provenance: ProvenanceRecord

SectionSpecification
  ├── section_type: SectionType
  ├── title: str
  ├── artifact_types: tuple[str, ...]
  ├── filters: dict[str, Any] | None
  ├── ordering: tuple[str, ...] | None
  └── metadata: dict[str, Any]
```

A specification describes **what should be represented**, not how to compute it. It aligns with the Directional Programming architecture: declarative intent, not imperative script.

### 13.4 Section Types

Documents are composed of typed sections. Section types are declarative; their rendering is provider-neutral and implementation-defined.

```text
SectionType
  ├── TEXT
  ├── TABLE
  ├── METRICS
  ├── OBSERVATIONS
  ├── EVIDENCE
  ├── HYPOTHESES
  ├── CLAIMS
  ├── REASONING
  ├── DECISIONS
  ├── DIRECTION
  ├── CONFLICTS
  ├── PROVENANCE
  └── RESIDUALS
```

### 13.5 Document Projection

`DeterministicDocumentProjection` performs read-only, reproducible projection of structured cognitive state into a `DynamicDocument`.

```text
DeterministicDocumentProjection
  ├── project(specification, cognitive_state) -> DynamicDocument
  ├── refresh(document, specification, cognitive_state) -> DynamicDocument
  └── diff(old_version, new_version) -> DocumentChange
```

Projection properties:
- **Deterministic**: identical inputs always produce identical output
- **Read-only**: projection never mutates source state
- **Reproducible**: same specification + same state = same document
- **Provider-neutral**: projection logic contains no AI/ML or network dependency

### 13.6 Document Structure

```text
DynamicDocument
  ├── id: str
  ├── schema_version: str
  ├── created_at: str
  ├── document_version: str
  ├── title: str
  ├── document_type: str
  ├── source_references: tuple[DocumentReference, ...]
  ├── sections: tuple[DocumentSection, ...]
  ├── provenance: ProvenanceRecord
  └── metadata: dict[str, Any]

DocumentSection
  ├── section_id: str
  ├── section_type: SectionType
  ├── title: str
  ├── content: tuple[SectionContent, ...]
  ├── ordering: tuple[str, ...] | None
  ├── filters: dict[str, Any] | None
  ├── provenance: ProvenanceRecord
  └── metadata: dict[str, Any]

SectionContent
  ├── content_id: str
  ├── content_type: str
  ├── reference: DocumentReference | None
  ├── text: str | None
  ├── data: tuple[tuple[str, Any], ...] | None
  └── metadata: dict[str, Any]

DocumentReference
  ├── reference_id: str
  ├── artifact_id: str
  ├── artifact_type: str
  ├── schema_version: str
  ├── source_node_id: str | None
  ├── origin_node_id: str | None
  └── metadata: dict[str, Any]

DocumentVersion
  ├── version_id: str
  ├── document_id: str
  ├── document_version: str
  ├── specification_hash: str
  ├── state_hash: str
  ├── created_at: str
  ├── provenance: ProvenanceRecord
  └── metadata: dict[str, Any]
```

### 13.7 Document Change Tracking

Structural diffs between document versions are captured as `DocumentChange` records.

```text
DocumentChange
  ├── change_id: str
  ├── document_id: str
  ├── from_version: str
  ├── to_version: str
  ├── changes: tuple[ChangeEntry, ...]
  └── provenance: ProvenanceRecord

ChangeEntry
  ├── change_type: ChangeType
  ├── path: str
  ├── old_value: Any | None
  ├── new_value: Any | None
  └── metadata: dict[str, Any]

ChangeType
  ├── ADDED
  ├── REMOVED
  ├── CHANGED
  └── UNCHANGED
```

### 13.8 Document Intent

Human-requested document changes are captured as `DocumentIntent` artifacts. Intents are advisory proposals; they do not automatically mutate documents.

```text
DocumentIntent
  ├── intent_id: str
  ├── schema_version: str
  ├── created_at: str
  ├── document_id: str
  ├── intent_type: IntentType
  ├── parameters: tuple[tuple[str, Any], ...]
  ├── rationale: str | None
  ├── provenance: ProvenanceRecord
  └── metadata: dict[str, Any]

IntentType
  ├── ADD_REFERENCE
  ├── REMOVE_REFERENCE
  ├── CHANGE_SECTION
  ├── CHANGE_FILTER
  ├── CHANGE_ORDER
  ├── UPDATE_DIRECTION
  ├── ANNOTATE
  ├── REQUEST_REFRESH
  └── REQUEST_PROJECTION
```

### 13.9 Document Service

`DocumentService` provides the operational interface for document projection, refresh, and diff.

```text
DocumentService
  ├── project(specification, memory_context=None, conflicts=None) -> DynamicDocument
  ├── refresh(specification, document, memory_context=None, conflicts=None) -> DynamicDocument
  ├── diff(from_document, to_document) -> DocumentChange
  ├── version(document, specification_hash="", state_hash="") -> DocumentVersion
  ├── get_document(document_id) -> DynamicDocument | None
  └── get_versions(document_id) -> list[DocumentVersion]
```

### 13.10 Document Provider

`DeterministicMockDocumentProvider` integrates the document layer into the `CapabilityRegistry` as a first-class capability.

```text
CapabilityType
  ├── ...
  ├── DYNAMIC_DOCUMENT  (new in Phase 9)
  └── ...

DeterministicMockDocumentProvider
  ├── descriptor: CapabilityDescriptor
  ├── project(specification, memory_context=None, conflicts=None) -> DynamicDocument
```

### 13.11 Contradiction and Conflict Preservation

Documents preserve contradictions and conflicts from underlying cognitive state without silent selection or resolution.

```text
Observations section
  ├── may contain CONFLICTING observations
  └── never selects a "winner"

Evidence section
  ├── may contain SUPPORT and REFUTE evidence
  └── both remain visible

Claims section
  ├── may contain contradictory claims
  └── epistemic status remains explicit

Conflicts section
  └── surfaces CognitiveConflict artifacts verbatim
```

### 13.12 Epistemic Preservation

Document sections preserve the epistemic status of underlying artifacts without promotion or demotion.

```text
EpistemicStatus preserved in documents
  ├── UNKNOWN → rendered as UNKNOWN
  ├── HYPOTHESIS → rendered as HYPOTHESIS (never as FACT)
  ├── REFUTED → rendered as REFUTED (never removed)
  ├── SUPPORTED → rendered as SUPPORTED
  └── UNRESOLVED → rendered as UNRESOLVED
```

### 13.13 Zero Dependencies

Phase 9 maintains:
- Python >= 3.12
- 0 external runtime dependencies
- 0 network dependencies
- 0 AI/ML frameworks

All document projection is deterministic in-process logic.

### 13.14 Acceptance Criteria

- `DocumentSpecification`, `SectionSpecification` declare projection intent
- `DynamicDocument` is a pure projection of existing cognitive state
- `DeterministicDocumentProjection` produces reproducible documents
- `DocumentService` supports project, refresh, diff, and version tracking
- `DocumentIntent` captures human-requested changes as advisory proposals
- `DocumentChange` captures structural version diffs
- Contradictions and epistemic states are preserved without silent selection
- `DeterministicMockDocumentProvider` integrates via `CapabilityType.DYNAMIC_DOCUMENT`
- 77 new tests under `tests/documents/`
- Zero regressions in existing test suite
- 0 external runtime dependencies

---

## 14. Phase 10: Integrated Cognitive Loop

### 14.1 Overview

Phase 10 composes existing Phase 0–9 subsystems into a complete, deterministic, auditable end-to-end cognitive cycle via orchestrator only. No new cognitive engines, reasoning strategies, memory stores, or persistence mechanisms are introduced.

### 14.2 Loop Topology

```text
Observation → Experience → Persistence → Memory → Recall → Context → Attention → Reasoning → Epistemic Evaluation → Directional Proposal/Decision → Dynamic Document → Human/Domain Authority → Outcome → Experience
```

### 14.3 Core Components

- `DeterministicCognitiveLoop` (`src/cognitia/integration/loop.py`): Orchestrator implementing `CognitiveLoop` protocol
- `CognitiveLoopResult` (`src/cognitia/integration/types.py`): Immutable result encapsulating all produced artifact identities and reconstructable provenance chain
- Integration package: `src/cognitia/integration/`

### 14.4 Subsystem Composition

The orchestrator composes existing in-memory reference implementations:
- `InMemoryPersistenceStore` for object and event persistence
- `InMemoryMemoryStore` for contextual memory retrieval
- `InMemoryRecallEngine` for experience recall
- `DeterministicContextAssembler` for context assembly
- `DeterministicAttentionEngine` for attention allocation
- `DeterministicReasoningEngine` for reasoning execution
- `InMemoryEpistemicService` for epistemic evaluation
- `InMemoryDirectionalService` for directional programming
- `DocumentService` for document projection
- `DeterministicMockDecisionProvider` for advisory decisions
- `InMemoryRuleStore` for rule-based reasoning

### 14.5 Identity Preservation

All canonical identities survive the loop:
- `observation_id` → `Observation.id`
- `experience_id` → `ExperienceRecord.id`
- `reasoning_trace_id` → `ReasoningTrace.id`
- `proposal_id` → `Proposal.id`
- `decision_id` → `Decision.id`
- `document_id` → `DynamicDocument.id`

Verified boundaries:
- `document_id` ≠ `artifact_id`
- `node_id` ≠ `artifact_id`
- `document_version` ≠ `artifact_version`

### 14.6 Provenance Chain

The provenance chain is reconstructable through the entire loop using existing `ProvenanceRecord` semantics. Each artifact's provenance records its derivation from prior artifacts in the loop sequence.

### 14.7 Loop Invariants

Phase 10 preserves all critical invariants:
- Observation ≠ Experience
- Persistence ≠ Memory
- Memory ≠ Recall
- Recall ≠ Context
- Context ≠ Attention
- Attention ≠ Reasoning
- Reasoning ≠ Truth
- Epistemic Status ≠ Confidence
- Proposal ≠ Action
- Decision ≠ Execution
- Document ≠ Source of Truth
- Outcome ≠ Proposal
- Cognition ≠ Domain Authority
- Distributed Cognition ≠ Distributed Authority
- Plasticity ≠ Autonomous Mutation

### 14.8 Authority Boundary

Cognitia reasons, remembers, evaluates, proposes, and documents. Cognitia does NOT execute domain actions. Proposal ≠ Action, Decision ≠ Execution, Document ≠ Command.

### 14.9 Zero Dependencies

Phase 10 maintains:
- Python >= 3.12
- 0 external runtime dependencies
- 0 network dependencies
- 0 AI/ML frameworks

All loop execution is deterministic in-process logic.

### 14.10 Acceptance Criteria

- `DeterministicCognitiveLoop` executes complete observation-to-outcome cycle
- `CognitiveLoopResult` captures all artifact identities and provenance chain
- Multi-cycle recall retrieval works (Cycle 2 retrieves Cycle 1 experience)
- Contradiction preservation through full loop
- Failure isolation (if recall fails, no fabricated context/reasoning)
- Distributed cognition compatibility (node_id/artifact_id distinct)
- Plasticity remains governed; not automatically activated
- 14 new integration tests under `tests/integration/test_cognitive_loop.py`
- Zero regressions in existing test suite
- 0 external runtime dependencies

---
