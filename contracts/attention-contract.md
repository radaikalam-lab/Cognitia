# Cognitive Attention Contract

## 1. Purpose

This contract defines the **Cognitive Attention** subsystem in Cognitia.

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
         Context (Situational assembly around observation)
              │
              ▼
        Attention (Task-dependent prioritization & focus)
              │
              ▼
        Reasoning (Inferential derivation & evaluation)
              │
              ▼
         Planning / Simulation / Epistemic Review
              │
              ▼
         Decision / Advisory Recommendation
              │
              ▼
     External Authority (Human / Consuming System)
```

The fundamental distinction across cognitive layers is:

* **Observation**: What happened (discrete event).
* **Memory**: What historical information can be retrieved.
* **Context**: What information was relevant around the current observation (situational assembly).
* **Attention**: What information deserves cognitive focus for the current task (prioritization).
* **Reasoning**: Inferential derivation, hypothesis evaluation, and deductive/inductive reasoning over attended information.
* **Authority**: Consuming domain system / application / human operating outside Cognitia Core.

$$\text{Context} \neq \text{Attention}$$

> **Context assembles.**
> **Attention prioritizes.**
> **Attention MUST NOT become reasoning.**

---

## 2. Core Invariants

$$\text{Persistence} \neq \text{Memory} \neq \text{Context} \neq \text{Attention} \neq \text{Reasoning} \neq \text{Planning} \neq \text{Authority}$$

### Invariant 1 — Non-Duplication
Attention does NOT duplicate or copy complete `Observation`, `Experience`, `CognitiveRule`, `MemoryContext`, or `EpistemicNode` objects into itself. Attention references Context items via immutable references (`source_context_item_id`, `item_id`). Context owns contextual assembly; Attention owns task prioritization.

### Invariant 2 — Non-Reasoning & Non-Causality
Attention selects and ranks information from an assembled `CognitiveContext`. Attention MUST NOT infer physical or logical causality, establish truth, generate conclusions, execute cognitive rules, make decisions, plan actions, modify production state, or alter model weights.

### Invariant 3 — Attention Score is NOT Truth or Confidence
`attention_score` is defined strictly as a deterministic engineering prioritization value used by the Attention subsystem to allocate cognitive focus budget.
$$\text{attention\_score} \neq \text{confidence} \neq \text{probability} \neq \text{truth} \neq \text{epistemic certainty} \neq \text{causal strength}$$

### Invariant 4 — Epistemic Awareness & Contradiction Preservation
Attention may consider epistemic states (`OBSERVED`, `SUPPORTED`, `TESTABLE`, `HYPOTHESIS`, `UNRESOLVED`, `REFUTED`) during deterministic scoring, but Attention MUST NOT reinterpret epistemic state or prematurely eliminate contradictory evidence. If both supporting and refuting evidence are relevant to a task, Attention preserves epistemic tension rather than resolving it. Resolution belongs strictly to Epistemic/Reasoning processes.

### Invariant 5 — Rule and Memory Non-Interference
Attention may prioritize items associated with active cognitive rules or retrieved historical memories, but Attention MUST NOT execute rules, rewrite memory, consolidate memory, or mutate memory store.

### Invariant 6 — Complete Determinism and Static Parameters
Attention ranking is 100% deterministic, explainable, and reproducible. Given identical `CognitiveContext`, `AttentionQuery`, and configuration, the result is identical. Attention contains zero randomness, zero LLMs, zero vector embeddings, zero neural networks, zero runtime weight mutation, and zero online training.

---

## 3. Attention Types and Schema

### AttentionReason
Enumeration of explainable reasons why an item received attention:
* `REFERENCE_ITEM`: The reference observation of the context itself.
* `TASK_MATCH`: Matches the requested task type or objective filter.
* `SUBJECT_MATCH`: Correlates with one of the focus subject IDs in the query.
* `TEMPORAL_PROXIMITY`: High temporal proximity in the temporal window.
* `EPISODE_RELEVANCE`: Belongs to the target episode or workflow lifecycle.
* `SOURCE_RELEVANCE`: Matches target source application or origin subsystem.
* `EPISTEMIC_RELEVANCE`: Carries epistemic status targeted by the query.
* `RULE_RELEVANCE`: Associated with an active rule relevant to the query.
* `MEMORY_RELEVANCE`: Historical memory match requested by the query.
* `EXPLICIT_SELECTION`: Explicitly targeted item ID in query parameters.

### AttentionQuery
Provider-neutral, lightweight immutable specification representing the cognitive task focus:
* `task_id`: Identifier of the cognitive task.
* `task_type`: Type of task (e.g. `anomaly_investigation`, `trend_analysis`, `rule_evaluation`, `epistemic_audit`, `general_focus`).
* `focus_subject_ids`: Tuple of subject IDs to prioritize.
* `requested_item_types`: Tuple of context item types to consider (e.g. `observation`, `experience`, `rule`, `claim`, `hypothesis`).
* `maximum_items`: Attention budget (maximum number of focused items to return).
* `minimum_score`: Minimum threshold for attention score.
* `target_epistemic_statuses`: Tuple of epistemic statuses to focus on.
* `scope`: Optional scope filter.
* `parameters`: Immutable key-value parameters.

### AttentionItem
Auditable immutable item ranking:
* `item_id`: Target entity ID.
* `rank`: Deterministic rank (1-indexed).
* `attention_score`: Deterministic prioritization value in range $[0.0, 1.0]$.
* `source_context_item_id`: Reference back to the `ContextItem` in the source `CognitiveContext`.
* `selection_reasons`: Tuple of `AttentionReason` values explaining the selection.
* `epistemic_status`: Associated epistemic status if present.
* `metadata`: Immutable metadata dictionary.

### AttentionResult
Immutable snapshot extending `CognitiveObject`:
* `id`: Unique attention snapshot ID (`att_...`).
* `created_at`: UTC ISO-8601 creation timestamp.
* `reference_observation_id`: Observation around which context was assembled.
* `context_id`: Source `CognitiveContext` entity ID.
* `task_id`: Query task ID.
* `task_type`: Query task type.
* `selected_item_ids`: Tuple of selected item IDs in ranked order.
* `attention_items`: Tuple of `AttentionItem` objects in ranked order.
* `budget_limit`: Requested budget (`maximum_items`).
* `provenance`: Provenance record linking to source `CognitiveContext` and referenced context item IDs.

---

## 4. Deterministic Ranking & Stable Tie-Breaking

The ranking function evaluates deterministic relevance components based on query matching and context attributes.

If two items produce equal attention scores, tie-breaking is strictly deterministic:
$$\text{attention\_score} \downarrow \longrightarrow \text{timestamp} \downarrow \longrightarrow \text{item\_id} \uparrow$$

Ranking order is completely independent of dictionary iteration, set ordering, database order, or thread scheduling.

---

## 5. Snapshot Immutability & Auditability

Like `CognitiveContext`, an `AttentionResult` is deeply immutable once assembled (`frozen=True`, containing tuples and immutable mapping views).
* Modifying underlying persistence, memory, rules, or assembling a new context $C_2$ at $T_2$ does NOT mutate $A_1$ produced at $T_1$.
* The full lineage ($A_1 \to C_1 \to \text{ContextItems} \to \text{Persistence Objects}$) is preserved for reasoning trace and auditability.
