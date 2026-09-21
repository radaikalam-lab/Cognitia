# Recall Contract

## Invariants

1. Recall is **read-only**. It does not modify persisted cognitive objects.
2. Recall is **offline**. No network calls, embeddings, or external providers are used.
3. Recall is **deterministic**. Identical queries against identical snapshots produce identical results.
4. Recall is **snapshot-safe**. Execution does not mutate state observed by concurrent readers.
5. Recall is **provider-independent**. Advanced providers may be absent; recall operates without them.
6. Advanced providers default to **DISABLED/DECLARED**; recall never auto-enables them.
7. Recall does **not** perform attention, reasoning, learning, truth evaluation, or causality inference.
8. Recall scores are bounded in **[0.0, 1.0]** and derived from deterministic weighted components.
9. Recall results are ordered by **descending normalized score**, then by **ascending object id**.
10. Recall traces are **immutable** audit records of execution parameters and outcomes.

## Scoring Components

| Component | Weight | Description |
|-----------|--------|-------------|
| TEMPORAL_RECENCY | 0.25 | Proximity to reference time |
| EPISODE_MATCH | 0.20 | Episode identifier match |
| AGENT_MATCH | 0.15 | Agent identifier match |
| ENVIRONMENT_MATCH | 0.10 | Environment identifier match |
| EPISTEMIC_STABILITY | 0.15 | Epistemic status stability |
| SOURCE_APPLICATION_MATCH | 0.05 | Source application match |
| METADATA_MATCH | 0.10 | Metadata field match ratio |

## Prohibited Operations

- Mutating persisted cognitive objects during recall
- Using embeddings, vector databases, or learned representations
- Delegating scoring to external providers or services
- Interpreting recall results as attention, reasoning, or truth
- Modifying query limits or ordering post-execution
