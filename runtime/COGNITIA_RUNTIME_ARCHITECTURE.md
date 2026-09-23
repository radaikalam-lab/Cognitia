# Cognitia Standalone Runtime Architecture

**Document Version:** 1.0.0  
**Runtime Identity:** `Cognitia`  
**Docker Image:** `cognitia:1.0.0`  
**Container Name:** `cognitia`  
**Cognitive ABI:** `1.0.0`  
**Status:** Hardened & Validated  

---

## 1. System Topology

Cognitia is an autonomous, domain-neutral epistemic reasoning service. External host applications interact strictly as **providers** through canonical adapter layers.

```
                         ┌─────────────────────────────────┐
                         │             COGNITIA            │
                         │        Standalone Runtime       │
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
                         │  │    Cognitia Gateway API   │  │
                         │  │   - ABI 1.0.0 Validator   │  │
                         │  │   - Provider Registry     │  │
                         │  │   - Security Sanitizer    │  │
                         │  │   - Local HTTP Server     │  │
                         │  └─────────────▲─────────────┘  │
                         └────────────────┼────────────────┘
                                          │ 127.0.0.1:8000 Only
                                          │
                  ┌───────────────────────┼───────────────────────┐
                  │                       │                       │
                  ▼                       ▼                       ▼
      ┌───────────────────────┐ ┌───────────────────┐ ┌───────────────────────┐
      │ Thorium Browser Adapt │ │  Frappe ERP Adapt │ │ AcoustiForge Adapter  │
      │ (OPERATIONAL_REF)     │ │ (PLANNED_REF)     │ │ (PLANNED_REF)         │
      │ Authority: NONE       │ │ Authority: NONE   │ │ Authority: NONE       │
      └───────────────────────┘ └───────────────────┘ └───────────────────────┘
```

---

## 2. Process Separation & Responsibilities

### 2.1 The Gateway Boundary (`runtime/gateway/`)
- **Transport:** HTTP/1.1 over `127.0.0.1:8000`.
- **Validation:** 
  - Canonical ABI v1.0.0: UUIDv4 entity check, SemVer 1.x schema version, UTC ISO-8601 timestamps.
  - Runtime Limits: 512 KB payload cap, nesting depth <= 10, max string <= 256 KB.
- **Provider Identification:** `X-Cognitia-Provider-Id` matches against static whitelist. Dynamic provider registration is permanently disabled in Runtime 1.0.
- **Capability Gating:** Rejects undeclared capabilities (`403 Forbidden`).
- **Security Sanitization:** Strips/rejects execution directives (`exec`, `command`, `shell`, `system`), detects structured credential leakage, and tags external browser content with `is_untrusted_external_content = true`.

### 2.2 The Epistemic Core (`src/cognitia/epistemic/`)
- **Epistemic Nodes:** Holds immutable nodes for observations, evidence, hypotheses, and claims.
- **Node Capacity:** Enforces bounded in-memory capacity (50,000 nodes max).
- **Transitions:** Non-linear state transitions (`UNKNOWN`, `OBSERVED`, `HYPOTHESIS`, `SUPPORTED`, `REFUTED`, `UNRESOLVED`).
- **Directional Programming:** Ingests specifications and emits advisory candidate `DirectionalProposal` instances. Zero execution logic is permitted.

---

## 3. Core Invariants

1. **Epistemic Novelty ≠ Production Authority:** Cognitia never commands external tools, browsers, or operating system processes.
2. **Untrusted Data Remains Data:** External text (including web content from Thorium) is passive data and cannot become executable instructions.
3. **Deterministic Serialization:** Invariant hashing and comparisons adhere to UTF-8 canonical JSON key sorting.