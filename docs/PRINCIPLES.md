# Cognitia Principles & Architectural Invariants

## 1. Core Invariants

### Invariant 1 — Cognitive Authority
> **Cognitia provides cognitive capability, not domain authority.**

Therefore:
```text
Cognitive proposal       != domain truth
Cognitive classification != scientific fact
Cognitive recommendation != production authority
Cognitive decision       != actuator authority
Epistemic state          != physical reality
```

### Invariant 2 — Epistemic Independence
> **Epistemic knowledge is versioned, provenance-bearing, challengeable, and distinct from physical or domain truth.**

The epistemic service operates deterministically without requiring AI, ML, LLMs, neural networks, or external network access. AI/ML models are contributors to epistemic evaluation, never intrinsic authorities.

### Invariant 3 — Provider Neutrality & Independence
> **Cognitia defines cognitive capability contracts but does not prescribe a particular AI/ML model, inference engine, reasoning engine, framework, or vendor.**

Providers (rules, heuristics, tiny ML, neural models, Laya, symbolic solvers, humans) may be replaced, composed, upgraded, retired, or run in parallel without changing the Cognitia ABI or domain application authority model.

Explicitly distinguish:
```text
Cognitia Capability ≠ Provider Implementation ≠ Model Instance ≠ Domain Authority
```

### Invariant 4 — Immutable Provenance & Determinism
Every cognitive artifact carries traceable lineage and explicit determinism declarations. Historical records and model identities are never overwritten upon upgrade.

### Invariant 5 — Local-First & Offline-Capable
Cognitia executes fully within a single local process. Zero external runtime dependencies. Distribution or synchronization are layered on top of immutable serialization contracts.

### Invariant 6 — Persistence Is Non-Authoritative
> **Persistence records what happened; it is not the source of authority or truth.**

$$\text{Persistence} \neq \text{Memory} \neq \text{Reasoning} \neq \text{Authority}$$

### Invariant 7 — Plasticity & Consolidation
> **Persistence provides longitudinal continuity; plasticity operators propose candidate adaptations; epistemics evaluates what should be supported; consolidation promotes validated patterns into versioned structures.**

$$\text{Persistence} \neq \text{Memory} \neq \text{Learning} \neq \text{Consolidation} \neq \text{Authority}$$

### Invariant 8 — Human-Governed Plasticity & Advisory Non-Authority
> **Cognitia can evolve its cognitive rule and intelligence layer through explicit human intervention without requiring autonomous self-learning.**

### Invariant 9 — Observation vs Context Assembly & Enrichment
> **Observation records an occurrence. Context assembles and enriches the structural situation relevant to that occurrence.**

$$\text{Persistence} \neq \text{Memory} \neq \text{Context} \neq \text{Attention} \neq \text{Reasoning} \neq \text{Planning} \neq \text{Authority}$$

### Invariant 10 — Context vs Attention Prioritization
> **Context assembles what was relevant around an observation; Attention prioritizes what deserves cognitive focus for a specific task.**

* **Prioritization $\neq$ Truth Estimation**: `attention_score` is strictly a deterministic engineering priority.
* **Preservation of Epistemic Tension**: Attention does NOT resolve contradictions or suppress refuted/challenged evidence; it preserves epistemic tension for Reasoning.

### Invariant 11 — Cognitive Reasoning & Snapshot Transformation
> **Reasoning is a transformation of an immutable cognitive snapshot, not a query against live mutable cognitive state.**

$$\text{Reasoning Output} \neq \text{Truth} \neq \text{Epistemic Status} \neq \text{Decision} \neq \text{Authority}$$

* **Immutable Snapshot**: Reasoners operate on self-contained, frozen `ReasoningInput` snapshots without live-store lookups.
* **Non-Authoritative Candidates**: Reasoning produces candidate hypotheses, claims, derivations, and scenarios; it does NOT directly declare truth or change epistemic status.
* **Strict Causal Guardrail**: Temporal succession ($A \text{ BEFORE } B$) and Correlation ($A \text{ CORRELATES\_WITH } B$) alone MUST NEVER infer causality. Causal evaluation requires an explicit causal graph, rule, or mechanism.
* **Structural Analogy $\neq$ Semantic Equivalence**: Structural alignment describes topological correspondence; it never implies physical equivalence.
* **Abduction $\neq$ Proof**: Abductive candidate explanations generate competing hypotheses for epistemic testing, never established truth.
* **Counterfactual $\neq$ Observation**: Counterfactual scenarios evaluate explicit interventions under supplied deterministic transition rules; missing rules create explicit residuals rather than manufactured extrapolations.

### Invariant 12 — Advanced Intelligence Is Optional Scaffolding
> **Advanced intelligence capabilities are an optional provider layer. Core Cognitia remains fully deterministic and functional without any advanced provider present or enabled.**

```text
Advanced Intelligence = Optional Provider Layer
Core Cognitia        = Deterministic Substrate (always functional)
Provider Output      = Advisory Candidate Only
Activation           = Explicit Governance Operation
```

* **Scaffolding, Not Implementation**: Phase 4A defines interfaces, registries, lifecycle states, and reference mocks. No AI/ML, LLM, TinyML, RL, or autonomous self-modification is implemented.
* **Provider Neutrality**: Advanced capabilities reuse existing Model Registry, Provenance DAG, and EpistemicService. No duplicate systems are created.
* **Execution Authorization**: The `ProviderGateway` enforces lifecycle, capability, resource, and snapshot-boundary checks. Execution is separate from epistemic evaluation.
* **Proposal vs Activation**: A candidate must never become active merely because a provider generated it. Activation requires explicit epistemic evaluation, governance review, and explicit promotion.
* **Resource Declaration**: Providers declare required resources (network, GPU, external runtime, filesystem). The Gateway rejects execution if declared mandatory resources are unavailable.
* **Zero Dependencies**: No external runtime dependencies, no network dependencies, and no AI/ML frameworks are introduced.

---

## 2. Epistemic Axioms

1. **Non-Linear Epistemic Life**: Inquiry branches into competing hypotheses, challenges, falsification attempts, and model revisions.
2. **Controlled Model Evolution**: Runtime operations record experiences, events, and residuals; production model weights are never mutated spontaneously at runtime without controlled offline approval.
3. **Domain Neutrality**: Core cognitive concepts (Observation, Evidence, Claim, Hypothesis, ReasoningTrace) contain zero domain-specific assumptions.
