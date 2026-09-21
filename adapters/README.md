# Cognitia Adapters

## Architectural Boundary

Domain applications integrate with Cognitia through **adapters**.

```text
┌────────────────────────────┐         ┌────────────────────────────┐
│     Domain Application     │         │          Cognitia          │
│ (Frappe, AcoustiForge,     │         │       (Cognitive Plane)    │
│  FJH, CellForge, Robotics) │         │                            │
│                            │         │                            │
│  Domain Data & Semantics   │ ──────> │  Cognitive ABI Contracts   │
│                            │ Adapter │                            │
│  Domain Control & Actions  │ <────── │  Advisory Proposals        │
└────────────────────────────┘         └────────────────────────────┘
```

### Core Adapter Invariants

1. **Cognitia does not import domain applications**:
   Cognitia core contains zero dependencies on any external domain code or data structures.
2. **Bidirectional Translation**:
   Domain adapters translate domain-specific observations, experiences, and requests into Cognitia contracts. They also translate Cognitia proposals back into domain-specific representations.
3. **External Domain Authority**:
   Domain authority remains strictly outside Cognitia. The adapter or the domain application decides whether, when, and how to execute or dismiss cognitive proposals.

### Implemented Adapters

- [Frappe / ERPNext Adapter](file:///e:/Cognitia/adapters/frappe/README.md): First reference adapter for enterprise business workflows, human-governed cognitive rules, and read-only advisory generation.
