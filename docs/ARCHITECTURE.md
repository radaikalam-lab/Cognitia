# Cognitia Architecture

## 1. Architectural Overview

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
│       Runtime (LocalCognitiveRuntime, In-Memory Reference Providers)   │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ Cognitive Proposals (Advisory)
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                           AUTHORITY PLANE                              │
│       Consuming Devices, Real-Time Controllers, Safety Interlocks       │
│       Owns: Physics, Safety, Constraint Verification, Actuators        │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Four-Tier Separation of Concerns

Cognitia enforces a strict 4-tier conceptual separation:

```text
┌────────────────────────────────────────────────────────────────────────┐
│ 1. SERVICE   = WHAT Cognitia provides (Epistemics, Experience,         │
│                Reasoning, Capabilities, Provenance, Model Registry)     │
├────────────────────────────────────────────────────────────────────────┤
│ 2. RUNTIME   = WHERE and HOW those services execute                    │
│                (e.g., LocalCognitiveRuntime in Phase 0)                │
├────────────────────────────────────────────────────────────────────────┤
│ 3. ADAPTER   = HOW an external domain connects and translates          │
│                (Bidirectional transformation, outside Cognitia core)   │
├────────────────────────────────────────────────────────────────────────┤
│ 4. APPLICATION = WHO owns domain semantics and production authority    │
│                (External client, real-time safety, physical actuators) │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Cognitive Service Composition

Cognitia avoids monolithic "god objects" through clean composition:

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
 └───────────────┘└──────────────┘└──────────────┘└──────────────┘└──────────────┘
```

---

## 4. Provider Layer & Provider Architecture

Cognitia defines a strict **Provider Boundary** separating domain-neutral capability interfaces from concrete cognitive engines.

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

### 4.1 Architectural Position of Laya

> **Laya Provider** is a concrete, optional implementation of one or more Cognitia capability contracts (e.g., `DecisionCapability`, `ReasoningCapability`).

* **Provider Independence**: Laya is merely one possible cognitive provider. Cognitia is fully functional without Laya.
* **No Core Coupling**: Laya is NOT part of the Cognitive ABI, Epistemic Service contract, Provenance contract, Experience contract, Model Registry contract, or Authority Boundary.
* **Dependency Inversion**:
  ```text
  Cognitia Core
        ▲
        │ implements
        │
  Laya Provider
  ```
  Cognitia Core NEVER imports Laya. Laya providers import Cognitia contracts and implement its SPI protocols.

### 4.2 Epistemic and Authority Boundary for Providers

A cognitive provider (including Laya) never possesses domain authority or epistemic infallibility:

```text
Laya / Provider Inference
         │
         ▼
  Cognitive Proposal (Advisory)
         │
         ▼
Epistemic Evaluation / Recording (Epistemic Service)
         │
         ▼
Domain-Specific Validation & Safety Interlocks (Domain Application)
         │
         ▼
  Authoritative Decision / Physical Actuation (Authority Plane)
```

Never:
$$\text{Provider Inference} \longrightarrow \text{Domain Truth / Actuator Control}$$

### 4.3 Provider Plurality & Model Registration

Cognitia is designed to support provider coexistence and substitution:

```text
DecisionCapability
       │
       ├── LayaDecisionProvider (Optional neural/generative provider)
       ├── RuleDecisionProvider (Deterministic reference provider)
       ├── TinyMLDecisionProvider (Edge-optimized ML provider)
       └── ClassicalMLDecisionProvider (Statistical estimator)
```

The **Capability Registry** tracks *what capability is available* (`capability_type = DECISION`, `provider_name = "laya"`).  
The **Model Registry** tracks *which versioned model artifact implements it* (`model_id`, `model_version`, `provider = "laya"`, `calibration_checksum`).

---

## 5. Deployment Topologies (Present & Future)

### Phase 0: Local-First (In-Process)
In Phase 0, all services execute synchronously/asynchronously within a single Python process managed by `LocalCognitiveRuntime`. Zero network, zero databases, zero external services, and zero mandatory external AI models required.

### Future Topology (Central Cognitive Server & Edge Nodes)
In future phases, the same contracts will support central and edge topologies without modifying domain adapter contracts:

```text
                   CENTRAL COGNITIVE SERVICE
                   ┌────────────────────────┐
                   │ Cognitia Core Service  │
                   │                        │
                   │ • Experience Store     │
                   │ • Epistemic Graph      │
                   │ • Deep Reasoning       │
                   │ • Model Registry       │
                   │ • Offline Learning     │
                   │                        │
                   │    Provider Layer      │
                   │   ┌──────────────┐     │
                   │   │ Laya / Rules │     │
                   │   └──────────────┘     │
                   └───────────┬────────────┘
                               │
                      async / event bus / IPC
                               │
               ┌───────────────┼───────────────┐
               ▼               ▼               ▼
          AcoustiForge     CellForge       Robotics
         (Edge Adapter)  (Edge Adapter)  (Edge Node)
               │               │               │
               ▼               ▼               ▼
         Local Safety / Actuator Control Authorities
```
> **Critical Invariant**: Central Cognitia and central providers (such as Laya) are NEVER in the hard real-time safety path. Local edge domains must operate safely even when disconnected.
