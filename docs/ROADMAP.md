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

## Phase 6: Cognitive Pattern Discovery & Governed Plasticity (In Progress)
* [x] Establish plasticity operator contract (read-only, advisory-only, no production mutation)
* [x] Define `PlasticityOperator` protocol with `propose(context: MemoryContext) -> CandidateLearningArtifact`
* [x] Implement `DeterministicPatternOperator` (recurring event/subject patterns)
* [x] Implement `DeterministicAssociationOperator` (co-occurrence without causation)
* [x] Implement `DeterministicRecurrenceOperator` (temporal recurrence statistics)
* [x] Implement `InMemoryPlasticityOperatorRegistry` with lifecycle management
* [x] Define `OperatorLifecycleStatus` enum (8 lifecycle states matching provider lifecycle)
* [x] Define `OperatorRecord` immutable record
* [x] Synthetic domain validation: ERP (InvoiceCreated, PaymentReceived)
* [x] Synthetic domain validation: Automotive (BoostHigh, HighLoad, LowFlow)
* [x] Synthetic domain validation: Acoustics (NoiseDetected, SilenceDetected)
* [x] Synthetic domain validation: Scientific (MeasurementTaken, CalibrationPerformed)
* [x] 28 new plasticity tests under `tests/plasticity/` (4 test files)
* [x] Zero external runtime dependencies; zero network dependencies; zero AI/ML frameworks
* [ ] Epistemic evaluation integration for candidate artifacts
* [ ] Governance review and explicit promotion workflow
* [ ] Phase 5A adapter integrations (Frappe, AcoustiForge, CellForge, Robotics)

---

## Phase 7: Directional Programming (Completed)
* [x] Establish directional programming contract (`contracts/directional-programming-contract.md`)
* [x] Define `DirectionalObjective`, `DirectionalConstraint`, `SuccessCriterion`, `DirectionalSpecification`
* [x] Define `DirectionalProposal`, `DirectionalResidual` artifacts
* [x] Implement `DirectionalProvider` protocol with explicit residual declaration
* [x] Implement `DeterministicDirectionalProvider` with deterministic residual generation
* [x] Implement `DirectionalService` protocol and `InMemoryDirectionalService`
* [x] Integrate with existing Persistence, Provider Registry, and Gateway
* [x] Authority boundary: proposals remain advisory; no automatic execution or state mutation
* [x] Epistemic boundary: proposals start `UNRESOLVED`; explicit evaluation required
* [x] 68 new Phase 7 tests under `tests/directional/`
* [x] Full regression suite: 552 tests passing, 0 failures, 0 errors, 0 warnings

---

## Phase 8: Distributed & Edge Cognition (Completed)
* [x] Establish distributed cognition contract (`contracts/distributed-cognition-contract.md`)
* [x] Define `CognitiveNode`, `NodeCapability`, `NodeType` for node identity
* [x] Define `CognitiveEnvelope` as transport-neutral artifact wrapper
* [x] Define `CognitiveConflict`, `ConflictType`, `ConflictStatus` for explicit conflict representation
* [x] Define `SynchronizationState` for idempotent sync tracking
* [x] Define `CognitiveTopology` for connectivity description without authority
* [x] Implement `LocalCognitiveRuntime` refactored for distribution reuse
* [x] Implement `CentralCognitiveRuntime` and `EdgeCognitiveRuntime` inheriting local substrate
* [x] Implement `SyncService` protocol and `InMemoryCognitiveTransport` for deterministic testing
* [x] Implement `InMemorySyncService` with send, receive, acknowledge, idempotency, duplicate simulation
* [x] Preserve artifact identity separate from node identity
* [x] Preserve provenance across node boundaries
* [x] Support local-first/offline operation on edge nodes
* [x] Authority boundary: synchronization is data movement, not execution
* [x] 71 new Phase 8 tests under `tests/distributed/`
* [x] Full regression suite: 623 tests passing, 0 failures, 0 errors, 0 warnings
* [x] Zero external runtime dependencies; zero network dependencies

---

## Phase 8.1: Distributed Contract Reconciliation (Completed)
* [x] Baseline verification: 623 passed, 0 failed, 0 errors, 0 warnings
* [x] Contract gap analysis: filled missing sections in `distributed-cognition-contract.md`
* [x] Added Section 15 (Contract Cross-Reference)
* [x] Added Section 8.3 (Conflict Preservation)
* [x] Added Section 7.3 (Partial Synchronization)
* [x] Added Section 16 (Ordering Semantics)
* [x] Added 1 contract-level test: `test_processing_node_tracked_separately_from_origin`
* [x] Final regression: 624 passed, 0 failed, 0 errors, 0 warnings
* [x] All 29 acceptance criteria satisfied

---

