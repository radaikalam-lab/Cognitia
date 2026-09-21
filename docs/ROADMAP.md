# Cognitia Roadmap

---

## Phase 0: Foundation, Persistence & Cognitive Memory (Completed)
* [x] Establish canonical Cognitive ABI and type system
* [x] Define formal markdown contracts for all subsystems
* [x] Enforce four-plane architecture and authority boundary invariants
* [x] Define Provider Layer boundary and provider neutrality principle
* [x] Establish Persistence Plane contract, Event Journal, Object Store, and SPI
* [x] Establish Cognitive Memory, Plasticity Operator, and Consolidation contracts
* [x] Implement deterministic, in-memory reference implementations
* [x] Implement `LocalCognitiveRuntime` composing services, persistence, and memory
* [x] Provide 100% offline, zero-warning contract test suite

---

## Phase 1: Frappe Adapter & Human-Governed Cognitive Intelligence (Completed)
* [x] Establish decoupled Frappe / ERPNext application adapter (`adapters/frappe/`)
* [x] Define Frappe event vocabulary and observation translation (`FrappeEventTranslator`)
* [x] Implement ERP multi-observation lifecycle experience builder (`FrappeExperienceBuilder`)
* [x] Implement domain-neutral Cognitive Rule subsystem (`CognitiveRule`, `RuleStore`, `InMemoryRuleStore`)
* [x] Implement Rule Evaluation Capability with full provenance and lineage linkage
* [x] Establish Human-Governed Plasticity lifecycle (immutable versioning $N \to N+1$, supersession, retirement)
* [x] Implement read-only non-authoritative advisory presentation (`FrappeAdvisory`)
* [x] Guarantee domain neutrality and zero Frappe dependencies in Cognitia Core
* [x] Verify future domain compatibility (AcoustiForge, FJH, CellForge, Robotics)
* [x] Full regression test suite passing with zero warnings under `-W error`

---

## Phase 2: Cognitive Observation & Context (Completed)
* [x] Establish Cognitive Context contract (`contracts/context-contract.md`)
* [x] Define domain-neutral `CognitiveContext`, `ContextItem`, `TemporalContext`, and `RelevanceReason`
* [x] Implement deterministic context assembly engine (`DeterministicContextAssembler`)
* [x] Integrate context assembly across Persistence, Memory, Cognitive Rules, and Epistemics
* [x] Preserve strict non-causality from temporal proximity alone
* [x] Multi-domain synthetic validation (ERP-like, AcoustiForge-like, FJH-like)
* [x] Ensure zero external runtime dependencies and full offline operation
* [x] Maintain 100% test pass with zero warnings under `-W error`

---

## Phase 3: Cognitive Attention (Completed)
* [x] Establish Cognitive Attention contract (`contracts/attention-contract.md`)
* [x] Define lightweight immutable `AttentionQuery`, `AttentionItem`, `AttentionReason`, and `AttentionResult`
* [x] Implement deterministic attention engine (`DeterministicAttentionEngine`) with budget enforcement
* [x] Implement stable tie-breaking ($\text{attention\_score} \downarrow, \text{timestamp} \downarrow, \text{item\_id} \uparrow$)
* [x] Integrate attention engine into `LocalCognitiveRuntime.focus_context`
* [x] Preserve epistemic tension and contradictory evidence without silent suppression
* [x] Non-authority verification (no rule execution, no decision generation, no memory/persistence mutation)
* [x] Multi-domain synthetic validation (ERP-like, AcoustiForge-like, FJH-like)
* [x] 100% test pass with zero warnings under `-W error`

---

## Phase 3A: Cognitive Context Enrichment (Completed)
* [x] Modular enricher architecture (`src/cognitia/context/enrichers/`)
* [x] Temporal relationships and interval deltas (`BEFORE`, `AFTER`, `CONCURRENT`, `INTERVAL`)
* [x] Entity & context neighbourhood (`SAME_SUBJECT`, `SAME_EPISODE`, `SAME_SOURCE`, `SHARED_PROVENANCE`)
* [x] Observable state reconstruction (`latest`, `previous`, `first`, `unknown`, `conflicted`)
* [x] Event sequence context (chronological ordering, relative positions, deltas)
* [x] Recurrence statistics (counts, intervals, median interval, latest interval)
* [x] Deterministic descriptive aggregates & sample standard deviation convention
* [x] Historical baselines & contextual deviations (`ABOVE_HISTORICAL_RANGE`, `BELOW_HISTORICAL_RANGE`, `RAPID_CHANGE`)
* [x] Bounded cross-source correlation with explicit explanation basis
* [x] Bounded provenance neighbourhood lineage mapping
* [x] Epistemic tension mapping (coexisting `SUPPORT` and `REFUTE` evidence preserved)
* [x] Context conflict preservation (concurrent observational divergence)
* [x] Context compression (structural summarization without prioritization)
* [x] Multi-domain synthetic validation (ERP, AcoustiForge, FJH, Automotive)
* [x] 100% test pass with zero warnings under `-W error`

