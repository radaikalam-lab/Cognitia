# Cognitia

**Domain-Neutral Cognitive Infrastructure and Epistemic Service Framework**

[![Phase 0](https://img.shields.io/badge/Phase-0%20Foundation-blue.svg)](#)
[![Python](https://img.shields.io/badge/Python-3.12%2B-green.svg)](#)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)

---

## 1. Mission

**Cognitia** is a domain-neutral cognitive infrastructure and epistemic service framework. It provides reusable cognitive infrastructure across consuming applications (e.g., AcoustiForge, CellForge, robotics, home automation, farm automation, swarm systems, and scientific discovery systems) without entangling domain logic or violating safety/authority boundaries.

### Core Invariant
> **Cognitia provides cognitive capability, not domain authority.**

Cognitia may observe, remember, correlate, classify, hypothesize, reason, challenge, and recommend. 
The consuming domain remains authoritative over:
* Physical reality
* Scientific computation
* Safety and physical constraints
* Real-time control
* Actuators
* Production decisions

---

## 2. Three-Plane Architecture

```text
┌────────────────────────────────────────────────────────┐
│                   APPLICATION PLANE                    │
│   (AcoustiForge, CellForge, Swarm, Robotics, etc.)     │
│   Owns domain semantics, scientific models, workflows  │
└───────────────────────────┬────────────────────────────┘
                            │ Domain Adapters / API
                            ▼
┌────────────────────────────────────────────────────────┐
│                    COGNITIVE PLANE                     │
│                       (Cognitia)                       │
│   Experience · Memory · Epistemics · Reasoning         │
│   Capabilities · Model Registry · Provenance · Lineage │
└───────────────────────────┬────────────────────────────┘
                            │ Cognitive Proposals
                            ▼
┌────────────────────────────────────────────────────────┐
│                    AUTHORITY PLANE                     │
│              (Consuming Application/Device)            │
│   Physics · Safety · Constraints · Actuator Control    │
│   Scientific Truth · Production Decisions              │
└────────────────────────────────────────────────────────┘
```

---

## 3. Fundamental Invariants

1. **Cognitive Authority Invariant**:
   ```text
   Cognitive proposal != domain truth
   Cognitive classification != scientific fact
   Cognitive recommendation != production authority
   Cognitive decision != actuator authority
   Epistemic state != physical reality
   ```
2. **Epistemic Independence Invariant**: The epistemic subsystem is fully functional without AI, ML, LLMs, external APIs, databases, or internet connectivity.
3. **Provider Independence Invariant**: Capabilities (decision, reasoning, etc.) are provider-agnostic. Rule engines, heuristics, ML models, or human experts can serve as providers.
4. **Immutable Provenance Invariant**: Every cognitive artifact contains traceable, immutable lineage and schema versioning.
5. **Local-First Invariant**: Operates self-contained in a single local process, with explicit serialization contracts enabling future distributed transport.

---

## 4. Separation of Concerns

Cognitia strictly separates four architectural levels:
* **Service**: *What* Cognitia provides (e.g., `EpistemicService`, `ExperienceService`, `ReasoningService`, `CapabilityService`, `ProvenanceService`, `ModelRegistry`).
* **Runtime**: *Where and how* those services execute (e.g., `LocalCognitiveRuntime`).
* **Adapter**: *How* external applications translate between their domain models and Cognitia contracts (residing in `adapters/`).
* **Application**: *Who* owns domain semantics and production authority.

---

## 5. Repository Structure

```text
cognitia/
├── contracts/               # Authoritative markdown contracts & ABI specifications
├── docs/                    # Architectural documents, principles, glossary, roadmap
├── src/cognitia/            # Pure Python implementation (Python >= 3.12)
│   ├── abi/                 # Canonical ABI types, identities, serialization
│   ├── provenance/          # Provenance records, lineage chains, checksums
│   ├── experience/          # Multi-agent / swarm domain-neutral experience
│   ├── epistemic/           # Epistemic nodes, claims, challenges, service
│   ├── reasoning/           # Reasoning modes, steps, immutable traces
│   ├── capabilities/        # Provider-agnostic capability SPI & registry
│   ├── models/              # Immutable model registry & schema tracking
│   ├── service/             # Composed CognitiveService facade
│   └── runtime/             # LocalCognitiveRuntime assembly
├── adapters/                # Adapter architectural boundary documentation
└── tests/                   # Strict contract and unit test suite
```

---

## 6. Getting Started

### Prerequisites
* Python `>= 3.12`
* `pytest` (for test suite execution)

### Installation (Development Mode)
```bash
pip install -e .[dev]
```

### Running the Contract Verification Suite
```bash
pytest -v -W error
```
