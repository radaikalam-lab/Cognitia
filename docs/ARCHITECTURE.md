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