---

## Phase 4: Cognitive Reasoning (Completed)
* [x] Establish immutable `ReasoningInput` snapshot semantics (isolation from live mutable stores)
* [x] Implement modular `ReasoningStrategy` SPI protocol
* [x] Implement `DeductiveReasoner` (deterministic rule evaluation, derivation steps, missing premise residuals)
* [x] Implement `AbductiveReasoner` (candidate explanation generation, competing hypotheses, deterministic ranking)
* [x] Implement `AnalogicalReasoner` (structural correspondence mapping, limitations, Non-Equivalence invariant)
* [x] Implement `CausalReasoner` (explicit causal graphs/mechanisms, strict guardrails against temporal/correlational inference)
* [x] Implement `CounterfactualReasoner` (deterministic transition rules under interventions, non-observed simulation)
* [x] Implement `DeterministicReasoningEngine` orchestration layer
* [x] Integrate reasoning into `LocalCognitiveRuntime` (`reason`, `reason_over_attention`)
* [x] Preserve epistemic boundary (reasoning candidate generation != automatic epistemic state mutation)
* [x] Enforce authority boundary (no production state mutation, no action execution)
* [x] Multi-domain synthetic test validation (Automotive, ERP, Acoustics, Scientific Process)
* [x] 100% test pass with zero warnings under `-W error`

---

## Phase 4A: Advanced Reasoning Provider Scaffold (Completed)
* [x] Define `AdvancedCapabilityType` enum (8 capability classes)
* [x] Define `ProviderLifecycleStatus` enum (8 lifecycle states)
* [x] Define `ProposalLifecycleStatus` enum (7 proposal states)
* [x] Define `ResourceRequirements` immutable dataclass
* [x] Define `AdvancedProviderRecord` immutable/versioned identity
* [x] Define `CandidateReasoningArtifact` universal provider output envelope
* [x] New artifacts start epistemically `UNRESOLVED` and `PROPOSED`
* [x] Define `ReasoningRequest` immutable request envelope
* [x] Implement `AdvancedProviderRegistry` protocol + `InMemoryAdvancedProviderRegistry`
* [x] Implement `ProviderGateway` + `InMemoryProviderGateway` with execution authorization
* [x] Gateway does NOT automatically perform epistemic evaluation
* [x] Model Registry is reused; no duplicate registries
* [x] Provenance DAG is reused; no duplicate provenance systems
* [x] Provider availability vs. activation distinction (`AVAILABLE` ≠ `ENABLED`)
* [x] Provider versioning with immutable historical versions
* [x] Scaffold `LLMReasoningProvider` + `MockLLMProvider`
* [x] Scaffold `TinyMLReasoningProvider` + `MockTinyMLProvider`
* [x] Scaffold `HypothesisGenerationProvider` + `MockHypothesisProvider`
* [x] Scaffold `CausalInferenceProvider` + `MockCausalProvider`
* [x] Scaffold `SemanticGraphProvider` + `MockSemanticGraphProvider`
* [x] Scaffold `SimilarityProvider` + `MockSimilarityProvider`
* [x] Scaffold `ReinforcementLearningProvider` + `MockRLProvider`
* [x] Scaffold `ReasoningStrategyEvolutionProvider` + `MockStrategyEvolutionProvider`
* [x] All mock providers are deterministic, synthetic, and contain no AI/ML framework
* [x] Snapshot boundary verified (providers receive only immutable `ReasoningInput`)
* [x] Authority boundary verified (no mutation, no execution, no live-store access)
* [x] Epistemic separation verified (provider output ≠ epistemic state change)
* [x] Resource gating verified (network, GPU, external runtime, filesystem)
* [x] Disable gate verified (DISABLED/SUSPENDED/RETIRED providers cannot execute)
* [x] Activation gating verified (REGISTERED → VALIDATED → AVAILABLE → ENABLED)
* [x] 170 new Phase 4A tests; 338 total tests passing
* [x] Zero external runtime dependencies; zero network dependencies; zero AI/ML frameworks

---

## Phase 5: Adapters & Integrations
* Reference domain adapter for AcoustiForge
* Reference domain adapter for CellForge
* Reference domain adapter for Autonomous Robotics / Swarm telemetry
* Standardized bidirectional event schemas over local IPC / message brokers

---

## Phase 6: Distributed & Edge Topologies
* Central Cognitive Server deployment runtime (`CentralCognitiveRuntime`)
* Edge Cognitive Node runtime (`EdgeCognitiveRuntime`)
* Asynchronous state synchronization and offline replay protocols
* Controlled offline model evolution pipelines across edge clusters
