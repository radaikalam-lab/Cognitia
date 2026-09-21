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