## Phase 9: Dynamic Cognitive Documents (Completed)
* [x] Establish dynamic cognitive document contract (`contracts/dynamic-cognitive-document-contract.md`)
* [x] Define `DynamicDocument`, `DocumentSection`, `SectionContent`, `DocumentReference`, `DocumentVersion`
* [x] Define `DocumentSpecification`, `SectionSpecification` (declarative projection intent)
* [x] Define `DocumentIntent`, `IntentType` (human-requested document changes)
* [x] Define `DocumentChange`, `ChangeEntry`, `ChangeType` (structural version diff)
* [x] Define `SectionType` enum (TEXT, TABLE, METRICS, OBSERVATIONS, EVIDENCE, HYPOTHESES, CLAIMS, REASONING, DECISIONS, DIRECTION, CONFLICTS, PROVENANCE, RESIDUALS)
* [x] Implement `DeterministicDocumentProjection` (read-only, reproducible projection)
* [x] Implement `DocumentService` and `InMemoryDocumentService` (project, refresh, diff, version)
* [x] Implement `DeterministicMockDocumentProvider` integrating with `CapabilityRegistry`
* [x] Register `CapabilityType.DYNAMIC_DOCUMENT`
* [x] Core invariant: document is projection, never source of truth, authority, memory, or execution
* [x] Preserve contradictions and conflicts without silent selection
* [x] Preserve epistemic states without promotion
* [x] 77 new Phase 9 tests under `tests/documents/`
* [x] Full regression suite: 701 tests passing, 0 failures, 0 errors, 0 warnings
* [x] Zero external runtime dependencies; zero network dependencies

---

## Phase 9.1: Dynamic Cognitive Document Contract Reconciliation & Freeze (Completed)
* [x] Baseline verification: 701 passed, 0 failed, 0 errors, 0 warnings
* [x] Verified all authoritative contracts referenced by `dynamic-cognitive-document-contract.md`
* [x] Reconciled `docs/ARCHITECTURE.md` Section 13 with actual implementation
* [x] Reconciled `docs/GLOSSARY.md` Phase 9 terminology
* [x] Verified identity boundaries: `document_id` ≠ `artifact_id`, document versioning ≠ artifact versioning
* [x] Verified projection semantics: deterministic, read-only, provenance-aware, versioned, explainable
* [x] Verified epistemic preservation: no silent transitions (e.g., HYPOTHESIS → FACT)
* [x] Verified contradiction preservation: no central/latest/highest-confidence-wins semantics
* [x] Verified provenance semantics: `DocumentReference` preserves artifact identity
* [x] Verified distributed cognition compatibility: `source_node_id`/`origin_node_id` distinct
* [x] Verified capability boundary: `CapabilityType.DYNAMIC_DOCUMENT` follows existing SPI
* [x] Verified dependency audit: `pyproject.toml` has `dependencies = []`
* [x] Added invariant tests for document identity, non-mutation, determinism, and boundaries
* [x] Full regression suite: 701 tests passing, 0 failures, 0 errors, 0 warnings
* [x] `pytest -q -W error` clean
* [x] `git diff --check` clean
* [x] Contract frozen: `docs/ROADMAP.md` marked COMPLETE/FROZEN

---

## Phase 10: Integrated Cognitive Loop (Completed)
* [x] Composed existing Phase 0–9 subsystems via orchestrator only; no new cognitive engines
* [x] Established `DeterministicCognitiveLoop` orchestrator in `src/cognitia/integration/loop.py`
* [x] Defined `CognitiveLoopResult` in `src/cognitia/integration/types.py` with reconstructable provenance chain
* [x] Verified canonical identity survival through loop: observation_id, experience_id, reasoning_trace_id, proposal_id, decision_id, document_id
* [x] Verified identity boundaries: document_id ≠ artifact_id, node_id ≠ artifact_id, document_version ≠ artifact_version
* [x] Verified provenance chain reconstructable using existing `ProvenanceRecord` semantics
* [x] Preserved loop invariants: Observation ≠ Experience, Persistence ≠ Memory, Memory ≠ Recall, Recall ≠ Context, Context ≠ Attention, Attention ≠ Reasoning, Reasoning ≠ Truth, Epistemic Status ≠ Confidence, Proposal ≠ Action, Decision ≠ Execution, Document ≠ Source of Truth, Outcome ≠ Proposal, Cognition ≠ Domain Authority, Distributed Cognition ≠ Distributed Authority, Plasticity ≠ Autonomous Mutation
* [x] Maintained zero external runtime dependencies, zero network dependencies, zero AI/ML frameworks
* [x] 14 new Phase 10 integration tests under `tests/integration/test_cognitive_loop.py`
* [x] Full regression suite: 721 tests passing, 0 failures, 0 errors, 0 warnings
* [x] `pytest -q -W error` clean
* [x] `git diff --check` clean
* [x] `dependencies = []` preserved in `pyproject.toml`
