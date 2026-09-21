# Contract: Authority Boundary Contract

**Contract Status**: Authoritative  
**Contract Version**: 1.0.0  
**Phase**: Phase 0 Foundation  

---

## 1. Purpose & Core Axiom

The **Authority Boundary Contract** defines the non-negotiable boundary between the **Cognitive Plane** (Cognitia) and the **Authority Plane** (the consuming domain application/device).

### Fundamental Invariant
> **Cognitia provides cognitive capability, not domain authority.**

---

## 2. Permitted Operations vs. Prohibited Actions

### 2.1 Cognitia May:
* **Observe**: Ingest and structure telemetry, sensor readings, and application states.
* **Store**: Persist episodic experiences, epistemic states, traces, and model lineage.
* **Correlate**: Identify patterns, cross-correlations, and anomalies across experiences.
* **Classify**: Assign semantic labels and categories based on configured capabilities.
* **Hypothesize**: Formulate candidate explanations or generative hypotheses.
* **Reason**: Perform deductive, abductive, analogical, counterfactual, and causal derivations.
* **Challenge**: Issue formal challenges against existing claims, hypotheses, and models.
* **Recommend & Propose**: Output candidate decisions, actions, or parameter adjustments to the consuming application.

### 2.2 Cognitia Must NOT:
* **Redefine Domain Truth**: Epistemic beliefs cannot override empirical domain measurements or scientific ground truth.
* **Bypass Application Constraints**: Cognitive recommendations cannot override domain safety interlocks or physical constraints.
* **Directly Actuate**: Cognitia components MUST NOT bind directly to physical actuators or hardware drivers.
* **Assume Execution Authority**: A `Decision` emitted by Cognitia is purely advisory; only the consuming domain application can grant it execution authority.
* **Mutate Production Models Silently**: Runtime experience must not alter active production model weights without explicit offline validation and approval.

---

## 3. Cognitive vs. Domain Decision Flow

```text
               ┌────────────────────────────────────────────────────────┐
               │                     COGNITIA                           │
               │  Observation ──> Capability ──> Cognitive Decision     │
               │                                   (Advisory Proposal)  │
               └───────────────────────────┬────────────────────────────┘
                                           │
                                           │ Adapter Translation
                                           ▼
               ┌────────────────────────────────────────────────────────┐
               │                  DOMAIN APPLICATION                    │
               │  1. Safety Verification                                │
               │  2. Physical Constraint Check                          │
               │  3. Authority Conferral                                │
               │  4. Actuator Dispatch / Domain Action Execution        │
               └────────────────────────────────────────────────────────┘
```
