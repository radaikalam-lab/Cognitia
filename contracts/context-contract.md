# Cognitive Context Contract

## 1. Purpose

This contract defines the **Cognitive Context** subsystem and its **Phase 3A Context Enrichment** extensions in Cognitia.

```text
External Application / Environment
              │
              ▼
        Observation (What happened)
              │
              ▼
        Persistence (Durable event log & object store)
              │
              ▼
          Memory (Historical retrieval)
              │
              ▼
    Context Assembly & Enrichment (What is structurally relevant around it)
              │
              ▼
        Attention (Task-dependent prioritization & focus)
              │
              ▼
        Reasoning (Inferential derivation & evaluation)
              │
              ▼
     External Authority (Human / Consuming System)
```

The fundamental distinction across cognitive layers is:

* **Observation**: What happened (discrete event).
* **Memory**: What historical information can be retrieved.
* **Context**: What is structurally relevant around the observation (situational assembly and structural enrichment).
* **Attention**: What information deserves cognitive focus for the current task (prioritization).
* **Reasoning**: What can be inferred (inferential derivation, diagnosis, causality, hypothesis evaluation).
* **Authority**: Outside Cognitia (consuming domain / application / human).

$$\text{Persistence} \neq \text{Memory} \neq \text{Context} \neq \text{Attention} \neq \text{Reasoning} \neq \text{Planning} \neq \text{Authority}$$

> **Context assembles.**
> **Context enriches structurally.**
> **Context MUST NOT become reasoning.**

---

## 2. Core Invariants & Boundaries

### Invariant 1 — Non-Duplication
Context is an assembly of immutable references, structural relationships, and deterministic descriptive summaries, NOT a second object store. Persistence owns durable objects; Memory retrieves historical objects; Context assembles and enriches references to the current cognitive situation.

### Invariant 2 — Non-Causality & Non-Diagnosis
Context MAY establish temporal relationships (`BEFORE`, `AFTER`, `INTERVAL`), entity neighbourhoods, state reconstructions, event sequences, recurrence, descriptive aggregates, cross-source correlations, provenance neighbourhoods, epistemic tension maps, and contextual deviation indicators.
Context MUST NOT establish causality, truth, diagnosis, hypotheses, intents, decisions, actions, or authority.
* *Allowed*: "Observation B occurred 2.4 seconds after Observation A."
* *Prohibited*: "Observation A caused Observation B."
* *Allowed*: "Current temperature is above the historical observed range (magnitude +9.6)."
* *Prohibited*: "The engine is failing / sensor is faulty."
* *Allowed*: "Evidence E1 supports Claim C1 while Evidence E2 refutes Claim C1."
* *Prohibited*: "Claim C1 is true / winning."

### Invariant 3 — Snapshot Immutability
Assembled `CognitiveContext` snapshots are deeply immutable once generated (`frozen=True`, containing tuples and immutable mapping views). Modifying underlying persistence, rules, or memory at $T_2$ does NOT alter snapshot $C_1$ assembled at $T_1$.

---

## 3. Structural Enrichment Capabilities

Cognitia Context Enrichment exposes 10 deterministic structural capabilities:

1. **Temporal Neighbourhood**: Exposes deterministic temporal intervals and relations (`BEFORE`, `AFTER`, `WITHIN_WINDOW`, `SAME_TIME_BUCKET`, `CONCURRENT`) without inferring causality.
2. **Entity Neighbourhood**: Captures provider-neutral structural relationships (`SAME_SUBJECT`, `SAME_EPISODE`, `SAME_SOURCE`, `SHARED_PARENT`, `SHARED_PROVENANCE`, `EXPLICIT_RELATIONSHIP`).
3. **State Reconstruction**: Reconstructs observable state surrounding an observation based strictly on recorded observations (`latest_value`, `previous_value`, `first_known_value`, `is_unknown`, `is_conflicted`). Does not guess missing state.
4. **Event Sequence Context**: Identifies observed chronological event sequences (`SequenceContext` with `event_ids`, `relative_positions`, `timestamps`, `time_deltas`). Sequence does not imply causality.
5. **Recurrence Context**: Computes deterministic occurrence counts, intervals, median interval, and latest interval across historical time windows.
6. **Deterministic Aggregate Context**: Computes descriptive statistics over observed numerical metrics (`count`, `min`, `max`, `mean`, `median`, `range`, `std_dev`, `delta_from_previous`, `delta_from_mean`).
7. **Contextual Deviation Indicators**: Exposes descriptive deviations (`ContextDeviation` with types `ABOVE_HISTORICAL_RANGE`, `BELOW_HISTORICAL_RANGE`, `ABOVE_BASELINE`, `BELOW_BASELINE`, `RAPID_CHANGE`, `UNUSUAL_INTERVAL`, `magnitude`).
8. **Cross-Source Correlation**: Exposes multi-source temporal and structural correlations with explicit `CorrelationReason` (`TEMPORAL_PROXIMITY`, `SHARED_SUBJECT`, `SHARED_EPISODE`, `SHARED_SOURCE`, `SHARED_PROVENANCE`, `EXPLICIT_RELATIONSHIP`).
9. **Provenance Neighbourhood**: Traverses the provenance DAG to expose upstream lineages (`derived_from`, `produced_by`, `transformed_by`, `measured_by`, `validated_by`, `referenced_by`).
10. **Epistemic Tension & Conflict Mapping**:
    * `EpistemicTension`: Maps coexisting supporting, refuting, and neutral evidence for propositions without picking a winner or estimating truth.
    * `ContextConflict`: Preserves conflicting observations occurring at the same timestamp/subject rather than silently overwriting.
11. **Context Compression**: Provides deterministic structural summaries (counts of observations, timespan, subjects, sources, epistemic states, sequences, deviations, conflicts) for high-level inspection.

---

## 4. Deterministic Ordering & Task Neutrality

* Context assembly and enrichment are completely deterministic and task-neutral.
* Ordering of items and relations is strictly deterministic:
  $$\text{Relevance Score} \downarrow \longrightarrow \text{Timestamp} \downarrow \longrightarrow \text{Stable Entity UUID} \uparrow$$
* Downstream Attention layers consume enriched `CognitiveContext` snapshots and perform task-specific prioritization without requiring Context redesign.
