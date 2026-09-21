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
│                (e.g., LocalCognitiveRuntime in Phase 0)                │
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
 │    Service    ││   Service    ││   Service    ││   Registry   ││   Registry   │
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

Cognitia defines a controlled mechanism for artificial cognitive adaptation:

```text
                         EXPERIENCE
                             │
                             ▼
                        PERSISTENCE
                             │
                             ▼
                      MEMORY RETRIEVAL
                             │
                             ▼
                PLASTICITY OPERATOR (Laya / TinyML / Rules)
                             │
                             ▼
                 CANDIDATE LEARNING ARTIFACT
                             │
                             ▼
                    EPISTEMIC EVALUATION
                             │
                      ┌──────┴──────┐
                      │             │
                   REFUTED      SUPPORTED
                      │             │
                      ▼             ▼
                 Historical   CONSOLIDATION
                   Record           │
                                    ▼
                             VALIDATION GATE
                                    │
                                    ▼
                           VERSION N+1 CREATED
                                    │
                                    ▼
                             MODEL REGISTRY
```

### 4.1 Invariants of Cognitive Plasticity
1. **$\text{Persistence} \neq \text{Memory} \neq \text{Learning} \neq \text{Consolidation} \neq \text{Authority}$**: Each layer maintains strict separation.
2. **No Autonomous Production Weight Mutation**: Runtime experience never directly modifies active model weights. Adaptation produces candidate proposals that undergo epistemic evaluation and controlled consolidation into version $N+1$.
3. **Versioned Plasticity**: Version $N$ remains immutable and historically retrievable when Version $N+1$ is registered.
4. **Forgetting as Deprioritization**: Forgetting is an access/priority transformation (supersession, attenuation, retirement), never the destructive erasing of historical lineage.

---

## 5. Biological Metaphor & Hive / Collective Cognition

To aid intuitive reasoning about distributed cognitive roles, Cognitia uses a biological architectural metaphor:
* **Ecosystem (Hive)**: The collective Cognitia deployment across edge nodes and central services.
* **Coordinator (Queen-like)**: Central Cognitia service orchestrating model governance and long-term consolidation.
* **Specialist Providers (Worker-like)**: Laya, tiny models, deterministic rules, and symbolic engines performing fast inferences and candidate pattern proposals.
* **Collective Memory**: Persistent cognitive history preserving longitudinal experiences across nodes.
* **Consolidation**: Hardening repeatedly corroborated patterns into stable, versioned models.

> **Note**: This is an architectural analogy only, not a claim of biological neural equivalence.

---

## 6. Provider Layer & Provider Architecture

```text
                    COGNITIA CORE
                          │
           ┌──────────────┴──────────────┐
           │                             │
      Core Contracts               Service Layer
           │                             │
           │                      CognitiveService
           │                             │
           ├──────────────┬──────────────┤
           │              │              │
    Capability SPI   Reasoning SPI   Model Registry
           │              │              │
           └──────────────┴──────────────┘
                          │
                   Provider Boundary (SPI)
                          │
             ┌────────────┼────────────┐
             ▼            ▼            ▼
           Laya      Rule Engine   Other Models
          Provider    Provider      (TinyML/ML)
             │            │            │
             └────────────┴────────────┘
                          │
                   Cognitive Proposal (Advisory)
                          │
                   Authority Boundary
                          │
                   Domain Application
```

---

## 7. Phase 1: Frappe Adapter & Human-Governed Cognitive Intelligence

Phase 1 introduces the first concrete domain adapter along with a domain-neutral **Human-Governed Cognitive Rule** subsystem.

```text
                    Frappe / ERPNext
                           │
                    Document Events
                           │
                           ▼
                 ┌───────────────────┐
                 │   Frappe Adapter  │
                 └─────────┬─────────┘
                           │
                     Cognitia ABI
                           │
                           ▼
                 ┌───────────────────┐
                 │     Cognitia      │
                 │                   │
                 │ Observation       │
                 │ Experience        │
                 │ Persistence       │
                 │ Memory            │
                 │ Epistemics        │
                 │ Reasoning         │
                 │ Rules             │
                 └─────────┬─────────┘
                           │
                    Advisory Decision
                           │
                           ▼
                    Frappe / Human
```

### 7.1 Three Plasticity Paths

Cognitia recognizes that artificial cognitive plasticity does not require autonomous machine learning. Plasticity evolves across three distinct paths:

```text
                 COGNITIVE PLASTICITY
                         │
          ┌──────────────┼───────────────┐
          │              │               │
          ▼              ▼               ▼
       HUMAN          ASSISTED         FUTURE
      GUIDANCE        LEARNING        AUTONOMOUS
          │              │               │
          ▼              ▼               ▼
     Human rule      Model proposal    Model proposal
     / revision      + human review    + governance
          │              │               │
          └──────────────┼───────────────┘
                         ▼
                   Consolidation
                         │
                         ▼
                  Versioned Cognition
```

1. **Human-Guided Plasticity**: A human observes operational evidence, formulates a heuristic or business insight, and authors/updates an immutable `CognitiveRule` ($N \to N+1$).
2. **Machine-Assisted Plasticity**: A TinyML model, Laya, or rule operator processes memory to propose a `CandidateLearningArtifact`, which undergoes human/governance review prior to consolidation.
3. **Governed Autonomous Plasticity**: Autonomous candidate generation with epistemic validation and automated consolidation under strict constraint envelopes (future capability).

