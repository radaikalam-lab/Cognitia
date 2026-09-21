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

Laya is one possible provider implementation of those contracts. Providers (rules, heuristics, tiny ML, neural models, Laya, symbolic solvers, humans) may be replaced, composed, upgraded, retired, or run in parallel without changing the Cognitia ABI or domain application authority model.

Explicitly distinguish:
```text
Cognitia Capability ≠ Provider Implementation ≠ Model Instance ≠ Domain Authority
```

### Invariant 4 — Immutable Provenance & Determinism
Every cognitive artifact carries traceable lineage and explicit determinism declarations. Historical records and model identities are never overwritten upon upgrade.

### Invariant 5 — Local-First & Offline-Capable
Cognitia executes fully within a single local process. Distribution, central coordination, or cloud synchronization are layered on top of immutable serialization contracts, never required as foundational dependencies.

### Invariant 6 — Persistence Is Non-Authoritative
> **Persistence records what happened; it is not the source of authority or truth.**

$$\text{Persistence} \neq \text{Memory} \neq \text{Reasoning} \neq \text{Authority}$$

Persistence is non-authoritative and MUST NEVER be in the hard real-time safety or physical control path. Local physical control and safety interlocks MUST continue to function safely if persistence is delayed or offline.

### Invariant 7 — Plasticity & Consolidation
> **Persistence provides longitudinal continuity; plasticity operators propose candidate adaptations; epistemics evaluates what should be supported; consolidation promotes validated patterns into versioned structures.**

$$\text{Persistence} \neq \text{Memory} \neq \text{Learning} \neq \text{Consolidation} \neq \text{Authority}$$

* No autonomous runtime weight mutation is permitted.
* Candidate learning artifacts are proposals for adaptation.
* Consolidation produces Version $N+1$ in the Model Registry, keeping Version $N$ historically immutable.
* Forgetting is modeled as priority attenuation, supersession, or status retirement, never physical destruction of lineage.

### Invariant 8 — Human-Governed Plasticity & Advisory Non-Authority
> **Cognitia can evolve its cognitive rule and intelligence layer through explicit human intervention without requiring autonomous self-learning.**

* Cognitive rules are human-authored or model-proposed intelligence artifacts carrying complete provenance (`SourceType.HUMAN`).
* Published cognitive rules are immutable once registered; revisions generate Version $N+1$ without modifying historical versions.
* Advisories produced by Cognitia are strictly non-authoritative (`is_authoritative = False`) and cannot mutate application state, accounting ledgers, prices, stock, or workflows.
* Autonomous machine learning is a future capability and is not required for Cognitia to exhibit controlled cognitive plasticity.

### Invariant 9 — Observation vs Context Assembly & Enrichment
> **Observation records an occurrence. Context assembles and enriches the structural situation relevant to that occurrence.**

$$\text{Persistence} \neq \text{Memory} \neq \text{Context} \neq \text{Attention} \neq \text{Reasoning} \neq \text{Planning} \neq \text{Authority}$$

* **Structural vs Semantic Intelligence**: Context can become structurally intelligent without becoming semantically intelligent. Context describes observed relationships and structure; Reasoning interprets them.
* **Non-Causality**: Temporal sequence and interval relations do NOT imply physical or logical causality ($A \to B$ does not mean $A \text{ caused } B$).
* **Descriptive, Non-Diagnostic**: Contextual deviation indicates descriptive divergence relative to historical baselines; it does NOT imply fault, failure, or diagnosis.
* **State Reconstruction Grounding**: State reconstruction requires explicit observation semantics and represents `UNKNOWN` when unobserved; it never guesses missing state.
* **Epistemic Tension Preservation**: Coexisting contradictory evidence (`SUPPORT` and `REFUTE`) is mapped and preserved without picking a winner or estimating truth probability.
* **Compression vs Attention**: Context compression summarizes structure; Attention selects task importance. Compression never duplicates Attention.
* **Context snapshots are immutable** once assembled and carry complete composite provenance.

### Invariant 10 — Context vs Attention Prioritization
> **Context assembles what was relevant around an observation; Attention prioritizes what deserves cognitive focus for a specific task.**

$$\text{Persistence} \neq \text{Memory} \neq \text{Context} \neq \text{Attention} \neq \text{Reasoning} \neq \text{Planning} \neq \text{Authority}$$

* **Prioritization $\neq$ Truth Estimation**: `attention_score` is strictly a deterministic engineering priority, not confidence, truth, or epistemic certainty.
* **Preservation of Epistemic Tension**: Attention does NOT resolve contradictions or suppress refuted/challenged evidence; it preserves epistemic tension for Reasoning.
* **Non-Execution & Non-Reasoning**: Attention focuses and filters; it does NOT execute rules, make decisions, plan actions, or infer causality.
* **Attention $\neq$ Neural Attention**: In Cognitia, Attention is an explainable, deterministic cognitive prioritization abstraction over assembled context, not a transformer self-attention mechanism.

---

## 2. Epistemic Axioms

1. **Non-Linear Epistemic Life**: Inquiry branches into competing hypotheses, challenges, falsification attempts, and model revisions.
2. **Controlled Model Evolution**: Runtime operations record experiences, events, and residuals; production model weights are never mutated spontaneously at runtime without controlled offline approval.
3. **Domain Neutrality**: Core cognitive concepts (Observation, Evidence, Claim, Hypothesis) contain zero domain-specific assumptions (e.g., acoustics, cellular biology, kinematics).

