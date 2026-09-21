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

## Phase 2: Cognitive Engine, Providers & Persistence Services
* Long-term episodic and semantic memory storage abstractions on top of Persistence Plane
* Durable local storage backends (`SQLitePersistenceStore`, append-only local log files)
* High-performance serialization adapters (Arrow / Protobuf options alongside JSON ABI)
* Model registry versioning and calibration lifecycle manager
* Offline model evolution pipelines and governance review tooling

---

## Phase 3: Adapters & Integrations
* Reference domain adapter for AcoustiForge
* Reference domain adapter for CellForge
* Reference domain adapter for Autonomous Robotics / Swarm telemetry
* Standardized bidirectional event schemas over local IPC / message brokers

---

## Phase 4: Distributed & Edge Topologies
* Central Cognitive Server deployment runtime (`CentralCognitiveRuntime`)
* Edge Cognitive Node runtime (`EdgeCognitiveRuntime`)
* Asynchronous state synchronization and offline replay protocols
* Controlled offline model evolution pipelines across edge clusters