### 7.2 Core Adapter & Rule Invariants

* **Core Independence**: Cognitia Core has ZERO dependencies on Frappe, ERPNext, AcoustiForge, or FJH.
* **Non-Authoritative Advisories**: Cognitia outputs read-only advisories with explicit `is_authoritative: False`. It never mutates domain documents or business states.
* **Immutability of Rule Versions**: Published cognitive rules cannot be modified in place. Revisions generate Version $N+1$ linked by parent lineage.
* **Anti-Silent-Mutation**: Runtime observations and model inferences cannot silently alter active rules or weights.

---

## 8. Phase 2: Cognitive Observation & Context Layer

Phase 2 establishes the **Cognitive Context** layer positioned above Persistence and Memory.

```text
External Application / Environment
              │
              ▼
        Observation (What happened)
              │
              ▼
       Context Assembly (What was relevant around it)
              │
       ┌──────┼────────┐
       ▼      ▼        ▼
    Memory  Rules   Epistemics
       │      │        │
       └──────┼────────┘
              ▼
       Cognitive Context
              │
              ▼
    Future Attention / Reasoning
```

### 8.1 Observation vs Context Distinction

$$\text{Observation} = \text{What happened (discrete occurrence)}$$
$$\text{Context} = \text{What was relevant around what happened (situational assembly)}$$

Context is NOT a conclusion, causal assertion, or authoritative decision. It represents the multi-dimensional cognitive situation surrounding an observation.

### 8.2 Context Dimensions & Relevance

* **Temporal Context**: Preceding and succeeding observations within a configured temporal window, capturing temporal deltas without assuming causality.
* **Subject & Episode Context**: Entity and episodic continuity grouping related historical observations and experiences.
* **Historical Memory Context**: Contextual retrieval of past experiences, claims, and evidence via the Memory layer.
* **Epistemic Context**: Explicit evaluation statuses preserved without lossy flattening.
* **Rule Context**: Identification of active cognitive rules matching observation scope and predicates.
* **Deterministic Selection**: Ordering and selection are 100% deterministic ($\text{Relevance Score} \to \text{Timestamp} \to \text{UUID}$).

### 8.3 Phase 3A: Cognitive Context Enrichment

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

#### Core Context Enrichment Invariants:
1. **Structural vs Semantic Intelligence**: Context can become structurally intelligent without becoming semantically intelligent. Context describes observed relationships and structure; Reasoning interprets them.
2. **Non-Causality**: Temporal sequence does not imply causality ($A \to B$ does not mean $A \text{ caused } B$).
3. **Descriptive, Non-Diagnostic**: Contextual deviation indicates descriptive divergence relative to historical baselines; it does NOT imply fault, failure, or diagnosis.
4. **State Reconstruction Grounding**: State reconstruction requires explicit observation semantics and represents `UNKNOWN` when unobserved; it never guesses missing state.
5. **Epistemic Tension Preservation**: Coexisting contradictory evidence (`SUPPORT` and `REFUTE`) is mapped and preserved without picking a winner or estimating truth probability.
6. **Compression vs Attention**: Context compression summarizes structure; Attention selects task importance. Compression never duplicates Attention.

---

## 9. Phase 3: Cognitive Attention Layer

Phase 3 establishes the **Cognitive Attention** layer positioned between Context Assembly and Cognitive Reasoning.

```text
Observation (What happened)
      │
      ▼
Persistence (Durable history)
      │
      ▼
Memory (Historical retrieval)
      │
      ▼
Context (Situational assembly)
      │
      ▼
Attention (Task-dependent focus & prioritization)
      │
      ▼
Reasoning (Inferential derivation & evaluation)
      │
      ▼
Planning / Epistemic Review / Decision Advisories
```

### 9.1 Context vs Attention Distinction

$$\text{Context} = \text{What information is relevant around the current observation}$$
$$\text{Attention} = \text{What information deserves cognitive focus for the current task}$$

$$\text{Context} \neq \text{Attention}$$

> **Context assembles.**
> **Attention prioritizes.**
> **Attention MUST NOT become reasoning.**

### 9.2 Core Attention Invariants

1. **Non-Duplication**: Attention prioritizes Context items via immutable references (`context_item_id`, `item_id`); it does NOT duplicate Context, Persistence, or Memory objects.
2. **Prioritization, NOT Truth Estimation**: `attention_score` is strictly a deterministic engineering prioritization value used to allocate attention budget. It is NOT confidence, probability, truth, epistemic certainty, or causal strength.
3. **Preservation of Epistemic Tension**: Attention does NOT eliminate contradictory evidence (e.g. `SUPPORT` vs `REFUTE`). It preserves epistemic tension for downstream Reasoning and Epistemic evaluation rather than prematurely resolving it.
4. **Non-Execution**: Attention may prioritize active rules or historical memories, but it never executes rules, mutates memory, or triggers actions.
5. **Deterministic Budget & Stable Tie-Breaking**: Given identical input context and query, results are 100% reproducible. Identical scores tie-break strictly by $(\text{attention\_score} \downarrow, \text{timestamp} \downarrow, \text{item\_id} \uparrow)$.
6. **Snapshot Immutability & Provenance**: Attention results are deeply frozen snapshots linked to upstream `CognitiveContext` through Cognitia's provenance system.

