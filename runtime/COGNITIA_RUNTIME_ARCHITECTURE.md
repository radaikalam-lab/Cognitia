# Cognitia Standalone Runtime Architecture

**Document Version:** 1.0.0  
**Cognitive ABI Version:** 1.0.0  
**Status:** Approved & Implemented  

---

## 1. Architectural Model

Cognitia is designed as an autonomous, application-neutral epistemic reasoning engine. Applications interface strictly as **independent providers** through adapter bridges.

```
                         ┌─────────────────────────────────┐
                         │   Cognitia Standalone Runtime   │
                         │                                 │
                         │  ┌───────────────────────────┐  │
                         │  │  InMemoryEpistemicService │  │
                         │  │   - Epistemic Nodes       │  │
                         │  │   - Observations/Evidence │  │
                         │  │   - Directional Reasoning │  │
                         │  └─────────────▲─────────────┘  │
                         │                │                │
                         │  ┌─────────────┴─────────────┐  │
                         │  │      Epistemic Bridge     │  │
                         │  └─────────────▲─────────────┘  │
                         │                │                │
                         │  ┌─────────────┴─────────────┐  │
                         │  │  Cognitia Gateway Layer   │  │
                         │  │   - ABI 1.0.0 Validator   │  │
                         │  │   - Provider Registry     │  │
                         │  │   - Security Sanitizer    │  │
                         │  │   - Local HTTP Server     │  │
                         │  └─────────────▲─────────────┘  │
                         └────────────────┼────────────────┘
                                          │ Localhost Only (127.0.0.1:8000)
                                          │
                  ┌───────────────────────┼───────────────────────┐
                  │                       │                       │
                  ▼                       ▼                       ▼
      ┌───────────────────────┐ ┌───────────────────┐ ┌───────────────────────┐
      │ Thorium Browser Adapt │ │  Frappe ERP Adapt │ │ AcoustiForge Adapter  │
      │ (observe.navigation   │ │ (observe.ledger   │ │ (observe.acoustics    │
      │  observe.content)     │ │  observe.orders)  │ │  propose.resonances)  │
      │ Authority: NONE       │ │ Authority: NONE   │ │ Authority: NONE       │
      └───────────────────────┘ └───────────────────┘ └───────────────────────┘
```

---

## 2. Process Separation & Responsibilities

### 2.1 The Gateway Layer
- **Transport:** Local-only REST interface on `127.0.0.1:8000`.
- **Validation:** ABI 1.0.0 schema conformance, UUIDv4 entity checks, ISO-8601 UTC timestamp format.
- **Provider Authorization:** Matches provider ID against registered whitelist; verifies declared capabilities.
- **Security Sanitization:** Strips/rejects execution directives (`exec`, `command`, `system`), detects credential leaks, enforces payload size caps (512 KB), and tags untrusted external data.

### 2.2 The Epistemic Core
- Maintains canonical `Observation`, `ProvenanceRecord`, `Evidence`, `Claim`, and `EpistemicNode` structures.
- Implements state transitions (`OBSERVED`, `SUPPORTED`, `CHALLENGED`, `REFUTED`).
- Evaluates `DirectionalSpecification` inputs and emits advisory `DirectionalProposal` candidate structures.

---

## 3. Epistemic Invariants

1. **Epistemic Novelty ≠ Production Authority:** Cognitia may identify patterns, generate hypotheses, or propose directions, but never directly acts upon or commands external systems.
2. **Untrusted Data Remains Data:** External content (e.g. web pages extracted by Thorium) is strictly passive data, flagged with `is_untrusted_external_content = true`.
3. **Deterministic Serialization:** Ingestion and hash verification utilize canonical key sorting and compact representation.